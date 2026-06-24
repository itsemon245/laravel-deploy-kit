# Laravel Deploy Kit Plan

## Context

We maintain multiple production Laravel applications with a similar deployment shape:

- Laravel app code is deployed to Linux VMs.
- VMs are already placed behind upstream load balancers by the sys-admin team.
- Staging usually runs on one VM with app, database, and Redis together.
- Production usually starts with multiple backend/app VMs, one DB VM, and one Redis VM on the same private LAN.
- Deployment is currently GitHub Actions + Ansible + Docker Compose.
- The app VM pulls the Git branch, builds the Docker image locally with Compose, gracefully drains queue workers, recreates services, and health-checks the result.
- New projects are bootstrapped by copying deployment files from older projects.
- Later fixes and optimizations stay in only the project where they were made, causing stale copied configs elsewhere.
- New VM setup is still manual-heavy: Docker install/upgrade, deploy user/SSH, repo checkout, `.env`, GitHub credentials, Ansible access, DB/Redis tuning, and service startup.

The goal is to create a reusable, public `laravel-deploy-kit` repository that centralizes the generic deployment engine while keeping every app's private topology, secrets, and app-specific choices outside the public kit.

## Problems To Solve

1. **Copy-paste deployment drift**
   Deployment playbooks, workflows, Docker/Compose conventions, monitoring snippets, upload scripts, and VM bootstrap steps are copied across projects. Bug fixes and improvements do not propagate cleanly.

2. **New project bootstrap fatigue**
   Every new Laravel app requires manually cloning deployment structure from a previous app and stripping project-specific details.

3. **New VM onboarding fatigue**
   Every new staging/production/backend/DB/Redis VM requires repeated manual setup.

4. **Secret management friction**
   GitHub environment secrets such as a single `ENV_DOTENV` blob are hard to inspect, hard to update one key at a time, and not ideal for production-grade operations.

5. **Deployment build cost**
   We intentionally moved away from CI-built Docker images because frequent staging builds hit Docker Hub/GitHub limits and cost, while VM-side builds have more stable cache and lower practical overhead.

## Non-Goals

- Do not migrate to Kubernetes, Nomad, or Swarm in the first version.
- Do not require a private Docker registry for the default path.
- Do not require CI-built Docker images for the default path.
- Do not commit plaintext secrets to app repositories.
- Do not make Laravel containers fetch secrets directly at runtime in the first version.
- Do not publish any company/private topology, domains, IPs, usernames, or credentials in the public kit.

## Primary Decision Summary

Build a **public generic deploy kit** with:

- reusable GitHub workflows,
- Ansible playbooks and roles,
- VM bootstrap roles,
- Laravel Docker Compose deployment roles,
- DB/Redis provisioning roles,
- monitoring templates,
- secrets-provider adapters,
- documentation and examples.

Each app repo keeps:

- a tiny local GitHub workflow trigger,
- a non-secret deployment manifest,
- app-specific Dockerfile and Compose files,
- `.env.example`,
- optional encrypted SOPS files if that app uses SOPS,
- no plaintext production secrets.

Default deployment mode:

```text
app repo push -> tiny app workflow -> public deploy-kit reusable workflow -> Ansible -> VM git sync -> VM-side Docker build -> Compose rollout
```

## Decision Record

### Public Kit Vs Private Shared Repo

Options considered:

- **Private repo under one personal account**
  - Problem: app repos may live under another personal account, and private reusable workflows are not reliably shareable across unrelated personal accounts.

- **Private org repo**
  - Good if all projects live under one GitHub organization.
  - Not enough for non-company/personal projects.

- **Public generic repo**
  - Works across personal accounts, organizations, private app repos, and unrelated projects.
  - Requires stripping all private details and treating the repo as generic software.

Decision:

- Use a **public `itsemon245/laravel-deploy-kit` repo**.
- Keep only generic logic, examples, fake domains, fake IPs, and templates in it.
- Keep all private app details in app repos, GitHub environments, Infisical, or SOPS.

### Reusable Workflow Vs Local Workflow Only

Options considered:

- **Copy full workflow into every app repo**
  - Simple, but repeats the original drift problem.

