import json

file_path = '/Users/lu/AIProjects/垟里唱台小程序/xixun-parser/backend/data/result_20260123_005044.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

html = data['data']['content_html']
target = "青湾村"
idx = html.find(target)

if idx != -1:
    start = max(0, idx - 200)
    end = min(len(html), idx + 200)
    print(f"Context found:\n{html[start:end]}")
else:
    print("Target not found in HTML")
