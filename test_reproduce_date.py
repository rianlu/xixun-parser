
import re

def test_parse_date(text):
    print(f"Testing text: '{text}'")
    
    # Current buggy pattern (from backend/parser.py)
    current_pattern = r'（?(\d{4}年\d{1,2}月\d{1,2}日)[<＜《]([^>＞》]+)[>＞》]）?'
    match = re.search(current_pattern, text)
    print(f"  [Original Regex] Match: {match}")
    if match:
        print(f"    Date: {match.group(1)}")
        print(f"    Lunar: {match.group(2)}")
    
    # Proposed fix pattern
    # 1. Start with optional （
    # 2. Date: \d{4}年...
    # 3. Open bracket: [<＜《]
    # 4. Content: [^>＞》）]+ (anything except close bracket OR close paren)
    # 5. Optional close bracket: [>＞》]?
    # 6. Optional close paren: ）?
    new_pattern = r'（?(\d{4}年\d{1,2}月\d{1,2}日)[<＜《]([^>＞》）]+)[>＞》]?）?'
    
    match_new = re.search(new_pattern, text)
    print(f"  [New Regex] Match: {match_new}")
    if match_new:
        print(f"    Date: {match_new.group(1)}")
        print(f"    Lunar: {match_new.group(2)}")
        clean_text = re.sub(new_pattern, '', text).strip()
        print(f"    Cleaned Text: '{clean_text}'")
    else:
        print("    No match found.")
    print("-" * 40)

if __name__ == "__main__":
    # Case 1: The reported issue (missing closing > but has closing ）)
    test_parse_date("（2026年2月17日<农历正月初一）平阳县萧江后江村")
    
    # Case 2: Standard complete format
    test_parse_date("（2026年2月17日<农历正月初一>）平阳县萧江后江村")
    
    # Case 3: Missing outer parens but partial inner
    test_parse_date("2026年2月17日<农历正月初一）平阳县萧江后江村")
    
    # Case 4: Full width brackets
    test_parse_date("（2026年2月17日＜农历正月初一＞）平阳县萧江后江村")

    # Case 5: No brackets at all (should not match lunar pattern, but maybe date?)
    # The regex requires the < part, so this shouldn't match the lunar pattern.
    test_parse_date("2026年2月17日 平阳县萧江后江村")
