#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试解析器 - 使用本地HTML文件验证 backend.parser.WeChatArticleParser
"""

import sys
import os
import json

# 添加模块路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.parser import WeChatArticleParser, Performance

def test_local_html(html_file):
    """测试本地HTML解析"""
    if not os.path.exists(html_file):
        print(f"错误: 文件不存在 {html_file}")
        return

    print(f"正在读取文件: {html_file}")
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    print(f"HTML长度: {len(html_content)} 字符")
    
    # 实例化解析器 (headless=True, 但这里主要用它的静态逻辑)
    parser = WeChatArticleParser(headless=True)
    
    # 直接调用提取方法
    print("\n开始提取数据...")
    try:
        performances = parser._extract_performances(html_content)
        
        print(f"\n✓ 解析成功!")
        print(f"共提取 {len(performances)} 条戏讯数据\n")
        
        # 显示前10条
        print("=" * 80)
        print("前10条数据示例:")
        print("=" * 80)
        
        for perf in performances[:10]:
            print(f"\n【{perf.id}】 {perf.troupe}")
            if perf.date:
                print(f"  日期: {perf.date} ({perf.lunar_date})")
            print(f"  地点: {perf.venue}")
            if perf.location_note:
                print(f"  定位: {perf.location_note}")
            
            if perf.shows:
                print(f"  剧目: {len(perf.shows)}场")
                for show in perf.shows:
                     time = show.time
                     info = show.info
                     print(f"    - [{time}] {info}")
            
            if perf.days_info:
                print(f"  {perf.days_info}")
                
        # 保存结果
        output_file = 'backend/data/parsed_performances_new.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            # dataclass list to dict
            json_data = [p.to_dict() for p in performances]
            json.dump(json_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n完整结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"\n❌ 解析出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # 使用之前保存的临时HTML文件，如果不存在则报错
    html_file = 'backend/data/temp_content.html'
    
    # 如果 data 下有 content_*.html 文件，也可以优先使用最新的
    data_dir = 'backend/data'
    if os.path.exists(data_dir):
        files = [f for f in os.listdir(data_dir) if f.startswith('content_') and f.endswith('.html')]
        if files:
            files.sort(reverse=True)
            html_file = os.path.join(data_dir, files[0])
    
    test_local_html(html_file)
