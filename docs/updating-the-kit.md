# Updating The Kit

App repositories should pin the deploy kit to a release.

## Pinning

```yaml
uses: your-github-org/laravel-deploy-kit/.github/workflows/laravel-vm-deploy.yml@v1
```

Use a major tag for routine updates or an exact tag for stricter change control.

## Release Process

1. Update docs and changelog.
2. Run validation, tests, and Ansible syntax checks once implementation exists.
3. Tag a release such as `v1.1.0`.
4. Move the `v1` major tag after compatibility is confirmed.
5. Roll out one staging app before production apps.

## Drift Checklist

- app workflow still pins the intended kit version,
- manifest schema version is supported,
- secret provider shape is still valid,
- Compose service names still match the manifest,
- health check endpoint still represents app readiness.

Run the local checker from an app repository:

```bash
path/to/laravel-deploy-kit/bin/check-workflow-version --path . --expected-ref v1
```
