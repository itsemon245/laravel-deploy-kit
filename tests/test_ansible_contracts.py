import pathlib
import unittest

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"


def load_yaml(path):
    return yaml.safe_load(path.read_text())


def role_name(entry):
    if isinstance(entry, str):
        return entry
    return entry["role"]


class AnsibleContractTest(unittest.TestCase):
    def test_playbook_roles_exist_and_have_tasks(self):
        for playbook in (ANSIBLE / "playbooks").glob("*.yml"):
            plays = load_yaml(playbook)
            for play in plays:
                for role_entry in play.get("roles", []):
                    name = role_name(role_entry)
                    role_dir = ANSIBLE / "roles" / name
                    with self.subTest(playbook=playbook.name, role=name):
                        self.assertTrue(role_dir.is_dir(), f"Missing role dir: {role_dir}")
                        self.assertTrue(
                            (role_dir / "tasks" / "main.yml").is_file(),
                            f"Missing tasks/main.yml for role: {name}",
                        )

    def test_deploy_role_order_keeps_one_time_services_before_rollout(self):
        playbook = load_yaml(ANSIBLE / "playbooks" / "laravel-vm-deploy.yml")
        roles = [role_name(entry) for entry in playbook[0]["roles"]]

        self.assertLess(
            roles.index("compose_one_time_services"),
            roles.index("laravel_remote_build"),
        )
        self.assertLess(
            roles.index("compose_one_time_services"),
            roles.index("compose_rollout"),
        )

    def test_secret_roles_use_no_log(self):
        for role in ["secrets_sops", "secrets_infisical", "secrets_merge", "render_env_file"]:
            path = ANSIBLE / "roles" / role / "tasks" / "main.yml"
            content = path.read_text()
            with self.subTest(role=role):
                self.assertIn("no_log: true", content)

    def test_host_common_documents_ubuntu_24_baseline(self):
        defaults = load_yaml(ANSIBLE / "roles" / "host_common" / "defaults" / "main.yml")

        self.assertEqual(defaults["ldk_supported_distribution"], "Ubuntu")
        self.assertEqual(str(defaults["ldk_min_supported_distribution_version"]), "24.04")

    def test_docker_engine_uses_ubuntu_compose_v2_package(self):
        defaults = load_yaml(ANSIBLE / "roles" / "docker_engine" / "defaults" / "main.yml")

        self.assertIn("docker.io", defaults["ldk_docker_packages"])
        self.assertIn("docker-compose-v2", defaults["ldk_docker_packages"])

    def test_ubuntu24_integration_inventory_exists(self):
        inventory = (
            ROOT / "tests" / "integration" / "ubuntu24" / "inventory.ini"
        ).read_text()

        self.assertIn("ubuntu-app", inventory)
        self.assertIn("ansible_user=root", inventory)


if __name__ == "__main__":
    unittest.main()
