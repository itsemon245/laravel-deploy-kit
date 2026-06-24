from __future__ import annotations

import copy
from typing import Any, Mapping


def _deep_merge(base: Any, override: Any) -> Any:
    if isinstance(base, Mapping) and isinstance(override, Mapping):
        merged = {key: copy.deepcopy(value) for key, value in base.items()}
        for key, value in override.items():
            if key in merged:
                merged[key] = _deep_merge(merged[key], value)
            else:
                merged[key] = copy.deepcopy(value)
        return merged

    return copy.deepcopy(override)


def ldk_apply_manifest_environment(
    manifest: Mapping[str, Any],
    app_env: str,
    file_override: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    base = copy.deepcopy(dict(manifest or {}))
    inline_overrides = base.get("environments", {})
    inline_override = {}
    if isinstance(inline_overrides, Mapping):
        inline_override = inline_overrides.get(app_env, {}) or {}

    resolved = _deep_merge(base, inline_override)
    if file_override:
        resolved = _deep_merge(resolved, file_override)
    resolved.pop("environments", None)
    return resolved


class FilterModule:
    def filters(self) -> dict[str, Any]:
        return {
            "ldk_apply_manifest_environment": ldk_apply_manifest_environment,
        }

