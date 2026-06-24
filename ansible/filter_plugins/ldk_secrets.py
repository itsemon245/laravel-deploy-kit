from __future__ import annotations

import ast
import json
import re
from typing import Any, Iterable, Mapping

try:
    from ansible.errors import AnsibleFilterError
except Exception:  # pragma: no cover - allows local import without Ansible
    AnsibleFilterError = ValueError


KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _fail(message: str) -> None:
    raise AnsibleFilterError(message)


def ldk_parse_dotenv(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line_number, raw_line in enumerate(str(text).splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        if "=" not in line:
            _fail(f"Invalid dotenv line {line_number}: missing '='")

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not KEY_RE.match(key):
            _fail(f"Invalid dotenv key on line {line_number}: {key}")

        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            try:
                value = ast.literal_eval(value)
            except (SyntaxError, ValueError):
                value = value[1:-1]

        result[key] = str(value)
    return result


def ldk_normalize_infisical_json(value: Any) -> dict[str, Any]:
    data = json.loads(value) if isinstance(value, str) else value

    if isinstance(data, Mapping):
        if isinstance(data.get("secrets"), list):
            data = data["secrets"]
        else:
            return dict(data)

    if isinstance(data, list):
        result: dict[str, Any] = {}
        for item in data:
            if not isinstance(item, Mapping):
                _fail("Infisical JSON list entries must be objects")
            key = item.get("key") or item.get("secretKey") or item.get("Key")
            secret_value = (
                item.get("value")
                if "value" in item
                else item.get("secretValue")
                if "secretValue" in item
                else item.get("Value")
            )
            if not key:
                _fail("Infisical JSON secret entry is missing a key")
            result[str(key)] = secret_value
        return result

    _fail("Infisical JSON must be an object or list of secret entries")


def ldk_select_secret_classes(
    resolved_secrets: Mapping[str, Mapping[str, Any]], classes: Iterable[str]
) -> dict[str, Any]:
    selected: dict[str, Any] = {}
    for class_name in classes:
        class_values = resolved_secrets.get(class_name, {})
        if not isinstance(class_values, Mapping):
            _fail(f"Secret class '{class_name}' must be a mapping")
        selected.update(class_values)
    return selected


def ldk_normalize_class_payload(value: Any, class_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f"Secret payload for class '{class_name}' must be a mapping")

    if (
        len(value) == 1
        and class_name in value
        and isinstance(value[class_name], Mapping)
    ):
        return dict(value[class_name])

    return dict(value)


def ldk_render_dotenv(values: Mapping[str, Any]) -> str:
    if not isinstance(values, Mapping):
        _fail("Dotenv values must be a mapping")

    lines: list[str] = []
    for key in sorted(values):
        if not KEY_RE.match(str(key)):
            _fail(f"Invalid dotenv key: {key}")
        value = values[key]
        rendered = "" if value is None else str(value)
        lines.append(f"{key}={json.dumps(rendered)}")
    return "\n".join(lines) + ("\n" if lines else "")


class FilterModule:
    def filters(self) -> dict[str, Any]:
        return {
            "ldk_parse_dotenv": ldk_parse_dotenv,
            "ldk_normalize_infisical_json": ldk_normalize_infisical_json,
            "ldk_normalize_class_payload": ldk_normalize_class_payload,
            "ldk_select_secret_classes": ldk_select_secret_classes,
            "ldk_render_dotenv": ldk_render_dotenv,
        }
