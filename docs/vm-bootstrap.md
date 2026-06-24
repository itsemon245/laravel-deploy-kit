# VM Bootstrap

Bootstrap is separate from normal deploy. Normal deploy assumes the VM already has SSH access, Docker, an app directory, and the expected repository checkout shape.

The bootstrap roles are tested against Ubuntu 24.04 LTS or newer. The role fails early on unsupported distributions by default.

## App VM

The `vm-bootstrap.yml` reusable workflow runs `ansible/playbooks/bootstrap-host.yml` against the `app` inventory group by default. It can:

- create a deploy user,
- configure authorized SSH keys when provided,
- install Docker and the Compose plugin,
- create the app directory,
- clone or verify the app repository,
- render the initial app `.env` from the selected provider,
- install monitoring only when configured,
- validate Docker and Compose.

Pass `app_repo_url` from the private app workflow or define `repo.url` in the private manifest.

On Ubuntu 24.04, the distro package for Compose v2 is `docker-compose-v2`. The default `docker_engine` role installs `docker.io` plus `docker-compose-v2` from Ubuntu repositories.

## Inventory And SSH

Bootstrap uses the same inventory fallback chain as deploy:

1. GitHub environment secret.
2. SOPS inventory file.
3. Infisical inventory secret.

`known_hosts` is optional. Private production workflows may enforce it through app repo policy.

## DB And Redis

PostgreSQL and Redis provisioning are explicit one-time operations:

- `provision-postgres.yml` targets the `postgres` inventory group.
- `provision-redis.yml` targets the `redis` inventory group.

These workflows are separate from regular Laravel backend rollout.
