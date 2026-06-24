# SOPS Age Key Policy Example

This is a policy template for a private app repo. Do not store age private keys in this public kit.

## Rules

- Commit only encrypted `.sops.env`, `.sops.yml`, or `.sops.yaml` files.
- Keep age private keys in GitHub environment secrets, a protected runner, or a secure deployment machine.
- Rotate recipients when a maintainer leaves the project.
- Keep staging and production recipients separate when access differs.
- Do not paste decrypted values into issues, pull requests, workflow logs, or chat.

## Suggested Private Files

```text
deploy/secrets/staging.app.sops.env
deploy/secrets/production.app.sops.env
deploy/secrets/staging.deploy.sops.yml
deploy/secrets/production.deploy.sops.yml
```

