#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
戏讯解析助手 - 优化的数据解析器
根据实际HTML结构提取戏讯数据
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re
import json
import os


class WeChatArticleParser:
    """微信公众号文章解析器"""
    
    def __init__(self, headless=True):
        """
        初始化解析器
        
        Args:
            headless: 是否使用无头模式
        """
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
        """
        解析微信公众号文章
        
        Args:
            url: 文章链接
            
        Returns:
            dict: 解析结果
        """
        try:
            if not self.driver:
                self._init_driver()
            
            print(f"正在访问: {url}")
            self.driver.get(url)
            
            # 等待页面加载
            time.sleep(3)
            
            # 获取文章标题
            try:
                title_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "activity-name"))
                )
                title = title_element.text
            except:
                title = "未知标题"
            
            print(f"文章标题: {title}")
            
            # 执行JavaScript获取内容
            js_content_html = self.driver.execute_script(
                "return document.querySelector('#js_content') ? document.querySelector('#js_content').innerHTML : '';"
            )
            
            if not js_content_html:
                return {
                    'success': False,
                    'error': '未找到文章内容'
                }
            
            print(f"获取到内容长度: {len(js_content_html)} 字符")
            
            # 保存原始HTML到临时文件供调试
            temp_html_path = os.path.join(os.path.dirname(__file__), 'data', 'temp_content.html')
            os.makedirs(os.path.dirname(temp_html_path), exist_ok=True)
            with open(temp_html_path, 'w', encoding='utf-8') as f:
                f.write(js_content_html)
            print(f"原始HTML已保存到: {temp_html_path}")
            
            # 解析HTML提取戏讯数据
            performances = self._extract_performances(js_content_html)
            
            return {
                'success': True,
                'data': {
                    'title': title,
                    'url': url,
                    'content_html': js_content_html,
                    'performances': performances,
                    'total': len(performances)
                }
            }
            
        except Exception as e:
            print(f"解析出错: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_performances(self, html_content):
        """
        从HTML内容中提取戏讯数据
        
        Args:
            html_content: HTML内容
            
        Returns:
            list: 戏讯数据列表
        """
        soup = BeautifulSoup(html_content, 'lxml')
        performances = []
        
        # 移除所有script和style标签
        for tag in soup(['script', 'style']):
            tag.decompose()
        
        # 获取所有文本内容
        text_content = soup.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        print(f"\n提取到 {len(lines)} 行文本")
        
        # 解析戏讯数据
        i = 0
        perf_id = 1
        
        while i < len(lines):
            line = lines[i]
            
            # 跳过标题和无关内容
            if any(skip in line for skip in ['请点', '击', '上面', '蓝字', '免费', '订阅', '关注本公众号', '越剧戏讯', '最新戏讯', '查看戏讯']):
                i += 1
                continue
            
            # 检测是否是地区标题
            if re.match(r'^[^\d（【]+地区戏讯$', line) or re.match(r'^[^\d（【]+近期演出$', line):
                i += 1
                continue
            
            # 检测是否是日期标题行
            date_header_match = re.match(r'^(\d{4}年\d{1,2}月\d{1,2}日)', line)
            if date_header_match:
                # 这是当天演出的日期标题
                current_date = date_header_match.group(1)
                i += 1
                
                # 读取农历和星期
                lunar = ''
                weekday = ''
                if i < len(lines) and '农历' in lines[i]:
                    lunar = lines[i]
                    i += 1
                if i < len(lines) and '星期' in lines[i]:
                    weekday = lines[i]
                    i += 1
                
                continue
            
            # 检测包含【剧团】的行 - 这是演出信息的起始
            troupe_match = re.search(r'【([^】]+)】', line)
            
            if troupe_match:
                # 提取基本信息
                troupe = troupe_match.group(1)
                venue_part = line[:troupe_match.start()].strip()
                
                # 检查前一行是否是地点的一部分(没有【】且不是日期/剧目信息)
                if i > 0 and venue_part == '':
                    # 【剧团】单独一行,需要向前查找地点
                    prev_lines = []
                    j = i - 1
                    while j >= 0:
                        prev_line = lines[j]
                        # 如果遇到【】或日期格式或演出信息,停止
                        if ('【' in prev_line or 
                            re.match(r'（\d{4}年', prev_line) or 
                            re.match(r'(下午|晚上)[:：]', prev_line) or
                            re.match(r'（演出第\d+天）', prev_line)):
                            break
                        # 如果是普通文本,可能是地点的一部分
                        if prev_line and not any(skip in prev_line for skip in ['请点', '击', '上面', '蓝字', '免费', '订阅', '农历', '星期']):
                            prev_lines.insert(0, prev_line)
                        j -= 1
                    
                    # 合并地点信息
                    if prev_lines:
                        venue_part = ''.join(prev_lines)
                
                # 提取日期和地点
                date = ''
                lunar_date = ''
                venue = venue_part
                location_note = ''
                
                # 检查是否有括号日期
                date_match = re.search(r'（(\d{4}年\d{1,2}月\d{1,2}日)<([^>]+)>）', venue_part)
                if date_match:
                    date = date_match.group(1)
                    lunar_date = date_match.group(2)
                    venue = venue_part[date_match.end():].strip()
                
                # 检查是否有定位信息
                location_match = re.search(r'（定位([^）]+)）', venue)
                if location_match:
                    location_note = location_match.group(1)
                    venue = venue.replace(location_match.group(0), '').strip()
                
                # 初始化演出信息
                performance = {
                    'id': perf_id,
                    'date': date,
                    'lunar_date': lunar_date,
                    'venue': venue,
                    'location_note': location_note,
                    'troupe': troupe,
                    'shows': [],
                    'days_info': '',
                    'raw_text': line
                }

                
                i += 1
                
                # 读取后续的剧目信息和演出天数
                while i < len(lines):
                    next_line = lines[i]
                    
                    # 检查是否是演出天数信息
                    if re.match(r'（演出第\d+天）', next_line):
                        performance['days_info'] = next_line
                        i += 1
                        break
                    
                    # 检查是否是剧目信息(下午/晚上)
                    show_match = re.match(r'(下午|晚上|（\d+月\d+日）下午|（\d+月\d+日）晚上)[:：](.+)', next_line)
                    if show_match:
                        time_period = show_match.group(1)
                        show_info = show_match.group(2)
                        performance['shows'].append({
                            'time': time_period,
                            'info': show_info
                        })
                        i += 1
                        continue
                    
                    # 检查是否是多日演出格式: （X月X日）下午:...晚上:...
                    multi_day_match = re.match(r'（(\d+月\d+日)）(.+)', next_line)
                    if multi_day_match and date:  # 只有在已有起始日期时才处理
                        day_date = multi_day_match.group(1)
                        day_info = multi_day_match.group(2)
                        performance['shows'].append({
                            'date': day_date,
                            'info': day_info
                        })
                        i += 1
                        continue
                    
                    # 如果遇到新的演出信息或无关内容,结束当前演出
                    if '【' in next_line or re.match(r'（\d{4}年', next_line):
                        break
                    
                    # 否则跳过这一行
                    i += 1
                    break
                
                performances.append(performance)
                perf_id += 1
            else:
                i += 1
        
        print(f"解析出 {len(performances)} 条戏讯数据")
        return performances
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == '__main__':
    # 测试代码
    test_url = 'https://mp.weixin.qq.com/s/wg5cEjxl6ECctuQf1pXrjQ'
    
    print("=== 戏讯解析器测试 ===\n")
    
    with WeChatArticleParser(headless=False) as parser:
        result = parser.parse_article(test_url)
        
        if result['success']:
            print("\n✓ 解析成功!")
            print(f"标题: {result['data']['title']}")
            print(f"提取到 {result['data']['total']} 条数据")
            
            # 显示前5条数据
            print("\n前5条数据:")
            for perf in result['data']['performances'][:5]:
                print(f"\n{perf['id']}. {perf['venue']} 【{perf['troupe']}】")
                if perf['date']:
                    print(f"   日期: {perf['date']} {perf['lunar_date']}")
                if perf['shows']:
                    print(f"   剧目: {len(perf['shows'])}场")
                    for show in perf['shows']:
                        print(f"     - {show}")
            
            # 保存结果
            output_file = 'backend/data/test_result.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n结果已保存到: {output_file}")
        else:
            print(f"\n✗ 解析失败: {result['error']}")
