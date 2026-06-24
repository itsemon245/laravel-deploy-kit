# Laravel Deploy Kit

Laravel Deploy Kit is a public, reusable deployment kit for Laravel applications running on Linux VMs with Docker Compose and Ansible.

The intended app flow is:

```text
app repo push -> tiny app workflow -> deploy-kit workflow -> Ansible -> VM-side Docker build -> Compose rollout
```

This repository keeps generic deployment conventions, examples, and templates. Each application repository keeps its own private manifest, GitHub environment settings, inventory, secrets provider configuration, Dockerfile, and Compose files.

## What This Kit Is For

- Laravel apps deployed to one or more Linux VMs.
- VM bootstrap targets Ubuntu 24.04 LTS or newer.
- VM-side Docker builds that preserve build cache.
- Staging on a single VM, optionally with local PostgreSQL and Redis.
- Production with app VMs separate from PostgreSQL and Redis VMs.
- App runtime secrets rendered into `.env` from a configured provider.
- Deployment/control-plane secrets kept separate from application secrets.

## What This Kit Does Not Do

- It does not require Kubernetes, Nomad, Swarm, or a private image registry.
- It does not store real secrets, real hostnames, real IPs, or private topology.
- It does not render deployment secrets into the Laravel `.env` file.
- It does not implement future build modes such as private-LAN image distribution.

## Current Scope

This repository currently contains the repo-side deploy-kit foundation:

- repo documentation and security guidance,
- safe example manifests,
- tiny app workflow examples,
- fake inventories,
- starter service templates,
- a manifest schema draft and local validator,
- reusable GitHub workflows for deploy, refresh-secrets, validation, app VM bootstrap, and separate DB/Redis provisioning,
- core VM deploy roles for repo sync, Compose preflight, VM-side build, migration, rollout, and health checks,
- SOPS/Infisical secret-provider normalization, merge, and `.env` rendering roles,
- app VM bootstrap roles and separate one-time PostgreSQL/Redis provisioning roles,
- a workflow version drift checker,
- local verification, strict container linting, and a Docker-based Ubuntu 24.04 deploy smoke test.

## Quick Start For An App Repo

1. Copy `templates/app-workflows/deploy.yml` to `.github/workflows/deploy.yml` in the app repo.
2. Copy `templates/manifests/laravel-compose.yml` to `deploy/manifest.yml`; see `docs/manifest.md` for the manifest contract and environment override rules.
3. Replace all fake `.invalid` hostnames, documentation IPs, fake project names, and placeholder paths in the app repo.
4. Configure GitHub environments with only deployment/control-plane credentials.
5. Configure one secret provider: SOPS + age, Infisical Cloud, or Infisical self-hosted.
6. Configure private inventory through GitHub environment secret, SOPS, or Infisical.
7. Keep `.env`, age private keys, SSH keys, tokens, and real inventories out of git.

## Repository Layout

```text
docs/       concise operating documentation
examples/   safe example app repo snippets and fake inventories
templates/  starter workflow, manifest, Compose, and service templates
```

All values in `examples/` and `templates/` are fake. Use `.invalid` hostnames, documentation IP ranges, and obvious placeholder secret values until the private app repository provides real values.

## Verification

Run the offline checks:

```bash
make test
```

Run the full local verifier. Optional tools are used when installed:

```bash
make verify
```

Run the isolated container checks:

```bash
make container-test
```

Run the local Ubuntu 24.04 deployment smoke test:

```bash
make integration-docker
```

## Safety Rules

- Never commit plaintext production secrets.
- Never commit real public or private IP addresses.
- Never commit internal hostnames or private domain names.
- Never commit age private keys, SSH private keys, API tokens, or database passwords.
- Only render app runtime secret classes into the Laravel `.env` file.
- Treat deployment secrets as transient workflow or Ansible inputs.
