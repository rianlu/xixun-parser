#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
戏讯解析助手 - 优化的数据解析器
Refactored for maintainability and data structure clarity
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re
import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Optional

@dataclass
class Show:
    """单场演出信息"""
    time: str  # 下午/晚上/具体时间
    info: str  # 剧目名称或其他信息

@dataclass
class Performance:
    """戏讯条目"""
    id: int
    troupe: str
    venue: str
    date: str = ""
    start_date: str = "" # 计算得出的开始日期
    end_date: str = ""   # 可选，结束日期
    total_days: str = "" # 总演出天数
    lunar_date: str = ""
    location_note: str = ""
    shows: List[Show] = field(default_factory=list)
    days_info: str = ""
    raw_text: str = ""

    def to_dict(self):
        return asdict(self)

class WeChatArticleParser:
    """微信公众号文章解析器"""
    
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
    
    def _init_driver(self):
        """初始化Chrome驱动"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
    
    def parse_article(self, url):
        """解析微信公众号文章"""
        try:
            if not self.driver:
                self._init_driver()
            
            print(f"正在访问: {url}")
            self.driver.get(url)
            time.sleep(3) # 等待页面加载
            
            # 获取标题
            try:
                title_elem = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "activity-name"))
                )
                title = title_elem.text
            except:
                title = "未知标题"
            
            print(f"文章标题: {title}")
            
            # 获取内容区域HTML
            js_content_html = self.driver.execute_script(
                "return document.querySelector('#js_content') ? document.querySelector('#js_content').innerHTML : '';"
            )
            
            if not js_content_html:
                return {'success': False, 'error': '未找到文章内容'}
            
            # 解析数据
            performances = self._extract_performances(js_content_html)
            
            return {
                'success': True,
                'data': {
                    'title': title,
                    'url': url,
                    'content_html': js_content_html, # 保留原始HTML供调试
                    'performances': [p.to_dict() for p in performances],
                    'total': len(performances)
                }
            }
            
        except Exception as e:
            print(f"解析出错: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _extract_performances(self, html_content: str) -> List[Performance]:
        """从HTML提取戏讯列表"""
        soup = BeautifulSoup(html_content, 'lxml')
        
        # 预处理：移除 script/style
        for tag in soup(['script', 'style']):
            tag.decompose()
        
        # 智能提取文本：保持块级元素换行，合并行内元素
        # 1. 处理换行符
        for br in soup.find_all('br'):
            br.replace_with('\n')
        
        # 2. 在块级元素后插入换行符，确保视觉分行
        block_tags = ['p', 'div', 'section', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'tr']
        for tag in soup.find_all(block_tags):
            try:
                tag.insert_before('\n')
                tag.insert_after('\n')
            except:
                pass
                
        # 3. 提取文本，不使用默认分隔符（合并span），但保留strip以清除多余空白
        # get_text(strip=True) 会移除每个文本节点的首尾空白，对于紧凑的中文排版通常是合适的
        # UPDATE: strip=True 会移除我们手动插入的换行符（因为它们只是空白字符串），所以必须由 strip=False
        text_content = soup.get_text(separator='', strip=False)

        raw_lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        # 预处理：合并被意外断行的【剧团】括号
        # e.g. "Line1: ...", "Line2: 【", "Line3: ...】" -> "Line2: 【...】"
        lines = []
        buffer = ""
        open_count = 0
        
        for line in raw_lines:
            if not buffer:
                c_open = line.count('【')
                c_close = line.count('】')
                if c_open > c_close:
                    buffer = line
                    open_count = c_open - c_close
                else:
                    lines.append(line)
            else:
                buffer += line
                c_open = line.count('【')
                c_close = line.count('】')
                open_count += (c_open - c_close)
                
                if open_count <= 0:
                    lines.append(buffer)
                    buffer = ""
                    open_count = 0
        
        # Force flush if buffer remains (though unlikely to match if unbalanced)
        if buffer:
            lines.append(buffer)
        

        performances: List[Performance] = []
        current_date_info = {'date': '', 'lunar': '', 'weekday': ''}
        perf_id_counter = 1
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 1. 忽略干扰行
            if self._is_skip_line(line):
                i += 1
                continue
            
            # 2. 检查日期标题行 (e.g. 2026年1月19日)
            date_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', line)
            if date_match and len(line) < 30: # 长度限制防止误判长句
                current_date_info['date'] = date_match.group(1)
                # 尝试向下读取农历/星期 (往往紧跟其后)
                # 简单处理：如果下一行包含"农历"或"星期"，则更新
                next_check_idx = i + 1
                while next_check_idx < min(i + 4, len(lines)): # 只看这日期下面几行
                    check_line = lines[next_check_idx]
                    if '农历' in check_line:
                        current_date_info['lunar'] = check_line
                    elif '星期' in check_line:
                        current_date_info['weekday'] = check_line
                    elif '【' in check_line: # 遇到剧团了，停止
                        break
                    next_check_idx += 1
                i += 1
                continue
                
            # 3. 检查是否有【剧团】标记，这是新条目的核心特征
            # Supported formats: "Place【Troupe】", "【Troupe】" (Place in prev lines)
            troupe_match = re.search(r'【([^】]+)】', line)
            if troupe_match:
                troupe_name = troupe_match.group(1)
                venue_part = line[:troupe_match.start()].strip()

                if not venue_part and i > 0:
                    venue_part = self._backtrack_venue(lines, i - 1)
                
                # 解析本条目的日期（优先级高于全局current_date）
                # Format: （2026年1月20日<农历...>）Place...
                item_date, item_lunar, clean_venue = self._parse_inline_date(venue_part)
                
                # 如果本行/回溯的地点中没有提取到日期，向上查找独立的日期行
                # (处理被BS4断行为: DateLine -> VenueLine -> TroupeLine 的情况)
                if not item_date and i > 0:
                    check_idx = i - 1
                    # 最多向上看3行
                    while check_idx >= 0 and check_idx >= i - 3:
                        prev_line = lines[check_idx]
                        
                        # 如果遇到另一个剧团标记，停止回溯，避免跨条目
                        if '【' in prev_line or '】' in prev_line:
                            break
                        
                        # 尝试提取日期
                        found_date, found_lunar, found_rest = self._parse_inline_date(prev_line)
                        if found_date:
                            item_date = found_date
                            item_lunar = found_lunar
                            
                            # 如果之前的venue为空，或者当前找到的行除了日期还有其他内容(可能是地点一部分)
                            # 则将其合并到地点中。注意顺序：发现的行在更上面，所以放在前面。
                            # 但要注意 found_rest 可能是空字符串(如果整行就是日期)
                            if found_rest.strip():
                                clean_venue = found_rest.strip() + clean_venue
                            break
                            
                        check_idx -= 1

                final_venue = clean_venue
                final_date = item_date if item_date else current_date_info['date']
                final_lunar = item_lunar if item_lunar else current_date_info['lunar']
                
                # 提取定位备注
                # 提取定位备注 (User request: Don't extract as separate content, just keep in venue)
                # loc_note_match = re.search(r'（定位([^）]+)）', final_venue)
                loc_note = ""
                # if loc_note_match:
                #    loc_note = loc_note_match.group(1)
                    # 用户要求保留定位在地址中，不再移除
                    # final_venue = final_venue.replace(loc_note_match.group(0), '').strip()

                perf = Performance(
                    id=perf_id_counter,
                    troupe=troupe_name,
                    venue=final_venue,
                    date=final_date,
                    lunar_date=final_lunar,
                    location_note=loc_note,
                    raw_text=line
                )
                
                # 向下读取更多信息：剧目、时间、天数
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    
                    # 如果遇到下个【剧团】或日期标题，说明本条目结束
                    if '【' in next_line and '】' in next_line: 
                        break
                    if re.match(r'^(\d{4}年\d{1,2}月\d{1,2}日)', next_line):
                        break
                    
                    # 匹配演出第X天
                    if '演出第' in next_line:
                        perf.days_info = next_line
                        i += 1
                        continue
                    
                    # 匹配剧目信息 (下午/晚上)
                    # Common formats: "下午: 戏名", "晚上: 戏名"
                    # Also: "（1月22日）下午:..."
                    show = self._parse_show_line(next_line)
                    if show:
                        perf.shows.append(show)
                        i += 1
                        continue
                    
                    # 如果是很短的空行或无关行，跳过；如果是长文本可能是地点续行？
                    # 这里暂且认为非剧目非天数非新条目的行，可能是杂音，或者未处理格式
                    # 为了安全，若不匹配任何已知模式，暂时跳过
                    i += 1
                
                # --- Post-processing after gathering all lines for this item ---
                
                # 1. 提取总天数 (e.g. "演出第3天，共5天")
                if perf.days_info:
                    # 修复：仅匹配“共X天”或“共X场”，避免误判“第X天”
                    days_match = re.search(r'共(\d+)[天场]', perf.days_info)
                    if days_match:
                       perf.total_days = days_match.group(1)

                # 2. 计算开始日期 (Start Date Calculation)
                # 逻辑: 如果是 "第X天"，且有当前日期，则 start_date = current_date - (X-1) days
                if perf.date and perf.days_info and '第' in perf.days_info:
                    try:
                        day_num_match = re.search(r'第(\d+)天', perf.days_info)
                        if day_num_match:
                            day_num = int(day_num_match.group(1))
                            if day_num > 1:
                                # Convert date string to datetime object
                                # Format: 2026年1月20日
                                date_obj = datetime.strptime(perf.date, '%Y年%m月%d日')
                                start_date_obj = date_obj - timedelta(days=day_num - 1)
                                perf.start_date = start_date_obj.strftime('%Y年%m月%d日')
                            else:
                                perf.start_date = perf.date
                        else:
                             perf.start_date = perf.date
                    except Exception as e:
                        print(f"Date calculation error: {e}")
                        perf.start_date = perf.date
                else:
                    perf.start_date = perf.date

                # 3. 计算结束日期
                # 逻辑优化：如果不自动推算(from total_days)，则尝试从【剧目详情】中提取最后一天
                # 示例：
                # （2月26日）晚上《...》
                # ...
                # （3月2日）下午《...》 -> End Date = 3月2日
                
                calculated_end_date = ""
                
                if perf.shows:
                    last_show_date = None
                    last_show_date_str = ""
                    
                    # 当前基准年份 (默认为文章年份)
                    base_year = datetime.now().year
                    if perf.start_date:
                        try:
                            start_dt = datetime.strptime(perf.start_date, '%Y年%m月%d日')
                            base_year = start_dt.year
                        except:
                            pass

                    for show in perf.shows:
                        # 尝试从 show.time (e.g. "（2月26日）晚上") 或 show.info 中提取日期
                        # 优先匹配 "X月X日" 格式
                        # Combined check string
                        full_show_str = (show.time + " " + show.info)
                        
                        # Regex to find dates like 2月26日, 02月26日
                        # 排除年份，因为通常只有月日
                        date_matches = re.finditer(r'(\d{1,2})月(\d{1,2})日', full_show_str)
                        
                        for match in date_matches:
                            try:
                                m = int(match.group(1))
                                d = int(match.group(2))
                                
                                # Construct date object
                                # Simple logic: use base_year. If month is smaller than start month by a lot, maybe next year? 
                                # But usually performances are within same year or adjacent.
                                # Let's assume same year for now, or next year if month < start_month and start_month is Dec
                                
                                # To be safe, just use base_year. 
                                # Context: "2026年..." so base_year is 2026.
                                
                                current_dt = datetime(base_year, m, d)
                                
                                # Check for year rollover (e.g. starts in Dec, ends in Jan)
                                # If we have a start date, we can compare
                                if perf.start_date:
                                    start_dt = datetime.strptime(perf.start_date, '%Y年%m月%d日')
                                    # If extracted date is significantly before start date (e.g. Start Dec, Found Jan), add 1 year
                                    if m < start_dt.month and start_dt.month == 12:
                                         current_dt = datetime(base_year + 1, m, d)
                                    # If extracted date is significantly after (unlikely for "last date" logic but possible)
                                
                                if last_show_date is None or current_dt > last_show_date:
                                    last_show_date = current_dt
                                    last_show_date_str = f"{current_dt.year}年{m}月{d}日"
                            except:
                                continue
                    
                    if last_show_date_str:
                         # 如果找到的最后日期比开始日期晚（或相等），则认为是结束日期
                         # 且只有当它真的晚于开始日期时才设定？或者直接设定
                         # User says: "那么结束日期就是3月2日"
                         calculated_end_date = last_show_date_str

                perf.end_date = calculated_end_date

                performances.append(perf)
                perf_id_counter += 1
                continue
            
            i += 1
            
        # Helper for sort key
        def get_sort_date(p):
            if not p.start_date:
                return datetime.max
            try:
                return datetime.strptime(p.start_date.strip(), '%Y年%m月%d日')
            except ValueError:
                print(f"Skipping sort for item {p.id}: Invalid date format '{p.start_date}'")
                return datetime.max

        # 按开始日期排序 (Sort by start_date ascending)
        try:
            performances.sort(key=get_sort_date)
            print("Sorting completed successfully.")
        except Exception as e:
            print(f"CRITICAL Sorting error: {e}")
            
        return performances

    def _is_skip_line(self, line):
        """判断是否是需要跳过的无关行"""
        skip_keywords = ['请点', '击', '上面', '蓝字', '免费', '订阅', '关注本公众号', '越剧戏讯', 
                         '最新戏讯', '查看戏讯', '免责声明']
        if any(k in line for k in skip_keywords):
            return True
        # 纯地区标题往往只有几个字且无数字
        if len(line) < 10 and line.endswith('地区戏讯'):
            return True
        return False

    def _backtrack_venue(self, lines, idx):
        """向前回溯寻找地点信息"""
        parts = []
        while idx >= 0:
            line = lines[idx]
            # Stop conditions
            if ('【' in line or 
                re.match(r'（\d{4}年', line) or 
                re.match(r'^(\d{4}年)', line) or
                any(t in line for t in ['下午', '晚上']) or
                '演出第' in line):
                break
            
            if not self._is_skip_line(line) and '农历' not in line and '星期' not in line:
                parts.insert(0, line)
            
            # Simple heuristic: don't look back too far (e.g. 3 lines) to avoid merging headers
            if len(parts) >= 3: 
                break
            idx -= 1
        return "".join(parts)

    def _parse_inline_date(self, text):
        """解析行内日期: 支持多种格式变体
           - （2026年1月20日<农历...>）
           - 2026年1月20日<农历...>）（缺少开头括号）
           - （2026年1月20日＜农历...＞）（全角尖括号）
           - （2026年1月20日<农历...>（缺少结尾括号）
        """
        # 统一的日期模式，支持所有变体
        # （?表示开头括号可选，[<＜]表示半角或全角左尖括号，）?表示结尾括号可选
        pattern = r'（?(\d{4}年\d{1,2}月\d{1,2}日)[<＜《]([^>＞》]+)[>＞》]）?'
        
        match = re.search(pattern, text)
        if match:
            date = match.group(1)
            lunar = match.group(2)
            # 使用re.sub移除所有匹配的日期模式（包括所有变体）
            clean_text = re.sub(pattern, '', text).strip()
            return date, lunar, clean_text
        
        return None, None, text

    def _parse_show_line(self, line):
        """解析剧目行"""
        # Format 1: (Date) Time: Info
        # Format 2: Time: Info
        
        # Check for explicit date prefix first: （1月22日） or （2026年...）
        date_prefix = ""
        date_match = re.match(r'（(\d+月\d+日)）', line)
        if date_match:
            date_prefix = date_match.group(1) + " "
            content = line[date_match.end():].strip()
        else:
            content = line
            
        # Match "下午[:：]..."
        time_match = re.match(r'(下午|晚上|日场|夜场)[:：](.+)', content)
        if time_match:
            time_part = date_prefix + time_match.group(1)
            info_part = time_match.group(2).strip()
            return Show(time=time_part, info=info_part)
        
        # Fallback: if line has date prefix but no explicit time keyword?
        if date_prefix and content:
             return Show(time=date_prefix.strip(), info=content)
             
        return None

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

if __name__ == '__main__':
    # Local test
    test_url = 'https://mp.weixin.qq.com/s/wg5cEjxl6ECctuQf1pXrjQ'
    print("Testing Parser...")
    with WeChatArticleParser(headless=False) as p:
        res = p.parse_article(test_url)
        print(f"Success: {res.get('success')}")
        if res.get('success'):
            data = res['data']['performances']
            print(f"Found {len(data)} items.")
            for item in data[:3]:
                print(item)
