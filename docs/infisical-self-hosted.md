# Infisical Self-Hosted

Use self-hosted Infisical when app runtime secrets should live in Infisical and the team operates the Infisical service itself.

Follow the same app setup as [Infisical Cloud](infisical-cloud.md), with these differences:

- set `secrets.provider: infisical_self_hosted`,
- set `secrets.url` to the self-hosted base URL,
- set `inventory_infisical_url` too if inventory is read from self-hosted Infisical.

```yaml
secrets:
  provider: infisical_self_hosted
  url: https://secrets.internal.invalid
  sources:
    - name: app_runtime
      project_id: demo-laravel
      env_slug: "{{ app_env }}"
      path: /app
      class: app
```

## Operate The Service

- Use a dedicated hostname such as `secrets.internal.invalid` in examples.
- Terminate TLS with a managed certificate in the private deployment.
- Back up the Infisical database and encryption material together.
- Restrict admin access and machine identities by environment.
- Monitor failed auth attempts, service health, and database backups.

## Upgrade Considerations

- Test upgrades against a staging Infisical instance first.
- Export or snapshot configuration before upgrades.
- Keep rollback instructions near the service runbook.

## Deploy Kit Contract

The deploy kit should only need:

- base URL,
- auth method,
- project or workspace identifier,
- environment slug,
- path,
- class.

It should not depend on cross-project import behavior.
