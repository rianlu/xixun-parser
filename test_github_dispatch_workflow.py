import os
import unittest


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKFLOW_PATH = os.path.join(ROOT_DIR, ".github", "workflows", "sync.yml")
CLI_PATH = os.path.join(ROOT_DIR, "backend", "cli.py")


class GitHubDispatchWorkflowTests(unittest.TestCase):
    def test_sync_workflow_supports_dispatch_inputs(self):
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as workflow_file:
            workflow_content = workflow_file.read()

        self.assertNotIn("schedule:", workflow_content)
        self.assertIn("workflow_dispatch:", workflow_content)
        self.assertIn("inputs:", workflow_content)
        self.assertIn("url:", workflow_content)
        self.assertIn("chat_id:", workflow_content)

    def test_sync_workflow_runs_script_with_input_url(self):
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as workflow_file:
            workflow_content = workflow_file.read()

        self.assertNotIn("backend.telegram_workflow", workflow_content)
        self.assertIn('./one_click_sync.sh "${{ github.event.inputs.url }}" -y', workflow_content)
        self.assertIn("api.telegram.org", workflow_content)

    def test_cli_exits_with_status_code(self):
        with open(CLI_PATH, "r", encoding="utf-8") as cli_file:
            cli_content = cli_file.read()

        self.assertIn("return 1", cli_content)
        self.assertIn("raise SystemExit(main())", cli_content)


if __name__ == "__main__":
    unittest.main()
