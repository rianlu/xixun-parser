#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本 - 解析文章并分析HTML内容
"""

import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from parser import WeChatArticleParser

def main():
    test_url = 'https://mp.weixin.qq.com/s/wg5cEjxl6ECctuQf1pXrjQ'
    
    print("=" * 80)
    print("戏讯解析器测试")
    print("=" * 80)
    print(f"\n测试链接: {test_url}\n")
    
    # 使用非headless模式,可以看到浏览器操作
    with WeChatArticleParser(headless=False) as parser:
        print("正在解析...")
        result = parser.parse_article(test_url)
        
        if result['success']:
            print("\n✓ 解析成功!")
            print(f"文章标题: {result['data']['title']}")
            print(f"数据条数: {result['data']['total']}")
            print(f"\nHTML内容已保存到: backend/data/temp_content.html")
            print(f"内容长度: {len(result['data']['content_html'])} 字符")
            
            # 显示前10条数据
            print("\n前10条数据:")
            for i, perf in enumerate(result['data']['performances'][:10], 1):
                print(f"{i}. {perf.get('raw_text', '')[:100]}")
            
            print("\n" + "=" * 80)
            print("下一步: 运行分析工具查看HTML结构")
            print("  python3 analyze_html.py")
            print("=" * 80)
        else:
            print(f"\n✗ 解析失败: {result.get('error', '未知错误')}")

if __name__ == '__main__':
    main()
