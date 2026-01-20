#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML内容分析工具
用于查看和分析从#js_content提取的HTML内容
"""

import os
import sys
from bs4 import BeautifulSoup
import re

def analyze_html_file(filepath):
    """分析HTML文件内容"""
    
    print("=" * 80)
    print(f"分析文件: {filepath}")
    print("=" * 80)
    
    if not os.path.exists(filepath):
        print(f"错误: 文件不存在 - {filepath}")
        return
    
    # 读取HTML内容
    with open(filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"\n文件大小: {len(html_content):,} 字符\n")
    
    # 使用BeautifulSoup解析
    soup = BeautifulSoup(html_content, 'lxml')
    
    # 移除script和style
    for tag in soup(['script', 'style']):
        tag.decompose()
    
    # 分析结构
    print("=" * 80)
    print("HTML结构分析")
    print("=" * 80)
    
    # 查找所有标签
    all_tags = [tag.name for tag in soup.find_all()]
    tag_counts = {}
    for tag in all_tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    print("\n标签统计:")
    for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"  {tag}: {count}")
    
    # 查找段落
    paragraphs = soup.find_all('p')
    print(f"\n段落数量: {len(paragraphs)}")
    
    # 查找表格
    tables = soup.find_all('table')
    print(f"表格数量: {len(tables)}")
    
    # 查找section
    sections = soup.find_all('section')
    print(f"Section数量: {len(sections)}")
    
    # 提取所有文本
    text_content = soup.get_text(separator='\n', strip=True)
    lines = [line.strip() for line in text_content.split('\n') if line.strip()]
    
    print(f"\n文本行数: {len(lines)}")
    
    # 显示前50行文本
    print("\n" + "=" * 80)
    print("前50行文本内容")
    print("=" * 80)
    for i, line in enumerate(lines[:50], 1):
        print(f"{i:3d}. {line[:100]}")
    
    # 查找可能的数据模式
    print("\n" + "=" * 80)
    print("数据模式分析")
    print("=" * 80)
    
    # 查找日期模式
    date_patterns = [
        r'\d{1,2}月\d{1,2}日',
        r'\d{4}-\d{1,2}-\d{1,2}',
        r'\d{1,2}/\d{1,2}',
    ]
    
    dates_found = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text_content)
        if matches:
            dates_found.extend(matches)
    
    if dates_found:
        print(f"\n找到日期: {len(set(dates_found))} 个")
        print("示例:", list(set(dates_found))[:10])
    
    # 查找时间模式
    time_pattern = r'\d{1,2}:\d{2}'
    times_found = re.findall(time_pattern, text_content)
    if times_found:
        print(f"\n找到时间: {len(set(times_found))} 个")
        print("示例:", list(set(times_found))[:10])
    
    # 查找可能的剧场/地点
    venue_keywords = ['剧院', '剧场', '大剧院', '戏院', '影剧院', '文化馆']
    venues_found = []
    for line in lines:
        for keyword in venue_keywords:
            if keyword in line:
                venues_found.append(line)
                break
    
    if venues_found:
        print(f"\n找到可能的剧场信息: {len(venues_found)} 条")
        print("示例:")
        for venue in venues_found[:5]:
            print(f"  - {venue[:80]}")
    
    # 保存纯文本版本
    text_filepath = filepath.replace('.html', '_text.txt')
    with open(text_filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"\n纯文本已保存到: {text_filepath}")
    
    # 保存HTML结构分析
    structure_filepath = filepath.replace('.html', '_structure.txt')
    with open(structure_filepath, 'w', encoding='utf-8') as f:
        f.write("HTML结构分析\n")
        f.write("=" * 80 + "\n\n")
        f.write(soup.prettify()[:10000])  # 只保存前10000字符
    print(f"HTML结构已保存到: {structure_filepath}")
    
    print("\n" + "=" * 80)
    print("分析完成!")
    print("=" * 80)


if __name__ == '__main__':
    # 查找最新的HTML文件
    data_dir = 'backend/data'
    
    if len(sys.argv) > 1:
        # 使用命令行参数指定的文件
        filepath = sys.argv[1]
    else:
        # 自动查找最新的content_*.html文件
        if os.path.exists(data_dir):
            html_files = [f for f in os.listdir(data_dir) if f.startswith('content_') and f.endswith('.html')]
            if html_files:
                # 按时间排序,取最新的
                html_files.sort(reverse=True)
                filepath = os.path.join(data_dir, html_files[0])
                print(f"使用最新的HTML文件: {filepath}\n")
            else:
                # 尝试temp_content.html
                temp_file = os.path.join(data_dir, 'temp_content.html')
                if os.path.exists(temp_file):
                    filepath = temp_file
                    print(f"使用临时HTML文件: {filepath}\n")
                else:
                    print("错误: 未找到HTML文件")
                    print(f"请先运行解析器,或指定HTML文件路径:")
                    print(f"  python analyze_html.py <filepath>")
                    sys.exit(1)
        else:
            print(f"错误: 目录不存在 - {data_dir}")
            sys.exit(1)
    
    analyze_html_file(filepath)