- **Use `jobs.<job>.uses` to call public reusable workflow**
  - Centralizes workflow logic.
  - App repo still owns branch triggers.

- **Local workflow checks out deploy-kit and runs scripts**
  - Useful fallback if reusable workflow access becomes awkward.
  - More boilerplate in each app repo.

Decision:

- Default to GitHub reusable workflows from the public kit:

```yaml
jobs:
  deploy:
    uses: itsemon245/laravel-deploy-kit/.github/workflows/laravel-vm-deploy.yml@v1
    with:
      app_env: ${{ github.ref_name }}
      manifest_path: deploy/manifest.yml
    secrets: inherit
```

- Keep a documented fallback workflow that checks out the deploy kit and runs a CLI/script manually.

### CI-Built Images Vs VM-Side Builds

Options considered:

- **CI builds and pushes images; VMs pull**
  - Builds once, consistent image.
  - Costs GitHub runtime.
  - Can hit Docker Hub limits/subscription needs.
  - Adds registry auth and push/pull churn.

- **VMs build locally**
  - Matches current operational choice.
  - Preserves persistent Docker cache on VMs.
  - Keeps GitHub Actions cheap and short.
  - Builds multiple times in production, but production deploys are less frequent.

- **Build once on one VM and distribute over private LAN**
  - Avoids CI and registry.
  - More moving parts.
  - Useful later if production builds become slow.

Decision:

- Default to **VM-side Docker builds**.
- Preserve Docker build cache.
- Avoid unconditional Docker pruning in deploy path.
- Add future optional mode: `build_once_private_lan`.

### Docker Cleanup Policy

Options considered:

- **Prune on every deploy**
  - Frees disk.
  - Destroys build cache and undermines fast VM builds.

- **Never prune**
  - Fast builds.
  - Risks disk exhaustion.

- **Disk-pressure cleanup**
  - Preserve cache normally.
  - Prune only when free disk drops below threshold.

Decision:

- Default to **disk-pressure cleanup only**.
- Add optional scheduled deep cleanup outside deploy path.

### Secrets Manager

Options considered:

- **GitHub environment secret containing full `.env`**
  - Simple.
  - Poor visibility.
  - Hard to update one key.
  - Not a full secrets-management workflow.

- **Infisical Cloud**
  - Low operations overhead.
  - Good UI and audit/versioning.
  - Some company environments may not allow external secret custody.

- **Infisical self-hosted**
  - Company controls storage and network.
  - Good UI and audit/versioning.
  - Requires operating Infisical itself.

- **SOPS + age**
  - No server required.
  - Encrypted secrets can live in private app repos.
  - Good fallback/emergency mode.
  - Less friendly for non-CLI users, weaker central audit and access UX.

Decision:

- Support a provider interface with:
  - `infisical_cloud`,
  - `infisical_self_hosted`,
  - `sops_age`.
- Normalize all provider outputs into one merged secret dictionary.
- Render `.env` from normalized app runtime secrets.
- Keep deployment/control-plane secrets separate from app runtime secrets.

### Multiple Secret Sources

Options considered:

- **One source per app**
  - Simple.
  - Duplicates shared keys like `GEMINI_API_KEY` and `ML_API_KEY`.

- **Infisical imports only**
  - Good within one Infisical project/environment/folder.
  - Cross-project behavior and edition constraints should not be assumed.

- **Deploy-kit fetches multiple sources and merges**
  - Works across Infisical Cloud, self-hosted, and SOPS.
  - Explicit override order.
  - Portable.

Decision:

- Implement multiple secret sources with deterministic merge order.
- Earlier sources are base/shared secrets.
- Later sources override earlier sources.

Example:

```yaml
secrets:
  provider: infisical
  sources:
    - name: company_shared_ai
      project_id: shared-services
      env_slug: production
      path: /ai
      class: app
    - name: app_runtime
      project_id: podcast-flow
      env_slug: production
      path: /app
      class: app
    - name: app_deploy
      project_id: podcast-flow
      env_slug: production
      path: /deploy
      class: deploy
```

### App Runtime Secrets Vs Deployment Secrets

Decision:

- Keep these separate.

App runtime secrets:

