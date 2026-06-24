import json
import pathlib
import unittest

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]


class StaticFilesTest(unittest.TestCase):
    def test_json_schema_parses(self):
        schema = json.loads((ROOT / "schemas" / "manifest.schema.json").read_text())

        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)

    def test_yaml_files_parse(self):
        yaml_paths = [
            path
            for path in ROOT.rglob("*")
            if path.suffix in {".yml", ".yaml"} and ".git" not in path.parts
        ]

        self.assertGreater(len(yaml_paths), 0)
        for path in yaml_paths:
            with self.subTest(path=path.relative_to(ROOT)):
                list(yaml.safe_load_all(path.read_text()))

    def test_example_manifest_uses_supported_provider_alias(self):
        manifest = yaml.safe_load(
            (ROOT / "examples" / "app-repo" / "deploy" / "manifest.yml").read_text()
        )

        self.assertIn(
            manifest["secrets"]["provider"],
            {"sops", "sops_age", "infisical", "infisical_cloud", "infisical_self_hosted"},
        )

    def test_integration_manifest_targets_ubuntu24_smoke_shape(self):
        manifest = yaml.safe_load(
            (ROOT / "tests" / "integration" / "ubuntu24" / "manifest.yml").read_text()
        )

        self.assertEqual(manifest["app"]["app_dir"], "/srv/ldk-integration/current")
        self.assertEqual(manifest["health"]["type"], "command")
        self.assertEqual(
            manifest["environments"]["staging"]["compose"]["one_time_services"],
            ["redis"],
        )

    def test_ubuntu24_integration_target_installs_compose_v2(self):
        dockerfile = (
            ROOT / "tests" / "integration" / "ubuntu24" / "Dockerfile.target"
        ).read_text()

        self.assertIn("docker.io", dockerfile)
        self.assertIn("docker-compose-v2", dockerfile)


if __name__ == "__main__":
    unittest.main()
