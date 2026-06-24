# Kit Repo Development

This repository must stay generic enough to publish.

## Development Rules

- Use fake values in docs, examples, tests, and templates.
- Keep app-specific topology in private app repos.
- Keep deployment behavior backward compatible within a major release.
- Prefer additive manifest keys over breaking existing keys.
- Mark experimental keys clearly before documenting them as stable.

## Release Versioning

Use semantic version tags:

```text
v1.0.0
v1.1.0
v2.0.0
```

App repos may pin to a major tag such as `@v1` or an exact version such as `@v1.1.0`.

## Testing Expectations

Use layered checks before any real staging or production VM test:

1. Offline required checks:

```bash
make test
```

2. Full local verification with optional tools when installed:

```bash
make verify
```

3. Strict verification, failing when optional tools are missing:

```bash
LDK_REQUIRE_OPTIONAL_TOOLS=true bin/verify
```

4. Isolated container verification:

```bash
make container-test
```

5. Docker-based Ubuntu 24.04 deploy smoke test:

```bash
make integration-docker
```

This starts an Ubuntu 24.04 SSH target container, seeds a tiny Git app repo on it, mounts the host Docker socket into the target, and runs the deploy playbook through Ansible from a control container. It is intentionally still a local simulation, not a replacement for a private staging VM.

The smoke test covers the deploy path after SSH access and Docker/Compose are present: manifest layering, SOPS-style dotenv secret normalization, `.env` rendering, repo checkout, Compose preflight, one-time services, VM-side build, rollout, and command health checks. It does not fully emulate GitHub environment approvals, real network firewalls, production load balancers, or a long-lived VM's disk/cache history.

6. Private staging VM smoke test outside this public repo.

The optional tool layer covers YAML linting, Ansible linting, Ansible syntax checks, GitHub Actions workflow linting with `actionlint`, ShellCheck, and Docker Compose config validation.

`make dev-install` creates `.venv` and installs Python-based dev tools. It uses `uv` when available and falls back to `pip`. The production CLI scripts themselves use the Python standard library except for Ansible filter execution inside Ansible; the development dependencies are for tests and linting.

Ansible does not install its own Python package dependencies. The workflow/container environments install `ansible-core`, `ansible-lint`, and `yamllint` from `requirements-dev.txt`; app workflows install Ansible before running playbooks.
