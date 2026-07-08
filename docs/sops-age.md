# SOPS + Age

Use SOPS + age when app runtime secrets should be encrypted files in the private app repo. This path does not require a hosted secret service.

## What Goes Where

| Place | Value |
| --- | --- |
| GitHub environment secret | `SOPS_AGE_KEY`, the age private key used by the workflow |
| App repo | `.sops.yaml` and encrypted `deploy/secrets/*.sops.env` or `*.sops.yml` files |
| Manifest | `secrets.provider: sops_age` and one source per encrypted file |

Never commit the age private key or plaintext secret files.

## 1. Generate An Age Key

Generate age keys outside this public repository:

```bash
age-keygen -o keys/demo.agekey
```

Commit only public recipients in `.sops.yaml`. Never commit the age private key.

## 2. Add `.sops.yaml`

```yaml
creation_rules:
  - path_regex: deploy/secrets/.*\.sops\.(env|ya?ml)$
    age: age1replacewithpublicrecipient0000000000000000000000000
  - path_regex: deploy/inventories/.*\.ini\.sops$
    age: age1replacewithpublicrecipient0000000000000000000000000
```

The recipient above is fake and must be replaced in a private app repo.

## 3. Create Encrypted Secret Files

Use `.env` files for simple app runtime key/value data:

```text
APP_KEY=base64:replace-me
DB_HOST=127.0.0.1
DB_DATABASE=app
DB_USERNAME=app
DB_PASSWORD=replace-me
```

Edit with SOPS:

```bash
sops deploy/secrets/staging.app.sops.env
```

SOPS writes encrypted content back to the same file. Commit only encrypted files.

## 4. Configure The Manifest

```yaml
secrets:
  provider: sops_age
  sources:
    - name: shared_runtime
      file: deploy/secrets/shared.{{ app_env }}.sops.env
      class: app
    - name: app_runtime
      file: deploy/secrets/{{ app_env }}.app.sops.env
      class: app
  merge:
    override_order:
      - shared_runtime
      - app_runtime
  render:
    app_env_file:
      enabled: true
      target: .env
      mode: "0600"
      include_classes:
        - app
```

Use `class: app` for values that should be written to Laravel `.env`. Use other classes only when a workflow or role consumes them.

## 5. Configure GitHub Environment Secrets

Provide the age private key through one trusted path:

- `SOPS_AGE_KEY` in a GitHub environment secret,
- a protected self-hosted runner,
- a secure deployment machine for manual runs.

If inventory also comes from a SOPS file, the same `SOPS_AGE_KEY` must decrypt that file too. See [App Setup](setup.md#7-choose-one-inventory-source).
