# App Setup

Use this in the private Laravel app repo. Keep real secrets, hostnames, IPs, and topology out of this public kit.

## 1. Copy The App Workflow

Copy:

```text
templates/app-workflows/deploy.yml
```

to the app repo:

```text
.github/workflows/deploy.yml
```

Set the real kit repository owner and pin `uses:` to a release tag.

Example:

```yaml
uses: your-github-org/laravel-deploy-kit/.github/workflows/laravel-vm-deploy.yml@v0.1
```

## 2. Copy The Manifest

Copy:

```text
templates/manifests/laravel-compose.yml
```

to the app repo:

```text
deploy/manifest.yml
```

Replace fake app names, paths, Compose service names, health checks, and provider source references. Keep staging and production differences under `environments.staging` and `environments.production` unless they are too different to read clearly.

Manifest reference: [docs/manifest.md](manifest.md).

## 3. Create GitHub Environments

Create one GitHub environment per deploy target. The default workflow uses the branch name as `app_env`, so the normal names are:

- `staging`
- `production`

The reusable workflow reads GitHub environment secrets from the environment matching `app_env`.

## 4. Put Values In The Right Place

| Place | Put here | Do not put here |
| --- | --- | --- |
| GitHub environment secrets | Workflow/control-plane credentials: SSH key, host keys, provider token, optional inventory | Laravel runtime `.env` values, unless temporarily migrating |
| `deploy/manifest.yml` | Non-secret deploy contract: app path, git ref, Compose files, services, health check, provider sources | Secret values, private keys, tokens |
| Secret provider | Laravel runtime keys and classified app/deploy/db/redis/monitoring values | GitHub runner SSH private key, provider auth token |
| Workflow `with:` | `app_env`, `manifest_path`, optional inventory source inputs | Secret values |

Only `app` class secrets are rendered into Laravel `.env` by default. Keep deploy/control-plane secrets out of `.env`.

Details: [App Secrets Vs Deploy Secrets](app-vs-deploy-secrets.md).

## 5. Add Required GitHub Environment Secrets

Set these in each GitHub environment that can deploy.

| Secret | Required when |
| --- | --- |
| `LDK_SSH_PRIVATE_KEY` | The runner needs SSH access to the VM |
| `LDK_KNOWN_HOSTS` | Recommended for production host key pinning |
| `LDK_INVENTORY` | Inventory is stored directly in GitHub |
| `SOPS_AGE_KEY` | App secrets or inventory are decrypted from SOPS |
| `INFISICAL_TOKEN` | App secrets or inventory are read from Infisical |

`LDK_SSH_PRIVATE_KEY` is the multiline private key used by the workflow to SSH into target VMs.

## 6. Choose One App Secret Provider

Pick one provider for app runtime secrets and configure the manifest `secrets` block for it.

| Provider | Use when | Details |
| --- | --- | --- |
| SOPS + age | You want encrypted files in the app repo and no hosted secret service | [SOPS + Age](sops-age.md) |
| Infisical Cloud | You want managed secret storage | [Infisical Cloud](infisical-cloud.md) |
| Infisical self-hosted | You operate Infisical yourself | [Infisical Self-Hosted](infisical-self-hosted.md) |

Do not mix providers until one path works end to end.

## 7. Choose One Inventory Source

Inventory is resolved in this order:

1. `LDK_INVENTORY` GitHub environment secret.
2. SOPS-encrypted inventory file passed as `inventory_sops_path`.
3. Infisical inventory secret passed through the `inventory_infisical_*` inputs.

For the first deploy, use `LDK_INVENTORY` unless you already have SOPS or Infisical ready.

Minimal single-VM staging inventory:

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

If using SOPS inventory, remove `LDK_INVENTORY` and add:

```yaml
with:
  app_env: ${{ github.ref_name }}
  manifest_path: deploy/manifest.yml
  inventory_sops_path: deploy/inventories/${{ github.ref_name }}.ini.sops
```

The SOPS age key in `SOPS_AGE_KEY` must decrypt both the app secret files and the encrypted inventory file.

If using Infisical inventory, remove `LDK_INVENTORY` and add:

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

## 8. Deploy Staging First

Before running the workflow:

- `.env`, private keys, tokens, and plaintext production inventories are ignored by git.
- `deploy/manifest.yml` validates for `staging`.
- The selected provider has the app runtime keys the manifest references.
- The VM already allows SSH from the runner.
- The health check works from the VM.

Local manifest validation:

```bash
path/to/laravel-deploy-kit/bin/validate-manifest deploy/manifest.yml staging
```

Push the `staging` branch or run the workflow manually for `staging`. After staging works, repeat the same checklist for `production`.