- `APP_KEY`
- `DB_HOST`
- `DB_DATABASE`
- `DB_USERNAME`
- `DB_PASSWORD`
- `REDIS_HOST`
- `REDIS_PASSWORD`
- mail provider secrets
- object storage/CDN secrets
- third-party API keys used by the app

Deployment/control-plane secrets:

- SSH private key for VM access
- GitHub deploy key or repo read token
- Infisical machine identity credentials, unless using OIDC
- SOPS age private key
- private Ansible inventory, if considered sensitive
- DB/Redis bootstrap/admin credentials

Only app runtime secrets should be rendered into the application `.env`.

Deployment secrets should be used transiently by GitHub Actions/Ansible and should not be written into the app `.env`.

## Target `laravel-deploy-kit` Repository Structure

```text
laravel-deploy-kit/
  README.md
  LICENSE
  CHANGELOG.md
  SECURITY.md

  .github/
    workflows/
      laravel-vm-deploy.yml
      vm-bootstrap.yml
      provision-postgres.yml
      provision-redis.yml
      validate-app-manifest.yml

  ansible/
    ansible.cfg
    requirements.yml
    playbooks/
      laravel-vm-deploy.yml
      bootstrap-host.yml
      provision-postgres.yml
      provision-redis.yml
      refresh-secrets.yml
      validate-manifest.yml
    roles/
      manifest_validate/
      docker_engine/
      host_common/
      app_bootstrap/
      repo_checkout/
      compose_preflight/
      docker_cleanup_policy/
      secrets_infisical/
      secrets_sops/
      secrets_merge/
      render_env_file/
      laravel_remote_build/
      laravel_migrate_once/
      horizon_drain/
      compose_rollout/
      health_check/
      postgres_node/
      redis_node/
      monitoring/

  bin/
    ldk
    render-dotenv
    validate-manifest

  templates/
    app-workflows/
      deploy.yml
      refresh-secrets.yml
      bootstrap-vm.yml
    manifests/
      laravel-compose.staging.yml
      laravel-compose.production.yml
    docker-compose/
      base.yml
      staging-with-postgres-redis.yml
      production-app-only.yml
      monitoring.yml
    nginx/
      laravel-octane-reverb.conf
    postgres/
      postgresql.conf.j2
    redis/
      redis.conf.j2
    promtail/
      promtail-config.yml.j2
    sops/
      age-key-policy.example.md

  examples/
    app-repo/
      .github/workflows/deploy.yml
      deploy/manifest.yml
      deploy/secrets/staging.app.sops.env.example
      deploy/secrets/production.app.sops.env.example
    inventories/
      staging-single-vm.ini
      production-multi-vm.ini

  docs/
    architecture.md
    decisions.md
    app-repo-getting-started.md
    kit-repo-development.md
    vm-bootstrap.md
    deployment-flow.md
    secret-providers.md
    infisical-cloud.md
    infisical-self-hosted.md
    sops-age.md
    multiple-secret-sources.md
    app-vs-deploy-secrets.md
    db-redis-provisioning.md
    monitoring.md
    updating-the-kit.md
    troubleshooting.md
```

## App Repository Structure

Each app repo should keep only thin project-specific deployment configuration:

```text
app-repo/
  .github/
    workflows/
      deploy.yml
      refresh-secrets.yml
      bootstrap-vm.yml

  deploy/
    manifest.yml
    manifest.example.yml
    secrets/
      staging.app.sops.env        # only if SOPS provider is used
      production.app.sops.env     # only if SOPS provider is used
      staging.deploy.sops.yml     # only if SOPS provider is used
      production.deploy.sops.yml  # only if SOPS provider is used

  Dockerfile
  docker-compose.yml
  staging.docker-compose.yml
  production.docker-compose.yml
  .env.example
```

Do not commit:

- `.env`
- private SSH keys
- API tokens
- database passwords
- Redis passwords
- real production inventory, if sensitive
- Infisical machine identity secrets
- SOPS age private key

## App Repo Tiny Workflow

Default app repo workflow:

