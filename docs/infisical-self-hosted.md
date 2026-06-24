# Infisical Self-Hosted

Use self-hosted Infisical when the team needs to operate the secret service inside its own environment.

## Recommended Shape

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

