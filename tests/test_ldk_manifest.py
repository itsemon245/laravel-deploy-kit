import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "ansible" / "filter_plugins" / "ldk_manifest.py"


def load_plugin():
    spec = importlib.util.spec_from_file_location("ldk_manifest", PLUGIN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ldk = load_plugin()


class ManifestFilterTest(unittest.TestCase):
    def test_applies_inline_environment_override(self):
        resolved = ldk.ldk_apply_manifest_environment(
            {
                "schema_version": 1,
                "compose": {"files": ["base.yml"], "app_services": ["web"]},
                "cleanup": {"policy": "disk_pressure_only", "min_free_kb": 10},
                "environments": {
                    "production": {
                        "compose": {"app_services": ["web", "queues"]},
                        "cleanup": {"min_free_kb": 20},
                    }
                },
            },
            "production",
        )

        self.assertNotIn("environments", resolved)
        self.assertEqual(resolved["compose"]["files"], ["base.yml"])
        self.assertEqual(resolved["compose"]["app_services"], ["web", "queues"])
        self.assertEqual(resolved["cleanup"]["policy"], "disk_pressure_only")
        self.assertEqual(resolved["cleanup"]["min_free_kb"], 20)

    def test_file_override_wins_after_inline_override(self):
        resolved = ldk.ldk_apply_manifest_environment(
            {
                "health": {"retries": 6, "delay": 5},
                "environments": {"production": {"health": {"retries": 10}}},
            },
            "production",
            {"health": {"delay": 9}},
        )

        self.assertEqual(resolved["health"], {"retries": 10, "delay": 9})


if __name__ == "__main__":
    unittest.main()
