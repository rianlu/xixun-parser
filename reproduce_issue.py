import re

def _parse_inline_date(text):
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

text = "（2026年2月26日<农历正月初十>）平阳县腾蛟镇青湾村文化礼堂【宁波市小百花越剧团】"
print(f"Testing text: {text}")

# 1. Test basic extraction
date, lunar, clean_text = _parse_inline_date(text)
print(f"Extraction Result: Date={date}, Lunar={lunar}, Venue={clean_text}")

# 2. Test Troupe extraction logic from parser.py
troupe_match = re.search(r'【([^】]+)】', clean_text)
if troupe_match:
    troupe_name = troupe_match.group(1)
    venue_part = clean_text[:troupe_match.start()].strip()
    print(f"Troupe: {troupe_name}")
    print(f"Final Venue: {venue_part}")
else:
    print("Troupe not found")

