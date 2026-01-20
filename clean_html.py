#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理HTML文件,去除script和style标签,保留主要内容
"""

import re
import sys

def clean_html(input_file, output_file):
    """
    清理HTML文件,去除script和style标签
    
    Args:
        input_file: 输入HTML文件路径
        output_file: 输出清理后的HTML文件路径
    """
    print(f"正在读取文件: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    original_size = len(html_content)
    print(f"原始文件大小: {original_size:,} 字节 ({original_size / 1024 / 1024:.2f} MB)")
    
    # 去除所有script标签及其内容
    print("正在去除 <script> 标签...")
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # 去除所有style标签及其内容
    print("正在去除 <style> 标签...")
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # 去除HTML注释
    print("正在去除 HTML 注释...")
    html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
    
    # 压缩多余的空白字符(可选)
    print("正在压缩空白字符...")
    html_content = re.sub(r'\n\s*\n', '\n', html_content)
    html_content = re.sub(r'  +', ' ', html_content)
    
    cleaned_size = len(html_content)
    print(f"清理后文件大小: {cleaned_size:,} 字节 ({cleaned_size / 1024 / 1024:.2f} MB)")
    print(f"减少了: {original_size - cleaned_size:,} 字节 ({(1 - cleaned_size/original_size)*100:.1f}%)")
    
    # 保存清理后的文件
    print(f"正在保存到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✓ 清理完成!")
    
    # 尝试提取一些关键信息
    print("\n--- 内容预览 ---")
    
    # 查找标题
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE)
    if title_match:
        print(f"标题: {title_match.group(1).strip()}")
    
    # 查找文章标题
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.DOTALL | re.IGNORECASE)
    if h1_match:
        h1_text = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
        print(f"文章标题: {h1_text}")
    
    # 查找段落数量
    paragraphs = re.findall(r'<p[^>]*>.*?</p>', html_content, re.DOTALL | re.IGNORECASE)
    print(f"段落数量: {len(paragraphs)}")
    
    # 查找表格数量
    tables = re.findall(r'<table[^>]*>.*?</table>', html_content, re.DOTALL | re.IGNORECASE)
    print(f"表格数量: {len(tables)}")
    
    return html_content

if __name__ == '__main__':
    input_file = '/Users/lu/AIProjects/戏讯解析助手/网页源代码.html'
    output_file = '/Users/lu/AIProjects/戏讯解析助手/网页源代码_cleaned.html'
    
    clean_html(input_file, output_file)
