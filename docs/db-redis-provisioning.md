# DB And Redis Provisioning

DB and Redis provisioning are separate one-time operations, not part of the normal app deploy path.

## Staging

Staging can run app, PostgreSQL, and Redis on one VM when cost and simplicity matter more than isolation.

## Production

Production should usually separate:

- app VMs,
- PostgreSQL VM,
- Redis VM.

Keep real sizing, IPs, hostnames, and private network details in private inventories or manifests.

## VM Profiles

Provisioning roles expose variables for:

- PostgreSQL memory and connection settings,
- WAL and autovacuum settings,
- Redis max memory and eviction policy,
- persistence choices,
- file descriptor limits.

Run these playbooks only when creating or intentionally changing DB/Redis infrastructure. Production backend deploys should target app VMs only.
