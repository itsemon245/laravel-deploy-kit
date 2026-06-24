import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "ansible" / "filter_plugins" / "ldk_secrets.py"


def load_plugin():
    spec = importlib.util.spec_from_file_location("ldk_secrets", PLUGIN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ldk = load_plugin()


class SecretFiltersTest(unittest.TestCase):
    def test_parse_dotenv_handles_comments_export_and_quotes(self):
        parsed = ldk.ldk_parse_dotenv(
            """
            # fake example
            APP_NAME="Demo App"
            export DB_PASSWORD='fake password'
            REDIS_PASSWORD=
            """
        )

        self.assertEqual(
            parsed,
            {
                "APP_NAME": "Demo App",
                "DB_PASSWORD": "fake password",
                "REDIS_PASSWORD": "",
            },
        )

    def test_normalize_infisical_accepts_flat_objects(self):
        normalized = ldk.ldk_normalize_infisical_json('{"APP_KEY": "fake"}')

        self.assertEqual(normalized, {"APP_KEY": "fake"})

    def test_normalize_infisical_accepts_secret_lists(self):
        normalized = ldk.ldk_normalize_infisical_json(
            json.dumps(
                {
                    "secrets": [
                        {"secretKey": "APP_KEY", "secretValue": "base"},
                        {"key": "DB_PASSWORD", "value": "fake"},
                    ]
                }
            )
        )

        self.assertEqual(normalized, {"APP_KEY": "base", "DB_PASSWORD": "fake"})

    def test_select_classes_and_render_dotenv(self):
        values = ldk.ldk_select_secret_classes(
            {
                "app": {"APP_KEY": "base", "DB_PASSWORD": "fake"},
                "deploy": {"APP_KEY": "override", "GIT_TOKEN": "fake"},
            },
            ["app", "deploy"],
        )

        self.assertEqual(values["APP_KEY"], "override")
        self.assertEqual(
            ldk.ldk_render_dotenv({"APP_KEY": "fake value"}), 'APP_KEY="fake value"\n'
        )

    def test_normalize_class_payload_unwraps_class_wrapped_yaml(self):
        self.assertEqual(
            ldk.ldk_normalize_class_payload(
                {"deploy": {"git_deploy_token": "fake"}}, "deploy"
            ),
            {"git_deploy_token": "fake"},
        )


if __name__ == "__main__":
    unittest.main()
