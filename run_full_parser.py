from backend.parser import WeChatArticleParser
import json
from bs4 import BeautifulSoup

# Load actual content
file_path = '/Users/lu/AIProjects/垟里唱台小程序/xixun-parser/backend/data/result_20260123_005044.json'
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

content_html = data['data']['content_html']

print("--- Starting Full Parse ---")
parser = WeChatArticleParser()

# Run extraction logic
performances = parser._extract_performances(content_html)
print(f"Extracted {len(performances)} performances.")

found = False
for p in performances:
    if "青湾村" in p.venue:
        print(f"FOUND Qingwan: ID={p.id}, Venue={p.venue}")
        found = True

if not found:
    print("Qingwan STILL NOT FOUND inside extraction results.")
