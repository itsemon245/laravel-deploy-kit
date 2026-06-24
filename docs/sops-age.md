# SOPS + Age

SOPS + age is the simplest provider to pilot because it does not require a hosted secret service.

## Key Handling

Generate age keys outside this public repository:

```bash
age-keygen -o keys/demo.agekey
```

Commit only public recipients in `.sops.yaml`. Never commit the age private key.

## Example `.sops.yaml`

```yaml
creation_rules:
  - path_regex: deploy/secrets/.*\.sops\.(env|ya?ml)$
    age: age1replacewithpublicrecipient0000000000000000000000000
```

The recipient above is fake and must be replaced in a private app repo.

## Editing Secrets

```bash
sops deploy/secrets/staging.app.sops.env
```

SOPS writes encrypted content back to the same file. Commit only encrypted files.

## CI Or Deploy Decryption

Provide the age private key through one trusted path:

- `SOPS_AGE_KEY` in a GitHub environment secret,
- a protected self-hosted runner,
- a secure deployment machine for manual runs.

