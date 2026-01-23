import requests
import json
import hashlib
import time
import os
import glob
from datetime import datetime
import re

# --- Configuration ---
APP_ID = 'cli_a9dcd7700c38dbd8'
APP_SECRET = 'r23Hpe3TxzIOvGpuQVSMTel6aQUh21cu'
BASE_TOKEN = 'RqoNbb8Ufa7LIGsYXzTcsvZPnl8'
TABLE_ID = 'tbl3JeOpAwlX90f9'

# Field Names Mapping (JSON key -> Feishu Field Name)
FIELD_MAP = {
    'troupe': '剧团或词师名称',
    'venue': '地址', # Warning: Check if this is Location type or Text type
    'start_date': '开始日期',
    'end_date': '结束日期',
    'content': '内容详情',
    'total_days': '总演出天数',
    'type': '类型'
}
SOURCE_FIELD = '数据来源'
SYSTEM_TAG = 'System'

class FeishuSync:
    def __init__(self):
        self.token = None

    def get_token(self):
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": APP_ID,
            "app_secret": APP_SECRET
        }
        resp = requests.post(url, json=payload)
        data = resp.json()
        if data.get("code") == 0:
            self.token = data["tenant_access_token"]
            return self.token
        raise Exception(f"Failed to get token: {data}")

    def get_header(self):
        if not self.token:
            self.get_token()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def fetch_all_records(self):
        """Fetch all records to build local cache for fingerprinting"""
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_TOKEN}/tables/{TABLE_ID}/records/search"
        records = []
        page_token = None
        
        while True:
            payload = {"page_size": 500}
            if page_token:
                payload["page_token"] = page_token
            
            resp = requests.post(url, headers=self.get_header(), json=payload)
            data = resp.json()
            
            if data.get("code") != 0:
                print(f"Error fetching records: {data}")
                break
                
            if "data" in data and "items" in data["data"]:
                records.extend(data["data"]["items"])
            
            if data["data"].get("has_more"):
                page_token = data["data"]["page_token"]
            else:
                break
                
        return records

    def create_record(self, fields):
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_TOKEN}/tables/{TABLE_ID}/records"
        payload = {"fields": fields}
        resp = requests.post(url, headers=self.get_header(), json=payload)
        return resp.json()

    def update_record(self, record_id, fields):
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_TOKEN}/tables/{TABLE_ID}/records/{record_id}"
        payload = {"fields": fields}
        resp = requests.put(url, headers=self.get_header(), json=payload)
        return resp.json()

    def delete_record(self, record_id):
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_TOKEN}/tables/{TABLE_ID}/records/{record_id}"
        resp = requests.delete(url, headers=self.get_header())
        return resp.json()

    def batch_create(self, records_fields):
        if not records_fields: return
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_TOKEN}/tables/{TABLE_ID}/records/batch_create"
        
        chunk_size = 100
        for i in range(0, len(records_fields), chunk_size):
            chunk = records_fields[i:i+chunk_size]
            payload = {"records": [{"fields": f} for f in chunk]}
            try:
                resp = requests.post(url, headers=self.get_header(), json=payload)
                data = resp.json()
                if data.get('code') != 0:
                    print(f"Batch create error: {data}")
                    raise Exception(f"Feishu API Error ({data.get('code')}): {data.get('msg')}")
            except Exception as e:
                print(f"Batch create request failed: {e}")
                raise e

    def batch_update(self, records_data):
        if not records_data: return
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_TOKEN}/tables/{TABLE_ID}/records/batch_update"
        
        chunk_size = 100
        for i in range(0, len(records_data), chunk_size):
            chunk = records_data[i:i+chunk_size]
            payload = {"records": chunk}
            try:
                resp = requests.post(url, headers=self.get_header(), json=payload)
                data = resp.json()
                if data.get('code') != 0:
                    print(f"Batch update error: {data}")
                    raise Exception(f"Feishu API Error ({data.get('code')}): {data.get('msg')}")
            except Exception as e:
                print(f"Batch update request failed: {e}")
                raise e

    def batch_delete(self, record_ids):
        if not record_ids: return
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_TOKEN}/tables/{TABLE_ID}/records/batch_delete"
        
        chunk_size = 100
        for i in range(0, len(record_ids), chunk_size):
            chunk = record_ids[i:i+chunk_size]
            payload = {"records": chunk}
            try:
                resp = requests.post(url, headers=self.get_header(), json=payload)
                data = resp.json()
                if data.get('code') != 0:
                    print(f"Batch delete error: {data}")
                    raise Exception(f"Feishu API Error ({data.get('code')}): {data.get('msg')}")
            except Exception as e:
                print(f"Batch delete request failed: {e}")
                raise e

    def parse_cn_date(self, date_str):
        """Convert '2026年2月5日' to timestamp (ms)"""
        if not date_str: return None
        try:
            dt = datetime.strptime(date_str, "%Y年%m月%d日")
            return int(dt.timestamp() * 1000)
        except:
            return None

    def normalize_date(self, val):
        """Normalize date to YYYY-MM-DD string"""
        if isinstance(val, int): # Timestamp (ms)
            dt = datetime.fromtimestamp(val / 1000)
            return dt.strftime("%Y-%m-%d")
        elif isinstance(val, str):
            # Try parsing various formats
            # 1. YYYY年M月D日
            try:
                dt = datetime.strptime(val, "%Y年%m月%d日")
                return dt.strftime("%Y-%m-%d")
            except: pass
            
            # 2. YYYY-MM-DD
            try:
                dt = datetime.strptime(val, "%Y-%m-%d")
                return dt.strftime("%Y-%m-%d")
            except: pass
            
            return val
        return ""

    def generate_fingerprint(self, date_val, troupe, venue):
        # Normalize date
        d_str = self.normalize_date(date_val)
        # Normalize troupe/venue (strip)
        t_str = str(troupe).strip()
        v_str = str(venue).strip()
        
        s = f"{d_str}|{t_str}|{v_str}"
        return hashlib.md5(s.encode('utf-8')).hexdigest()

    def calculate_sync_plan(self, local_data):
        # 1. Fetch remote data
        remote_records = self.fetch_all_records()
        remote_count = len(remote_records)
        
        # Helper function to extract text from Feishu field formats
        def extract_text(field):
            """Extract text from various Feishu field formats"""
            if not field:
                return ""
            # String
            if isinstance(field, str):
                return field
            # Array of text objects: [{'text': '...', 'type': 'text'}]
            if isinstance(field, list) and len(field) > 0:
                if isinstance(field[0], dict) and 'text' in field[0]:
                    return field[0]['text']
                return str(field[0])
            # Location object: {'name': '...', 'full_address': '...'}
            if isinstance(field, dict):
                return field.get("full_address", "") or field.get("name", "") or field.get("text", "")
            return str(field)
        
        # 2. Build Remote Index: Fingerprint -> Record
        remote_idx = {}
        for r in remote_records:
            fds = r["fields"]
            r_date = fds.get(FIELD_MAP['start_date'])
            r_troupe = extract_text(fds.get(FIELD_MAP['troupe'], ""))
            r_venue = extract_text(fds.get(FIELD_MAP['venue'], ""))
            r_content = extract_text(fds.get(FIELD_MAP['content'], ""))
            
            fp = self.generate_fingerprint(r_date, r_troupe, r_venue)
            source = fds.get(SOURCE_FIELD, "")
            
            remote_idx[fp] = {
                "id": r["record_id"],
                "source": source,
                "fields": fds,
                "date_ts": r_date if isinstance(r_date, int) else 0,
                "troupe": r_troupe,
                "venue": r_venue,
                "content": r_content
            }

        # 3. Full Replacement Strategy
        # Step 1: Collect all System records for deletion
        # Step 2: Create all new records from local data
        actions = []
        
        for perf in local_data:
            start_date = perf.get("start_date")
            troupe = perf.get("troupe")
            venue = perf.get("venue")

            # Build fields payload
            fields = {}
            st_ts = self.parse_cn_date(start_date)
            et_ts = self.parse_cn_date(perf.get("end_date"))
            
            if st_ts: fields[FIELD_MAP['start_date']] = st_ts
            if et_ts: fields[FIELD_MAP['end_date']] = et_ts
            
            fields[FIELD_MAP['troupe']] = troupe
            fields[FIELD_MAP['venue']] = venue 
            
            # Format content: keep it simple
            # - Single-day: just output "time info" (e.g., "下午 加演《祭塔》正本《王老虎抢亲》")
            # - Multi-day: output "date info" with date converted to M.D format (e.g., "2.26 晚上《追鱼》加《打八仆》")
            raw_content = ""
            if perf.get("shows"):
                show_strs = []
                for s in perf["shows"]:
                    prefix = s.get("date", "") or s.get("time", "")
                    info = s.get("info", "")
                    
                    # Convert date format: '2月26日' -> '2.26'
                    if prefix:
                        prefix = re.sub(r'(\d+)月(\d+)日', r'\1.\2', prefix)
                    
                    # Simple concatenation
                    if prefix:
                        show_strs.append(f"{prefix} {info}")
                    else:
                        show_strs.append(info)
                
                raw_content = "\n".join(show_strs)
            
            fields[FIELD_MAP['content']] = raw_content
            
            # Type
            perf_type = perf.get("type", "戏剧")
            fields[FIELD_MAP['type']] = perf_type
            
            # Total days
            if perf.get("total_days"):
                try: 
                    fields[FIELD_MAP['total_days']] = int(perf.get("total_days"))
                except: 
                    pass
            
            # Data source
            fields[SOURCE_FIELD] = SYSTEM_TAG

            # All local data will be created (full replacement)
            actions.append({
                "type": "CREATE",
                "desc": f"新增: {troupe} @ {venue}",
                "fields": fields,
                "troupe": troupe,
                "venue": venue,
                "date": start_date,
                "end_date": perf.get("end_date", ""),
                "content": raw_content
            })


        # 4. Delete all System records (full replacement)
        for fp, rem in remote_idx.items():
            if rem["source"] == SYSTEM_TAG:
                # Extract end_date from remote record
                r_end_date = rem["fields"].get(FIELD_MAP['end_date'])
                end_date_str = ""
                if r_end_date:
                    if isinstance(r_end_date, int):
                        end_date_str = datetime.fromtimestamp(r_end_date/1000).strftime('%Y-%m-%d')
                    else:
                        end_date_str = str(r_end_date)
                
                # Insert DELETE actions at the beginning (delete first, then create)
                actions.insert(0, {
                    "type": "DELETE",
                    "desc": f"清理旧数据: {rem['troupe']} @ {rem['venue']}",
                    "id": rem["id"],
                    "troupe": rem["troupe"],
                    "venue": rem["venue"],
                    "date": datetime.fromtimestamp(rem["date_ts"]/1000).strftime('%Y-%m-%d') if rem["date_ts"] else "Unknown",
                    "end_date": end_date_str,
                    "content": rem.get("content", "")
                })


        return {"actions": actions, "remote_count": remote_count}

    def execute_sync_plan(self, actions):
        """Execute the calculated plan using Batch APIs"""
        stats = {"create": 0, "update": 0, "delete": 0, "skip": 0, "error": 0}
        
        to_create = []
        to_update = []
        to_delete = []

        for action in actions:
            if action["type"] == "CREATE":
                to_create.append(action["fields"])
                stats["create"] += 1
            elif action["type"] == "UPDATE":
                to_update.append({"record_id": action["id"], "fields": action["fields"]})
                stats["update"] += 1
            elif action["type"] == "DELETE":
                to_delete.append(action["id"])
                stats["delete"] += 1
            elif action["type"] == "SKIP":
                stats["skip"] += 1

        print(f"Executing Batch: Create={len(to_create)}, Update={len(to_update)}, Delete={len(to_delete)}")

        # Execute Batches
        if to_create: self.batch_create(to_create)
        if to_update: self.batch_update(to_update)
        if to_delete: self.batch_delete(to_delete)

        return stats

    def run(self):
        # Default run method for CLI usage
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, "data")
        files = glob.glob(os.path.join(data_dir, "result_*.json"))
        if not files:
            print(f"No parsed data found in {data_dir}")
            return
        latest_file = max(files, key=os.path.getctime)
        print(f"Loading local data: {latest_file}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            local_data = json.load(f)["data"]["performances"]

        print("Calculating sync plan...")
        actions = self.calculate_sync_plan(local_data)
        
        print("--- Execution Plan ---")
        for a in actions:
            print(f"[{a['type']}] {a['desc']}")
            
        print(f"\nTotal Actions: {len(actions)}")
        # confirm = input("Confirm execution? (y/n): ")
        # if confirm.lower() == 'y':
        print("Executing...")
        stats = self.execute_sync_plan(actions)
        print(f"Sync Complete. Stats: {stats}")


if __name__ == "__main__":
    syncer = FeishuSync()
    syncer.run()
