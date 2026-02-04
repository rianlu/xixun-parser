
import re

def _parse_inline_date(text):
    """解析行内日期: 支持多种格式变体"""
    # 统一的日期模式，支持所有变体
    # （?表示开头括号可选，[<＜]表示半角或全角左尖括号，）?表示结尾括号可选
    pattern = r'（?(\d{4}年\d{1,2}月\d{1,2}日)[<＜]([^>＞]+)[>＞]）?'
    
    match = re.search(pattern, text)
    if match:
        date = match.group(1)
        lunar = match.group(2)
        # 使用re.sub移除所有匹配的日期模式（包括所有变体）
        clean_text = re.sub(pattern, '', text).strip()
        return date, lunar, clean_text
    
    return None, None, text

test_str = "2026年2月14日《农历十二月二十七》平阳县水头镇南湖塔院街"
date, lunar, clean = _parse_inline_date(test_str)
print(f"Input: {test_str}")
print(f"Date: {date}")
print(f"Lunar: {lunar}")
print(f"Clean: {clean}")

if date == "2026年2月14日":
    print("SUCCESS")
else:
    print("FAILURE")
