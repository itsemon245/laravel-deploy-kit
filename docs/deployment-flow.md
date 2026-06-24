# Deployment Flow

## Staging Single-VM Flow

1. Push to the staging branch.
2. The app workflow calls the deploy-kit reusable workflow.
3. The manifest is validated.
4. A temporary Ansible inventory is resolved from GitHub environment secret, then SOPS, then Infisical.
5. `known_hosts` is used when provided; otherwise SSH uses the documented non-blocking fallback.
6. Secrets are resolved and app runtime values are rendered to `.env`.
7. The VM syncs the requested git ref.
8. Compose configuration is validated.
9. Missing `compose.one_time_services` are created when configured.
10. The app image is built locally on the VM.
11. Queue workers are drained when configured.
12. Migrations run once.
13. Compose recreates `compose.app_services`.
14. The health check must pass.

## Production Multi-VM Flow

Production app VMs should roll serially:

1. Optional GitHub environment approval may hold the job before any deploy steps.
2. Resolve inventory and SSH policy.
3. Run migrations once.
4. Deploy one backend app VM.
5. Wait for health to pass.
6. Continue to the next backend app VM.

This keeps a failed build or health check from rolling across every backend at once.
Regular production app deploys do not provision PostgreSQL or Redis VMs.

## Inventory Fallback

The reusable workflows resolve inventory in this order:

1. `LDK_INVENTORY` GitHub environment secret.
2. SOPS-encrypted inventory file path passed to the workflow.
3. Infisical secret, usually `ANSIBLE_INVENTORY` under `/deploy`.

The resolved inventory file is temporary runner state and must not be committed.

## Build And Cleanup

The default build mode is `per_vm`. Docker build cache should be preserved unless disk pressure crosses the configured threshold.