```yaml
name: Deploy

on:
  push:
    branches: [staging, production]
  workflow_dispatch: {}

concurrency:
  group: deploy-${{ github.ref_name }}
  cancel-in-progress: true

jobs:
  deploy:
    uses: itsemon245/laravel-deploy-kit/.github/workflows/laravel-vm-deploy.yml@v1
    with:
      app_env: ${{ github.ref_name }}
      manifest_path: deploy/manifest.yml
    secrets: inherit
```

The app repo owns:

- branch triggers,
- concurrency,
- optional path filtering,
- environment protection rules,
- app-specific manifest.

The deploy kit owns:

- workflow body,
- Ansible install/config,
- inventory creation,
- secret resolution,
- deploy playbook execution,
- VM-side build and rollout logic.

## Manifest Design

Example manifest:

```yaml
schema_version: 1

app:
  name: podcast-flow
  type: laravel
  app_dir: /var/www/app/webroot
  env: "{{ app_env }}"

repo:
  git_ref: "{{ app_env }}"
  remote: origin
  clean: true

compose:
  project_name: podcast-flow
  files:
    - docker-compose.yml
    - "{{ app_env }}.docker-compose.yml"
  build_service: web
  app_services:
    - web
    - queues
    - scheduler
    - ws
  queue_service: queues
  nginx_service: nginx

build:
  mode: per_vm
  preserve_cache: true
  progress: plain

cleanup:
  policy: disk_pressure_only
  min_free_kb: 10485760
  prune_build_cache: false
  scheduled_deep_cleanup: false

database:
  migrations:
    enabled: true
    run_once: true
    command: php artisan migrate --force

health:
  type: http
  url: http://127.0.0.1:8000/health
  retries: 6
  delay: 5

secrets:
  provider: infisical
  url: https://infisical.company.internal
  auth:
    method: oidc
  sources:
    - name: company_shared_ai
      project_id: shared-services
      env_slug: "{{ app_env }}"
      path: /ai
      class: app
    - name: app_runtime
      project_id: podcast-flow
      env_slug: "{{ app_env }}"
      path: /app
      class: app
    - name: app_deploy
      project_id: podcast-flow
      env_slug: "{{ app_env }}"
      path: /deploy
      class: deploy
  merge:
    override_order:
      - company_shared_ai
      - app_runtime
      - app_deploy
  render:
    app_env_file:
      enabled: true
      target: .env
      mode: "0600"
      include_classes:
        - app
```

## Secret Provider Design

The deploy kit should expose a normalized internal variable:

```yaml
resolved_secrets:
  app:
    APP_KEY: ...
    DB_PASSWORD: ...
  deploy:
    GITHUB_DEPLOY_KEY: ...
  db:
    POSTGRES_PASSWORD: ...
  redis:
    REDIS_PASSWORD: ...
```

Provider roles should only fetch and normalize secrets.

The `secrets_merge` role should:

- read ordered sources,
- merge dictionaries,
- allow later sources to override earlier sources,
- detect duplicate keys if configured,
- allow source classes: `app`, `deploy`, `db`, `redis`, `monitoring`,
- never log secret values.

The `render_env_file` role should:

- render only configured classes, normally `app`,
- write to `{{ app_dir }}/.env`,
- set owner to deploy/app user,
- set mode `0600`,
- use `no_log: true`,
- optionally restart services if content changed.

## Infisical Provider

Support both:

- Infisical Cloud: `https://app.infisical.com`
- Infisical self-hosted: custom URL such as `https://infisical.company.internal`

Authentication options:

- preferred: GitHub OIDC to Infisical identity,
- fallback: Infisical machine identity client ID/secret stored in GitHub environment secrets,
- fallback for manual runs: locally provided token.

Do not assume cross-project secret imports.

For shared company-level secrets, use multiple sources:

```yaml
sources:
  - name: company_shared
    project_id: shared-services
    env_slug: production
    path: /ai
    class: app
  - name: app_runtime
    project_id: podcast-flow
    env_slug: production
    path: /app
    class: app
```

Infisical Secret Imports can still be used inside a project/environment/folder, but the deploy kit should not depend on them for the cross-project shared-secret model.

## SOPS + Age Provider

Support multiple encrypted files:

