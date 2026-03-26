import os
import subprocess
import sys


WECHAT_DOMAIN = "mp.weixin.qq.com"


def normalize_text(text):
    return (text or "").strip()


def is_wechat_article(text):
    return WECHAT_DOMAIN in normalize_text(text)


def collect_processable_updates(results):
    processable = []
    seen_update_ids = set()

    for update in results:
        update_id = update.get("update_id")
        if update_id in seen_update_ids:
            continue

        seen_update_ids.add(update_id)

        message = update.get("message") or {}
        text = normalize_text(message.get("text"))
        chat_id = message.get("chat", {}).get("id")

        if not text or not chat_id or not is_wechat_article(text):
            continue

        processable.append(
            {
                "update_id": update_id,
                "chat_id": chat_id,
                "url": text,
            }
        )

    return processable


class TelegramWorkflowRunner:
    def __init__(self, token, session=None):
        if session is None:
            import requests

            session = requests.Session()

        self.token = token
        self.session = session
        self.api_base = f"https://api.telegram.org/bot{token}"
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def send_msg(self, chat_id, text):
        try:
            response = self.session.post(
                f"{self.api_base}/sendMessage",
                data={"chat_id": chat_id, "text": text},
                timeout=10,
            )
            return response.json()
        except Exception as exc:
            print(f"发送消息失败: {exc}")
            return {}

    def edit_msg(self, chat_id, message_id, text):
        try:
            response = self.session.post(
                f"{self.api_base}/editMessageText",
                data={"chat_id": chat_id, "message_id": message_id, "text": text},
                timeout=10,
            )
            return response.json()
        except Exception as exc:
            print(f"编辑消息失败: {exc}")
            return {}

    def fetch_updates(self):
        response = self.session.get(f"{self.api_base}/getUpdates", timeout=10)
        payload = response.json()
        return payload.get("result", [])

    def acknowledge_update(self, update_id):
        try:
            self.session.get(
                f"{self.api_base}/getUpdates",
                params={"offset": update_id + 1},
                timeout=10,
            )
        except Exception as exc:
            print(f"确认消息已读失败(update_id={update_id}): {exc}")

    def run_cli_sync(self, url):
        cli_path = os.path.join(self.root_dir, "backend", "cli.py")
        return subprocess.run(
            [sys.executable, cli_path, url, "-y"],
            capture_output=True,
            text=True,
        )

    def run(self):
        print("正在拉取待处理消息...")
        results = self.fetch_updates()
        print(f"收到 {len(results)} 条待处理记录。")

        if not results:
            print("暂无新消息。")
            return 0

        unique_updates = {}
        for update in results:
            update_id = update.get("update_id")
            if update_id not in unique_updates:
                unique_updates[update_id] = update

        processable = {
            item["update_id"]: item for item in collect_processable_updates(results)
        }

        for update_id in sorted(unique_updates):
            update = unique_updates[update_id]
            target = processable.get(update_id)

            try:
                if not target:
                    print(f"跳过非目标消息: update_id={update_id}")
                    continue

                url_target = target["url"]
                chat_id = target["chat_id"]
                print(f"🎯 处理链接: {url_target}")

                status_resp = self.send_msg(
                    chat_id,
                    "⌛ 发现戏讯链接，正在解析同步到飞书，请稍候...\n\n"
                    f"🔗 {url_target}",
                )
                msg_id = status_resp.get("result", {}).get("message_id")

                result = self.run_cli_sync(url_target)

                if result.returncode == 0:
                    final_text = (
                        "✅ 同步成功！\n数据已解析并更新至飞书多维表格。\n\n"
                        f"🔗 {url_target}"
                    )
                else:
                    err_info = result.stderr or result.stdout
                    final_text = (
                        "❌ 同步失败！\n\n"
                        f"原因: {err_info[:200]}...\n\n"
                        f"🔗 {url_target}"
                    )

                if msg_id:
                    self.edit_msg(chat_id, msg_id, final_text)
                else:
                    self.send_msg(chat_id, final_text)
            finally:
                self.acknowledge_update(update_id)

        return 0


def main():
    token = os.getenv("TG_TOKEN")
    if not token:
        print("缺少环境变量 TG_TOKEN")
        return 1

    try:
        runner = TelegramWorkflowRunner(token)
        return runner.run()
    except Exception as exc:
        print(f"执行 Telegram workflow 失败: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
