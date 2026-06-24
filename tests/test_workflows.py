import pathlib
import unittest

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def load_workflow(name):
    data = yaml.safe_load((WORKFLOWS / name).read_text())
    # PyYAML 1.1 treats the GitHub Actions key "on" as boolean True.
    if True in data and "on" not in data:
        data["on"] = data[True]
    return data


class WorkflowContractTest(unittest.TestCase):
    reusable_workflows = {
        "laravel-vm-deploy.yml",
        "refresh-secrets.yml",
        "validate-app-manifest.yml",
        "vm-bootstrap.yml",
        "provision-postgres.yml",
        "provision-redis.yml",
    }

    def test_reusable_workflows_have_workflow_call(self):
        for name in self.reusable_workflows:
            with self.subTest(workflow=name):
                workflow = load_workflow(name)
                self.assertIn("workflow_call", workflow["on"])

    def test_deploy_workflow_resolves_inventory_and_optional_known_hosts(self):
        content = (WORKFLOWS / "laravel-vm-deploy.yml").read_text()

        self.assertIn("bin/resolve-inventory", content)
        self.assertIn("LDK_INVENTORY", content)
        self.assertIn("StrictHostKeyChecking=accept-new", content)
        self.assertIn("StrictHostKeyChecking=yes", content)

    def test_deploy_workflow_checks_out_app_and_kit(self):
        workflow = load_workflow("laravel-vm-deploy.yml")
        steps = workflow["jobs"]["deploy"]["steps"]
        checkout_paths = [
            step.get("with", {}).get("path")
            for step in steps
            if step.get("uses") == "actions/checkout@v4"
        ]

        self.assertIn("app", checkout_paths)
        self.assertIn("deploy-kit", checkout_paths)

    def test_secret_consuming_workflows_bind_to_app_environment(self):
        jobs_by_workflow = {
            "laravel-vm-deploy.yml": "deploy",
            "refresh-secrets.yml": "refresh",
            "vm-bootstrap.yml": "bootstrap",
            "provision-postgres.yml": "provision",
            "provision-redis.yml": "provision",
        }

        for workflow_name, job_name in jobs_by_workflow.items():
            with self.subTest(workflow=workflow_name):
                workflow = load_workflow(workflow_name)
                self.assertEqual(
                    workflow["jobs"][job_name]["environment"],
                    "${{ inputs.app_env }}",
                )

    def test_no_workflow_placeholder_text_remains(self):
        for path in WORKFLOWS.glob("*.yml"):
            with self.subTest(workflow=path.name):
                content = path.read_text()
                self.assertNotIn("intentionally not implemented", content)
                self.assertNotIn("Phase 5 placeholder", content)
                self.assertNotIn("Phase 6 placeholder", content)


if __name__ == "__main__":
    unittest.main()