```yaml
secrets:
  provider: sops
  sources:
    - name: company_shared
      file: deploy/secrets/common.production.sops.env
      class: app
    - name: app_runtime
      file: deploy/secrets/production.app.sops.env
      class: app
    - name: app_deploy
      file: deploy/secrets/production.deploy.sops.yml
      class: deploy
```

The app repo may commit encrypted SOPS files.

Do not commit:

- unencrypted source files,
- `.env`,
- age private keys.

Age private key options:

- store `SOPS_AGE_KEY` in GitHub environment secrets,
- store on a trusted self-hosted runner,
- keep on a secure deployment machine for manual runs.

## How To Update Secrets

### Infisical Cloud Or Self-Hosted

To update one app runtime secret:

1. Open Infisical.
2. Select the app project.
3. Select environment: `staging` or `production`.
4. Open path `/app`.
5. Update the key, for example `DB_PASSWORD`.
6. Run the app repo `refresh-secrets` workflow or run a normal deploy.
7. Ansible fetches the current secret set, renders `.env`, and restarts affected services if configured.

To update shared secrets:

1. Open the shared Infisical project, for example `shared-services`.
2. Select environment: `staging` or `production`.
3. Open path `/ai`.
4. Update `GEMINI_API_KEY` or `ML_API_KEY`.
5. Run `refresh-secrets` or deploy for each app that consumes the shared source.

To update deployment secrets:

1. Open the app project.
2. Open path `/deploy`.
3. Update control-plane values such as GitHub deploy key or DB bootstrap credentials.
4. Run the workflow/playbook that needs that value.
5. Do not render `/deploy` values into app `.env`.

### SOPS + Age

To update one app runtime secret:

1. Pull latest app repo.
2. Decrypt/edit the relevant file:

```bash
sops deploy/secrets/production.app.sops.env
```

3. Change one key.
4. Save; SOPS writes encrypted content back.
5. Commit the encrypted file.
6. Push to branch.
7. Run deploy or `refresh-secrets`.

To update shared SOPS secrets:

1. Edit the shared encrypted file used by the app:

```bash
sops deploy/secrets/common.production.sops.env
```

2. Commit and push the encrypted change.
3. Deploy or refresh each app that consumes it.

For central shared SOPS files across many projects, prefer a separate private secrets repo only if access control is clear. Otherwise, duplicate encrypted shared files per app and accept the maintenance cost.

## Deployment Flow

### Staging Single-VM Flow

1. Push to `staging`.
2. App repo tiny workflow calls public deploy-kit workflow.
3. Deploy kit checks out app repo and deploy-kit repo.
4. Workflow resolves manifest.
5. Workflow authenticates to secrets provider.
6. Ansible connects to staging VM.
7. VM preflight:
   - app dir exists,
   - git repo exists,
   - Docker daemon works,
   - Docker Compose plugin works,
   - required compose files exist,
   - disk threshold is satisfied.
8. Secrets are fetched and rendered to `.env`.
9. VM git syncs the staging branch.
10. VM validates compose config.
11. VM builds Docker image locally with cache.
12. Horizon is paused/terminated if queues are running.
13. Migrations run once.
14. Compose recreates services.
15. Health check runs.
16. Service state is printed without secrets.

### Production Multi-VM Flow

1. Push to `production`.
2. App repo tiny workflow calls public deploy-kit workflow.
3. Ansible runs with `serial: 1` for backend app VMs.
4. Migrations run once only.
5. For each backend VM:
   - preflight,
   - render `.env`,
   - git sync,
   - build locally,
   - pause/terminate Horizon,
   - recreate services,
   - health check.
6. Continue to next VM only after health passes.

## VM Bootstrap Flow

Bootstrap should be separate from normal deploy.

App VM bootstrap:

- create deploy user,
- configure SSH access,
- install/upgrade Docker CE and Compose plugin,
- add deploy user to Docker group,
- create app directory,
- clone repository or prepare empty checkout,
- write initial `.env` from secrets provider,
- install monitoring/log shipping if configured,
- validate Docker/Compose.

DB VM bootstrap:

- install Docker,
- render PostgreSQL Compose/config from VM size profile,
- create data directories,
- set memory/connection/WAL/autovacuum profile,
- start PostgreSQL,
- health check,
- optionally create DB/user.

