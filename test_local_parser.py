#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试解析器 - 使用本地HTML文件
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from bs4 import BeautifulSoup
import re
import json


def extract_performances_from_file(html_file):
    """从本地HTML文件提取戏讯数据"""
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'lxml')
    
    # 移除script和style
    for tag in soup(['script', 'style']):
        tag.decompose()
    
    # 获取文本
    text_content = soup.get_text(separator='\n', strip=True)
    lines = [line.strip() for line in text_content.split('\n') if line.strip()]
    
    print(f"总行数: {len(lines)}\n")
    
    performances = []
    i = 0
    perf_id = 1
    
    while i < len(lines):
        line = lines[i]
        
        # 跳过标题和无关内容
        if any(skip in line for skip in ['请点', '击', '上面', '蓝字', '免费', '订阅', '关注本公众号', '越剧戏讯', '最新戏讯', '查看戏讯']):
            i += 1
            continue
        
        # 跳过地区标题
        if re.match(r'^[^\d（【]+地区戏讯$', line) or re.match(r'^[^\d（【]+近期演出$', line):
            i += 1
            continue
        
        # 跳过日期标题
        if re.match(r'^(\d{4}年\d{1,2}月\d{1,2}日)$', line):
            i += 1
            continue
        
        # 检测包含【剧团】的行
        troupe_match = re.search(r'【([^】]+)】', line)
        
        if troupe_match:
            troupe = troupe_match.group(1)
            venue_part = line[:troupe_match.start()].strip()
            
            # 检查前一行是否是地点的一部分
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
            
            # 检查括号日期
            date_match = re.search(r'（(\d{4}年\d{1,2}月\d{1,2}日)<([^>]+)>）', venue_part)
            if date_match:
                date = date_match.group(1)
                lunar_date = date_match.group(2)
                venue = venue_part[date_match.end():].strip()
            
            # 检查定位信息
            location_match = re.search(r'（定位([^）]+)）', venue)
            if location_match:
                location_note = location_match.group(1)
                venue = venue.replace(location_match.group(0), '').strip()
            
            performance = {
                'id': perf_id,
                'date': date,
                'lunar_date': lunar_date,
                'venue': venue,
                'location_note': location_note,
                'troupe': troupe,
                'shows': [],
                'days_info': ''
            }
            
            i += 1
            
            # 读取后续信息
            while i < len(lines):
                next_line = lines[i]
                
                # 演出天数
                if re.match(r'（演出第\d+天）', next_line):
                    performance['days_info'] = next_line
                    i += 1
                    break
                
                # 剧目信息
                show_match = re.match(r'(下午|晚上)[:：](.+)', next_line)
                if show_match:
                    performance['shows'].append({
                        'time': show_match.group(1),
                        'info': show_match.group(2)
                    })
                    i += 1
                    continue
                
                # 多日演出
                multi_day_match = re.match(r'（(\d+月\d+日)）(.+)', next_line)
                if multi_day_match and date:
                    performance['shows'].append({
                        'date': multi_day_match.group(1),
                        'info': multi_day_match.group(2)
                    })
                    i += 1
                    continue
                
                # 结束当前演出
                if '【' in next_line or re.match(r'（\d{4}年', next_line):
                    break
                
                i += 1
                break
            
            performances.append(performance)
            perf_id += 1
        else:
            i += 1
    
    return performances


if __name__ == '__main__':
    html_file = 'backend/data/temp_content.html'
    
    print("=" * 80)
    print("测试解析器 - 使用本地HTML文件")
    print("=" * 80)
    print(f"文件: {html_file}\n")
    
    performances = extract_performances_from_file(html_file)
    
    print(f"\n✓ 解析完成!")
    print(f"共提取 {len(performances)} 条戏讯数据\n")
    
    # 显示前10条
    print("=" * 80)
    print("前10条数据示例:")
    print("=" * 80)
    
    for perf in performances[:10]:
        print(f"\n【{perf['id']}】 {perf['troupe']}")
        if perf['date']:
            print(f"  日期: {perf['date']} ({perf['lunar_date']})")
        print(f"  地点: {perf['venue']}")
        if perf['location_note']:
            print(f"  定位: {perf['location_note']}")
        if perf['shows']:
            print(f"  剧目: {len(perf['shows'])}场")
            for show in perf['shows']:
                if 'date' in show:
                    print(f"    {show['date']}: {show['info'][:50]}...")
                else:
                    print(f"    {show['time']}: {show['info'][:50]}...")
        if perf['days_info']:
            print(f"  {perf['days_info']}")
    
    # 保存结果
    output_file = 'backend/data/parsed_performances.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(performances, f, ensure_ascii=False, indent=2)
    
    print(f"\n\n完整结果已保存到: {output_file}")
    print("=" * 80)
