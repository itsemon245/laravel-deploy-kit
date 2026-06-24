# Architecture

Laravel Deploy Kit separates public deployment machinery from private app configuration.

## Split Of Responsibility

The public kit owns generic conventions:

- app workflow templates,
- manifest examples,
- manifest reference documentation,
- layered base manifest plus environment override support,
- Ansible role contracts,
- VM-side build and rollout documentation,
- secret-provider interface documentation,
- service configuration templates.

The private app repository owns project-specific values:

- branch triggers,
- real inventory,
- real manifest values,
- app Dockerfile and Compose files,
- GitHub environments,
- encrypted SOPS files or provider paths,
- production approval rules.

## Deployment Shape

```text
app repo push
  -> tiny app workflow
  -> reusable deploy-kit workflow
  -> manifest validation
  -> temporary inventory resolution
  -> Ansible
  -> VM git sync
  -> VM-side Docker build
  -> Compose rollout
```

The default build strategy is `per_vm`. Each app VM builds locally and keeps its Docker build cache. CI-built images and private-LAN image distribution are future optional modes, not part of this skeleton.

PostgreSQL and Redis provisioning are separate one-time workflows. Regular production backend deploys target app VMs only.

## Secret Boundary

Secret providers normalize values into classes such as `app`, `deploy`, `db`, `redis`, and `monitoring`.

Only `app` class values should be rendered into the Laravel `.env` file. Deployment/control-plane values are transient workflow or Ansible inputs and must not be written to application runtime files.

Private inventory is resolved in fallback order: GitHub environment secret, SOPS, then Infisical.
