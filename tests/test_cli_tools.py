import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CliToolsTest(unittest.TestCase):
    def run_cmd(self, argv, env=None, cwd=None):
        return subprocess.run(
            argv,
            cwd=cwd or ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_resolve_inventory_prefers_environment_secret(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "inventory.ini"
            env = os.environ.copy()
            env["LDK_INVENTORY"] = "[app]\nvm-a ansible_host=192.0.2.10\n"

            result = self.run_cmd(
                [str(ROOT / "bin" / "resolve-inventory"), "--output", str(output)],
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Resolved inventory from github", result.stdout)
            self.assertEqual(output.read_text(), "[app]\nvm-a ansible_host=192.0.2.10\n")

    def test_resolve_inventory_fails_when_no_source_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env.pop("LDK_INVENTORY", None)
            result = self.run_cmd(
                [
                    str(ROOT / "bin" / "resolve-inventory"),
                    "--output",
                    str(Path(tmpdir) / "inventory.ini"),
                ],
                env=env,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("No inventory source resolved", result.stderr)

    def test_check_workflow_version_reports_mismatch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow_dir = Path(tmpdir) / ".github" / "workflows"
            workflow_dir.mkdir(parents=True)
            (workflow_dir / "deploy.yml").write_text(
                "jobs:\n"
                "  deploy:\n"
                "    uses: demo/laravel-deploy-kit/.github/workflows/laravel-vm-deploy.yml@v0\n",
                encoding="utf-8",
            )

            result = self.run_cmd(
                [
                    str(ROOT / "bin" / "check-workflow-version"),
                    "--path",
                    tmpdir,
                    "--expected-ref",
                    "v1",
                ]
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("OUTDATED", result.stdout)

    def test_check_workflow_version_accepts_expected_ref(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow_dir = Path(tmpdir) / ".github" / "workflows"
            workflow_dir.mkdir(parents=True)
            (workflow_dir / "deploy.yml").write_text(
                "jobs:\n"
                "  deploy:\n"
                "    uses: demo/laravel-deploy-kit/.github/workflows/laravel-vm-deploy.yml@v1\n",
                encoding="utf-8",
            )

            result = self.run_cmd(
                [
                    str(ROOT / "bin" / "check-workflow-version"),
                    "--path",
                    tmpdir,
                    "--expected-ref",
                    "v1",
                ]
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
