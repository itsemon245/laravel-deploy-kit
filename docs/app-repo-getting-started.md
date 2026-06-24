# App Repo Getting Started

Use these steps in a private app repository. Keep real values out of this public kit.

## 1. Add The Tiny Workflow

Copy `templates/app-workflows/deploy.yml` to:

```text
.github/workflows/deploy.yml
```

Replace the fake kit owner with the actual repository owner and pin to a release tag.

## 2. Add A Manifest

Copy `templates/manifests/laravel-compose.yml` to:

```text
deploy/manifest.yml
```

Set the real app name, app directory, Compose files, health URL, and secret provider sources in the private app repo. Put small staging/production differences under `environments.staging` and `environments.production`.

See `docs/manifest.md` for the complete manifest field reference.

## 3. Configure GitHub Environments

Create GitHub environments whose names exactly match the `app_env` values passed to the reusable workflow. The default templates use:

- `staging`
- `production`

The deploy-kit reusable jobs bind to `environment: ${{ inputs.app_env }}`, so environment secrets are read from the matching app repo environment.

Use GitHub environment secrets for deployment/control-plane credentials only. Do not store the full Laravel `.env` blob unless it is a temporary migration path.

No GitHub environment variables are required by default. Use secrets unless this doc explicitly says a value belongs in workflow `with:`.

### Required Environment Secrets

Set these in each GitHub environment that can deploy.

| Secret key | Required when | Example value |
| --- | --- | --- |
| `LDK_SSH_PRIVATE_KEY` | Always, unless the runner already has SSH access | See multiline example below |
| `LDK_INVENTORY` | When inventory is stored directly in GitHub | See inventory examples below |
| `LDK_KNOWN_HOSTS` | Optional, recommended for production | `production-app-1.internal.invalid ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFAKE...` |
| `SOPS_AGE_KEY` | When `secrets.provider: sops_age`, or when inventory comes from a SOPS file | `AGE-SECRET-KEY-1FAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKE` |
| `INFISICAL_TOKEN` | When `secrets.provider` is Infisical, or when inventory comes from Infisical | `st.fake-infisical-machine-token` |

`LDK_SSH_PRIVATE_KEY` is a multiline GitHub secret:

```text
-----BEGIN OPENSSH PRIVATE KEY-----
fake-private-key-content-for-docs-only
-----END OPENSSH PRIVATE KEY-----
```

### Minimal SOPS Setup

Use this when app runtime secrets are SOPS-encrypted files in the private app repo and inventory is stored directly in GitHub.

Environment: `staging`

| Secret key | Example value |
| --- | --- |
| `LDK_SSH_PRIVATE_KEY` | multiline deploy SSH private key |
| `LDK_INVENTORY` | staging inventory example below |
| `SOPS_AGE_KEY` | `AGE-SECRET-KEY-1FAKESTAGING...` |
| `LDK_KNOWN_HOSTS` | optional staging host key |

`LDK_INVENTORY` for single-VM staging:

```ini
[app]
staging-app.internal.invalid ansible_host=192.0.2.10 ansible_user=deploy ansible_port=22

[postgres]
staging-app.internal.invalid

[redis]
staging-app.internal.invalid

[all:vars]
app_env=staging
ansible_python_interpreter=/usr/bin/python3
```

Environment: `production`

| Secret key | Example value |
| --- | --- |
| `LDK_SSH_PRIVATE_KEY` | multiline deploy SSH private key |
| `LDK_INVENTORY` | production inventory example below |
| `SOPS_AGE_KEY` | `AGE-SECRET-KEY-1FAKEPRODUCTION...` |
| `LDK_KNOWN_HOSTS` | one known-hosts line per production VM |

`LDK_INVENTORY` for separate production VMs:

```ini
[app]
production-app-1.internal.invalid ansible_host=192.0.2.21 ansible_user=deploy ansible_port=22
production-app-2.internal.invalid ansible_host=192.0.2.22 ansible_user=deploy ansible_port=22

[postgres]
production-db-1.internal.invalid ansible_host=192.0.2.30 ansible_user=deploy ansible_port=22

[redis]
production-redis-1.internal.invalid ansible_host=192.0.2.40 ansible_user=deploy ansible_port=22

[all:vars]
app_env=production
ansible_python_interpreter=/usr/bin/python3
```

