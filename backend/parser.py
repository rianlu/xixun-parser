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
        
        # 获取纯文本行
        text_content = soup.get_text(separator='\n', strip=True)
        text_content = soup.get_text(separator='\n', strip=True)
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
                
                if "青湾村" in line or "（2026年2月26日<农历正月初十>）" in line:
                    print(f"DEBUG: Processing line {i}: {line}")
                    print(f"DEBUG: Venue part: '{venue_part}'")

                if not venue_part and i > 0:
                    venue_part = self._backtrack_venue(lines, i - 1)
                
                # 解析本条目的日期（优先级高于全局current_date）
                # Format: （2026年1月20日<农历...>）Place...
                item_date, item_lunar, clean_venue = self._parse_inline_date(venue_part)
                
                # 如果本行没有提取到日期，且上一行有日期信息，说明可能是换行导致的
                # e.g. Prev: (Date) 苍南县
                #      Curr: 灵溪镇...【Troupe】
                if not item_date and i > 0:
                     prev_line = lines[i-1]
                     prev_date, prev_lunar, prev_venue = self._parse_inline_date(prev_line)
                     if prev_date:
                         item_date = prev_date
                         item_lunar = prev_lunar
                         # 合并地址: 上一行的有效地址部分 + 本行的地址部分
                         # 注意: clean_venue 是本行去除日期后的部分(本来就没日期所以就是venue_part)
                         venue_part = prev_venue + clean_venue
                         clean_venue = venue_part

                final_venue = clean_venue
                final_date = item_date if item_date else current_date_info['date']
                final_lunar = item_lunar if item_lunar else current_date_info['lunar']
                
                # 提取定位备注
                loc_note_match = re.search(r'（定位([^）]+)）', final_venue)
                loc_note = ""
                if loc_note_match:
                    loc_note = loc_note_match.group(1)
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
                
                # 1. 提取总天数 (e.g. "演出第3天，共5天" -> 5 or just "3天")
                # 简单逻辑: 寻找数字
                if perf.days_info:
                    days_match = re.search(r'(\d+)', perf.days_info)
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

                # 3. 结束日期目前默认为开始日期，或暂空
                # 如果有总天数，也可以计算结束日期: start + total - 1
                # 根据用户需求：End Date 默认为当前条目日期
                perf.end_date = perf.date

                performances.append(perf)
                perf_id_counter += 1
                continue
            
            i += 1
            
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
        """解析行内日期: （2026年1月20日<农历...>) Venue
           兼容缺失起始括号的情况: 2026年1月20日<农历...>)
        """
        # Regex for （?YYYY年M月D日<农历...>）
        # Make the opening parenthesis optional
        match = re.search(r'（?(\d{4}年\d{1,2}月\d{1,2}日)<([^>]+)>）', text)
        if match:
            date = match.group(1)
            lunar = match.group(2)
            # Remove the date part from text to get clean venue
            clean_text = text.replace(match.group(0), '').strip()
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
