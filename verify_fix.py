
import sys
import os

# Add parent directory to path so we can import backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.parser import WeChatArticleParser

def verify():
    parser = WeChatArticleParser(headless=True)
    test_str = "2026年2月14日《农历十二月二十七》平阳县水头镇南湖塔院街"
    print(f"Testing string: {test_str}")
    
    date, lunar, clean = parser._parse_inline_date(test_str)
    
    print(f"Extracted Date: {date}")
    print(f"Extracted Lunar: {lunar}")
    print(f"Remaining Text: {clean}")
    
    if date == "2026年2月14日" and lunar == "农历十二月二十七":
        print("VERIFICATION SUCCESS: Date and Lunar correctly extracted.")
        return True
    else:
        print("VERIFICATION FAILED: Incorrect extraction.")
        return False

if __name__ == "__main__":
    if verify():
        sys.exit(0)
    else:
        sys.exit(1)