Redis VM bootstrap:

- install Docker,
- render Redis config from VM size profile,
- set memory policy,
- configure persistence choice,
- set file descriptor limits,
- start Redis,
- health check.

## Future Optional Build Mode

Add later if production build time becomes painful:

```yaml
build:
  mode: build_once_private_lan
```

Possible implementation:

- first app VM builds image tagged with git SHA,
- image is exported with `docker save`,
- transferred over private LAN with `ssh`/`rsync`,
- loaded on other app VMs with `docker load`,
- all VMs run Compose using the same local tag.

Do not implement this in phase one unless necessary.

## Documentation To Write

### Kit Repo Documentation

`README.md`

- What the kit is.
- What it does not do.
- Supported topology.
- Quick start.
- Security warning: never put real secrets or topology in the public repo.

`docs/architecture.md`

- Public kit + private app repos.
- GitHub workflow trigger model.
- Ansible role flow.
- VM-side build rationale.
- Secret provider abstraction.

`docs/decisions.md`

- Decision record from this plan.
- Include options considered and why each final choice was made.

`docs/kit-repo-development.md`

- How to work on the kit.
- How to version releases.
- How to test roles/playbooks.
- Backward compatibility expectations.

`docs/app-repo-getting-started.md`

- Add tiny workflow.
- Add manifest.
- Configure GitHub environments.
- Choose secret provider.
- First staging deploy.

`docs/vm-bootstrap.md`

- How to bootstrap app, DB, Redis, and monitoring VMs.
- Required SSH access.
- Idempotency expectations.

`docs/deployment-flow.md`

- Staging flow.
- Production serial rollout flow.
- Migrations.
- Queue drain.
- Health checks.

`docs/secret-providers.md`

- Provider interface.
- Common manifest shape.
- Source merge order.
- Secret classes.

`docs/infisical-cloud.md`

- Cloud setup.
- Machine identity/OIDC setup.
- Project/env/path conventions.
- Updating secrets.

`docs/infisical-self-hosted.md`

- Recommended self-hosting shape.
- Backups.
- TLS.
- Admin bootstrap.
- Upgrade considerations.
- High-level hardening checklist.

`docs/sops-age.md`

- Age key generation.
- `.sops.yaml`.
- Editing secrets.
- CI/deploy decryption.
- Team access and key rotation.

`docs/multiple-secret-sources.md`

- Shared company secrets.
- App runtime secrets.
- Deploy/control-plane secrets.
- Merge behavior.
- Override examples.

`docs/app-vs-deploy-secrets.md`

- What belongs in `/app`.
- What belongs in `/deploy`.
- What gets rendered into `.env`.
- What must never be rendered into `.env`.

`docs/db-redis-provisioning.md`

- DB VM provisioning.
- Redis VM provisioning.
- VM profile tuning.
- When to separate staging/production.

`docs/monitoring.md`

- Promtail/Loki/Grafana templates.
- Public vs private monitoring endpoints.
- Required secrets.

`docs/updating-the-kit.md`

- How app repos pin `@v1`.
- How to release `v1.1.0`.
- How to roll out updates across apps.
- Drift detection checklist.

`docs/troubleshooting.md`

- SSH failures.
- Docker build failures.
- Compose validation failures.
- Secret resolution failures.
- Health check failures.
- Disk pressure cleanup.

### App Repo Documentation

Each app should add:

`deploy/manifest.example.yml`

- Safe example with fake values.

`docs/deployment.md` or `deploy/README.md`

- Which deploy-kit version the app uses.
- Which branches deploy.
- Which secret provider is active.
- Which Infisical projects/paths or SOPS files are used.
- How to deploy staging.
- How to deploy production.
- How to refresh secrets.
- Who owns DB/Redis VM provisioning.

## Execution Phases

### Phase 1: Create Public Kit Skeleton

- Create repo structure.
- Add docs skeleton.
- Add examples with fake values.
- Add reusable workflow placeholder.
- Add manifest schema draft.
- Add Ansible requirements file.

### Phase 2: Implement Manifest Validation

