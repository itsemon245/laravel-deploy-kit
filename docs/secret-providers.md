# Secret Providers

Secret providers fetch raw values and normalize them into one internal shape. Provider roles should not decide what gets rendered into `.env`; rendering is handled by the env-file layer.

## Normalized Shape

```yaml
resolved_secrets:
  app:
    APP_KEY: "fake-value"
  deploy:
    GIT_DEPLOY_TOKEN: "fake-value"
  db:
    POSTGRES_PASSWORD: "fake-value"
  redis:
    REDIS_PASSWORD: "fake-value"
```

Values above are fake shape examples. Implementations must avoid logging secret values.

## Source Classes

Supported classes:

- `app`
- `deploy`
- `db`
- `redis`
- `monitoring`

Only `app` is rendered into Laravel `.env` by default.

## Merge Rules

Sources are merged in the order declared by `secrets.merge.override_order`. Later sources override earlier sources. Duplicate detection can be added as validation when teams want stricter behavior.

