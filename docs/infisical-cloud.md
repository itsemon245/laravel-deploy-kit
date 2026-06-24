# Infisical Cloud

Infisical Cloud can store app runtime and deployment/control-plane secrets without committing plaintext to app repositories.

## Suggested Layout

Use separate folders or paths for each class:

```text
/app
/deploy
/db
/redis
/monitoring
```

Use fake names in public examples, such as `demo-shared` and `demo-laravel`.

## Authentication

Preferred:

- GitHub OIDC to an Infisical identity.

Fallback:

- machine identity client ID and client secret stored in GitHub environment secrets.

Do not store the full app `.env` as one GitHub secret when a provider is available.

## Updating A Secret

1. Open the Infisical project.
2. Select the target environment.
3. Update the key in the correct path.
4. Run a secret refresh workflow or a normal deploy.
5. Confirm the app `.env` only receives `app` class keys.