- Validate required keys.
- Validate compose files.
- Validate build mode.
- Validate secret provider shape.
- Validate source merge order.
- Add a local validation command.

### Phase 3: Implement Core Deploy Roles

- `repo_checkout`
- `compose_preflight`
- `docker_cleanup_policy`
- `laravel_remote_build`
- `horizon_drain`
- `laravel_migrate_once`
- `compose_rollout`
- `health_check`

### Phase 4: Implement Secret Provider Interface

- `secrets_infisical`
- `secrets_sops`
- `secrets_merge`
- `render_env_file`

Start with one provider first, but keep the interface stable.

Recommended order:

1. SOPS + age, because it is testable without standing up Infisical.
2. Infisical Cloud/self-hosted, using the same normalized output.

### Phase 5: Implement Reusable GitHub Workflow

- Checkout app repo.
- Checkout deploy-kit repo.
- Install Ansible.
- Install required Ansible collections.
- Configure SSH.
- Validate manifest.
- Run deploy playbook.

### Phase 6: Implement Bootstrap Roles

- Docker install/upgrade.
- deploy user.
- app dir.
- repo clone/check.
- initial secret render.
- DB and Redis node setup.

### Phase 7: Pilot On One App

Recommended pilot: `podcast-flow`, because it has the newest deployment shape.

Pilot scope:

- staging first,
- VM-side build,
- SOPS or Infisical test secrets,
- render `.env`,
- deploy,
- verify health checks,
- confirm Docker cache is preserved.

### Phase 8: Production Pilot

- Use production branch.
- Use serial backend rollout.
- Confirm migrations run once.
- Confirm queue drain works.
- Confirm rollback story is acceptable.

### Phase 9: Migrate Other Apps

Order:

1. `ideabuddy`
2. `viralseek`
3. `backpips`
4. `clone-voice`

For each app:

- replace large workflow with tiny trigger workflow,
- add manifest,
- configure secret provider,
- test staging,
- test production.

### Phase 10: Versioning And Updates

- Tag stable releases: `v1.0.0`, `v1.1.0`.
- App repos pin to major or exact minor:

```yaml
uses: itsemon245/laravel-deploy-kit/.github/workflows/laravel-vm-deploy.yml@v1
```

- Maintain changelog.
- Add a small drift/update checker later that reports apps not using the latest recommended tag.

## Testing And Verification Strategy

Use focused tests:

- manifest validation tests,
- secret merge tests,
- SOPS decrypt/merge test with fake encrypted fixture,
- Ansible syntax checks,
- dry-run/check-mode where useful,
- local fake inventory smoke tests,
- one real staging VM integration test.

Do not test with real secrets in the public repo.

## Security Rules

- The public kit must contain no real secrets, IPs, domains, or internal hostnames.
- All example secrets must be fake.
- Use `no_log: true` around secret tasks.
- Never print rendered `.env`.
- Never commit `.env`.
- Never commit age private keys.
- Prefer OIDC for Infisical when available.
- If using Infisical machine credentials in GitHub, store only those bootstrap credentials, not whole app `.env` files.
- Separate app runtime secrets from deployment/control-plane secrets.
- Render only app runtime secrets into app `.env`.

## Open Questions For Implementation

- Will Infisical self-hosted be deployed before the first app pilot, or should the pilot use SOPS first?
- Will app repos live under personal accounts, an organization, or mixed ownership?
- Should private inventories be kept in GitHub environment secrets, Infisical `/deploy`, or generated from app manifest variables?
- Should `known_hosts` be mandatory before production deploy, or is `StrictHostKeyChecking=accept-new` acceptable initially?
- Should production deploys require GitHub environment approval?
- Which DB/Redis VM sizes need first-class tuning profiles?

## Final Direction

Build a public `laravel-deploy-kit` as a reusable deployment engine, not a copy of any real project's deployment folder.

Keep app repos thin and private where needed.

Keep VM-side Docker builds as the default.

Use multiple secret sources with deterministic merging.

Support Infisical Cloud, Infisical self-hosted, and SOPS + age.

Separate app runtime secrets from deployment/control-plane secrets.

Start with one staging pilot before migrating the rest.
