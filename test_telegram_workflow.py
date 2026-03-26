import os
import sys
import unittest


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)


from backend.telegram_workflow import collect_processable_updates


class TelegramWorkflowTests(unittest.TestCase):
    def test_collect_processable_updates_deduplicates_updates(self):
        updates = [
            {
                "update_id": 101,
                "message": {
                    "text": " https://mp.weixin.qq.com/s/example ",
                    "chat": {"id": 123},
                },
            },
            {
                "update_id": 101,
                "message": {
                    "text": "https://mp.weixin.qq.com/s/example",
                    "chat": {"id": 123},
                },
            },
            {
                "update_id": 102,
                "message": {
                    "text": "https://example.com/not-wechat",
                    "chat": {"id": 123},
                },
            },
        ]

        self.assertEqual(
            collect_processable_updates(updates),
            [
                {
                    "update_id": 101,
                    "chat_id": 123,
                    "url": "https://mp.weixin.qq.com/s/example",
                }
            ],
        )

    def test_sync_workflow_uses_concurrency_guard(self):
        workflow_path = os.path.join(ROOT_DIR, ".github", "workflows", "sync.yml")
        with open(workflow_path, "r", encoding="utf-8") as workflow_file:
            workflow_content = workflow_file.read()

        self.assertIn("concurrency:", workflow_content)
        self.assertIn("group: telegram-sync", workflow_content)
        self.assertIn("cancel-in-progress: false", workflow_content)


if __name__ == "__main__":
    unittest.main()
