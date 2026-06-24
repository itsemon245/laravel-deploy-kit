# App Secrets Vs Deploy Secrets

Keep runtime and control-plane credentials separate.

## App Runtime Secrets

These may be rendered into Laravel `.env`:

- `APP_KEY`
- `DB_HOST`
- `DB_DATABASE`
- `DB_USERNAME`
- `DB_PASSWORD`
- `REDIS_HOST`
- `REDIS_PASSWORD`
- mail provider credentials,
- object storage credentials,
- app-used API keys.

## Deployment Secrets

These must not be rendered into Laravel `.env`:

- SSH private keys,
- GitHub deploy keys or repo tokens,
- Infisical machine identity credentials,
- SOPS age private keys,
- private Ansible inventory when sensitive,
- DB or Redis bootstrap admin credentials.

## Rendering Rule

Default render configuration should include only:

```yaml
include_classes:
  - app
```

