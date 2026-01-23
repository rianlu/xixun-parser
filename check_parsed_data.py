import json

file_path = '/Users/lu/AIProjects/垟里唱台小程序/xixun-parser/backend/data/result_20260123_005044.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

performances = data['data']['performances']
print(f"Total performances: {len(performances)}")

found = False
for p in performances:
    if "青湾村" in p['venue']:
        print(f"Found Qingwan: {p}")
        found = True
    if "鹭鸶湾" in p['venue']:
        print(f"Found Lusiwan: {p}")

if not found:
    print("Qingwan NOT found in performances.")
