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

Create `staging` and `production` environments as needed. Store only deployment/control-plane credentials there, such as SSH access and provider bootstrap credentials.

Do not store a full Laravel `.env` blob unless using it as a temporary migration path.

For inventory, use this fallback order:

1. `LDK_INVENTORY` GitHub environment secret.
2. SOPS-encrypted inventory file.
3. Infisical inventory secret.

`LDK_KNOWN_HOSTS` is optional. Add it for stricter production SSH verification.

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
