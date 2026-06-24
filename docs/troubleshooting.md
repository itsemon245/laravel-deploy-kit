# Troubleshooting

## SSH Failures

- Confirm the target inventory is private and correct.
- Confirm the deploy key or SSH key is available only to the workflow that needs it.
- Confirm known-hosts handling is intentional for the environment.

## Manifest Validation Failures

- Check required keys under `app`, `repo`, `compose`, `build`, `cleanup`, `health`, and `secrets`.
- Confirm `build.mode` is `per_vm` for the default path.
- Confirm every source in `override_order` exists.

## Secret Resolution Failures

- Confirm provider auth works.
- Confirm source paths exist.
- Confirm the source class is one of the supported classes.
- Confirm secret values are not printed in logs.

## Docker Build Failures

- Confirm the VM has Docker and the Compose plugin.
- Confirm compose files exist in the checked-out app repo.
- Confirm disk free space is above the cleanup threshold.

## Health Check Failures

- Confirm the app service is listening on the expected internal URL.
- Confirm migrations completed.
- Confirm queue or scheduler failures did not block boot.

