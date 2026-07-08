# Infisical Cloud

Use Infisical Cloud when app runtime secrets should live in managed secret storage instead of encrypted files in the app repo.

## What Goes Where

| Place | Value |
| --- | --- |
| GitHub environment secret | `INFISICAL_TOKEN`, the token used by the workflow |
| Infisical | App runtime keys and optional deploy/db/redis/monitoring class values |
| Manifest | `secrets.provider: infisical_cloud` and one source per Infisical path |

Do not store the full Laravel `.env` as one GitHub secret when a provider is available.

## 1. Create Paths

Use separate folders or paths for each class:

```text
/app
/deploy
/db
/redis
/monitoring
```

Use fake names in public examples, such as `demo-shared` and `demo-laravel`.

## 2. Add App Runtime Keys

Put Laravel runtime keys under an app path such as `/app`:

```text
APP_KEY
DB_HOST
DB_DATABASE
DB_USERNAME
DB_PASSWORD
REDIS_HOST
REDIS_PASSWORD
```

Only sources marked `class: app` should be rendered into Laravel `.env`.

## 3. Configure Authentication

The current reusable workflows read `INFISICAL_TOKEN` from the matching GitHub environment. Put a token there that can read the paths referenced by the manifest.

Keep any machine identity client secret or token out of the manifest and out of the provider paths rendered into Laravel `.env`.

## 4. Configure The Manifest

```yaml
secrets:
  provider: infisical_cloud
  sources:
    - name: app_runtime
      project_id: demo-laravel
      env_slug: "{{ app_env }}"
      path: /app
      class: app
  merge:
    override_order:
      - app_runtime
  render:
    app_env_file:
      enabled: true
      target: .env
      mode: "0600"
      include_classes:
        - app
```

## Updating A Secret

1. Open the Infisical project.
2. Select the target environment.
3. Update the key in the correct path.
4. Run a secret refresh workflow or a normal deploy.
5. Confirm the app `.env` only receives `app` class keys.
