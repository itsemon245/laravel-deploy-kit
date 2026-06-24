# Multiple Secret Sources

Multiple sources allow shared defaults and app-specific overrides.

## Example Order

```yaml
secrets:
  provider: sops_age
  sources:
    - name: shared_app_defaults
      file: deploy/secrets/shared.staging.sops.env
      class: app
    - name: app_runtime
      file: deploy/secrets/staging.app.sops.env
      class: app
    - name: app_deploy
      file: deploy/secrets/staging.deploy.sops.yml
      class: deploy
  merge:
    override_order:
      - shared_app_defaults
      - app_runtime
      - app_deploy
```

If both `shared_app_defaults` and `app_runtime` define `MAIL_FROM_ADDRESS`, the app-specific value wins.

## Class Separation

Merge order controls override behavior. Class controls where the value may be used. A later `deploy` source must not cause deploy-only keys to be rendered into `.env`.

