# Changelog

All notable changes to Laravel Deploy Kit will be documented here.

## Unreleased

- Added public-kit documentation.
- Added safe example app workflow, manifests, SOPS example shapes, and fake inventories.
- Added starter templates for Compose, Nginx, PostgreSQL, Redis, Promtail, and SOPS age policy.
- Added manifest validation, deploy, secret-provider, and env rendering roles.
- Added reusable deploy, refresh-secrets, manifest validation, app VM bootstrap, and one-time DB/Redis provisioning workflows.
- Added inventory fallback resolution and workflow version checking CLI tools.
- Added layered manifest support for shared base manifests, inline environment overrides, and optional environment-specific manifest files.
- Added `compose.one_time_services` for first-deploy staging dependencies that should not be part of recurring app rollouts.