### Minimal Infisical Setup

Use this when app runtime secrets come from Infisical and inventory is stored directly in GitHub.

Environment: `staging`

| Secret key | Example value |
| --- | --- |
| `LDK_SSH_PRIVATE_KEY` | multiline deploy SSH private key |
| `LDK_INVENTORY` | staging inventory text |
| `INFISICAL_TOKEN` | `st.fake-staging-infisical-token` |
| `LDK_KNOWN_HOSTS` | optional staging host key |

Environment: `production`

| Secret key | Example value |
| --- | --- |
| `LDK_SSH_PRIVATE_KEY` | multiline deploy SSH private key |
| `LDK_INVENTORY` | production inventory text |
| `INFISICAL_TOKEN` | `st.fake-production-infisical-token` |
| `LDK_KNOWN_HOSTS` | production host keys |

For Infisical Cloud, leave the manifest `secrets.url` empty or use the provider default. For self-hosted Infisical, set the manifest URL, for example:

```yaml
secrets:
  provider: infisical_self_hosted
  url: https://secrets.internal.invalid
```

### Inventory From SOPS Instead Of GitHub

If inventory should not be stored as `LDK_INVENTORY`, commit an encrypted inventory file such as:

```text
deploy/inventories/staging.ini.sops
deploy/inventories/production.ini.sops
```

Then remove `LDK_INVENTORY` and add this to the app workflow `with:` block:

```yaml
with:
  app_env: ${{ github.ref_name }}
  manifest_path: deploy/manifest.yml
  inventory_sops_path: deploy/inventories/${{ github.ref_name }}.ini.sops
```

Required environment secrets for this path:

| Secret key | Example value |
| --- | --- |
| `LDK_SSH_PRIVATE_KEY` | multiline deploy SSH private key |
| `SOPS_AGE_KEY` | age private key that can decrypt the inventory and app secret files |
| `LDK_KNOWN_HOSTS` | optional host keys |

### Inventory From Infisical Instead Of GitHub

If inventory should come from Infisical, store a secret like this in Infisical:

| Infisical field | Example value |
| --- | --- |
| Project ID | `demo-laravel` |
| Environment | `staging` or `production` |
| Path | `/deploy` |
| Secret key | `ANSIBLE_INVENTORY` |
| Secret value | inventory text in INI format |

Then remove `LDK_INVENTORY` and add this to the app workflow `with:` block:

```yaml
with:
  app_env: ${{ github.ref_name }}
  manifest_path: deploy/manifest.yml
  inventory_infisical_project_id: demo-laravel
  inventory_infisical_env: ${{ github.ref_name }}
  inventory_infisical_path: /deploy
  inventory_infisical_key: ANSIBLE_INVENTORY
```

For self-hosted Infisical inventory, also set:

```yaml
  inventory_infisical_url: https://secrets.internal.invalid
```

Required environment secrets for this path:

| Secret key | Example value |
| --- | --- |
| `LDK_SSH_PRIVATE_KEY` | multiline deploy SSH private key |
| `INFISICAL_TOKEN` | machine identity token that can read `/deploy/ANSIBLE_INVENTORY` |
| `LDK_KNOWN_HOSTS` | optional host keys |

Inventory fallback order is always:

1. `LDK_INVENTORY` GitHub environment secret.
2. `inventory_sops_path` file.
3. Infisical inventory inputs.

Do not set `LDK_INVENTORY` if you want SOPS or Infisical inventory to be used.

## 4. Choose One Secret Provider

Start with one:

- SOPS + age for a no-server path.
- Infisical Cloud for managed secret storage.
- Infisical self-hosted when the team must operate its own secret service.

## 5. First Staging Deploy

Before deploying:

- confirm the staging inventory is private or fake,
- validate the manifest,
- confirm `.env` is ignored,
- confirm health checks do not require public access,
- deploy the staging branch first.
