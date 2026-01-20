#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试地点解析问题
"""

text = """苍南县大渔镇天后宫【台州市椒江弘艺越剧团】
苍南灵溪镇
灵峰村
【黄岩桔香越剧二团】
乐清市芙蓉镇筋竹村孔氏祠堂 【临海市亿亿越剧团】"""

lines = [line.strip() for line in text.split('\n') if line.strip()]

import re

for i, line in enumerate(lines):
    print(f"{i}: {line}")
    troupe_match = re.search(r'【([^】]+)】', line)
    if troupe_match:
        troupe = troupe_match.group(1)
        venue_part = line[:troupe_match.start()].strip()
        
        print(f"  找到剧团: {troupe}")
        print(f"  当前行地点部分: '{venue_part}'")
        
        # 如果当前行没有地点,向前查找
        if not venue_part and i > 0:
            print(f"  向前查找地点...")
            prev_lines = []
            j = i - 1
            while j >= 0:
                prev_line = lines[j]
                print(f"    检查第{j}行: {prev_line}")
                # 如果遇到【】,停止
                if '【' in prev_line:
                    print(f"      遇到【】,停止")
                    break
                # 添加到地点列表
                prev_lines.insert(0, prev_line)
                print(f"      添加到地点")
                j -= 1
            
            if prev_lines:
                venue_part = ''.join(prev_lines)
                print(f"  合并后的地点: '{venue_part}'")
        
        print()
