# Demo App Deploy Notes

This example uses fake values only.

## Branches

- `staging` deploys staging.
- `production` deploys production.

## Secret Provider

The example manifest uses SOPS + age and separates:

- shared runtime values,
- app runtime values,
- deployment/control-plane values.

Only runtime values with class `app` should be rendered into `.env`.

The files under `deploy/secrets/*.example` show plaintext shape only. Real app repos should create encrypted files without the `.example` suffix.

## Before Using In A Real App

- Replace the fake kit repository owner.
- Replace fake paths and app names.
- Add real encrypted SOPS files in the private app repo.
- Keep `.env`, age private keys, SSH keys, and tokens out of git.
