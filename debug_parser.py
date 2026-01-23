import json
from bs4 import BeautifulSoup

file_path = '/Users/lu/AIProjects/垟里唱台小程序/xixun-parser/backend/data/result_20260123_005044.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

content_html = data['data']['content_html']
soup = BeautifulSoup(content_html, 'html.parser')

p_tags = soup.find_all(['p', 'section', 'h1', 'h2', 'h3'])
p_texts = []
for p in p_tags:
    text = p.get_text().strip()
    if text:
        p_texts.append(text)

print(f"Total lines extracted: {len(p_texts)}")
for i, line in enumerate(p_texts):
    if "青湾村" in line:
        print(f"Line {i}: {line}")
        # Check surrounding lines
        if i > 0:
            print(f"Prev Line {i-1}: {p_texts[i-1]}")
        if i < len(p_texts) - 1:
            print(f"Next Line {i+1}: {p_texts[i+1]}")
