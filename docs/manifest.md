# Manifest Reference

The deploy manifest is the app repo's non-secret contract with Laravel Deploy Kit. It describes where the app lives on the VM, which Git ref and Compose files to use, how to build and roll out services, how health is checked, and which secret sources should be resolved.

Keep real topology and secrets out of the public kit. Private app repos usually store this file at `deploy/manifest.yml`.

## Layering Model

Use one shared manifest for most apps:

```text
deploy/manifest.yml
```

Put environment-specific differences under `environments.<app_env>`:

```yaml
environments:
  production:
    compose:
      app_services:
        - web
        - queues
        - scheduler
        - ws
    cleanup:
      min_free_kb: 20971520
```

The deploy kit resolves manifests in this order:

1. If a full environment manifest exists, use it instead of the base:
   - `deploy/manifest.production.yml`
   - `deploy/production.manifest.yml`
2. Otherwise load `deploy/manifest.yml`.
3. Merge `environments.<app_env>` from the base manifest.
4. If an environment override file exists, merge it last:
   - `deploy/manifest.production.override.yml`
   - `deploy/production.manifest.override.yml`

Merges are recursive for dictionaries. Lists are replaced, which is useful for `compose.files`, `compose.app_services`, `compose.one_time_services`, `secrets.sources`, and `secrets.merge.override_order`.

Use a full environment manifest only when staging and production differ enough that sharing becomes harder to read. Prefer the single shared manifest plus `environments` for normal apps.

## Validation

Validate from the app repo:

```bash
path/to/laravel-deploy-kit/bin/validate-manifest deploy/manifest.yml staging
```

The manifest supports `{{ app_env }}` templating. Reusable workflows pass `app_env` from the app workflow input or branch name.

## Minimal Shape

```yaml
schema_version: 1

app:
  name: demo-laravel
  type: laravel
  app_dir: /srv/demo-laravel/current
  env: "{{ app_env }}"

repo:
  git_ref: "{{ app_env }}"
  remote: origin
  clean: true

compose:
  project_name: demo_laravel
  files:
    - docker-compose.yml
    - "{{ app_env }}.docker-compose.yml"
  build_service: web
  app_services:
    - web
  queue_service: queues

build:
  mode: per_vm
  preserve_cache: true
  progress: plain

health:
  type: http
  url: http://127.0.0.1:8080/health

secrets:
  provider: sops_age
  sources:
    - name: app_runtime
      file: deploy/secrets/{{ app_env }}.app.sops.env
      class: app
  merge:
    override_order:
      - app_runtime
  render:
    app_env_file:
      enabled: true
      target: .env
      mode: "0600"
      include_classes:
        - app

environments:
  staging:
    compose:
      one_time_services:
        - postgres
        - redis

  production:
    compose:
      app_services:
        - web
        - queues
        - scheduler
        - ws
    cleanup:
      min_free_kb: 20971520
    health:
      retries: 10
      delay: 6
```

## Top-Level Keys

`schema_version`
: Required. Must be `1`.

`app`
: Required. Identifies the Laravel app and remote directory.

`repo`
: Required. Defines the Git ref and remote used by VM-side checkout.

`compose`
: Required. Defines Compose project, files, build service, and services to roll out.

`build`
: Required. Currently supports VM-side builds only.

`cleanup`
: Optional. Controls disk-pressure cleanup.

`database`
: Optional. Controls app migrations during rollout, not DB VM provisioning.

`health`
: Required. Defines post-rollout health check.

`secrets`
: Required. Defines provider, sources, merge order, and `.env` rendering.

`environments`
: Optional. A map of environment-specific partial manifest overrides keyed by `app_env`.

## `app`

```yaml
app:
  name: demo-laravel
  type: laravel
  app_dir: /srv/demo-laravel/current
  env: "{{ app_env }}"
```

`name`
: Human-readable app name used in logs and docs.

`type`
: Must be `laravel`.

`app_dir`
: Absolute path to the app checkout on each app VM.

`env`
: Logical environment name. Usually `{{ app_env }}`.

## `repo`

```yaml
repo:
  git_ref: "{{ app_env }}"
  remote: origin
  clean: true
  url: git@github.com:your-github-org/demo-laravel.git
```

`git_ref`
: Branch, tag, or SHA to deploy. Commonly `staging` or `production`.

`remote`
: Git remote name on the VM checkout. Usually `origin`.

`clean`
: If `true`, deployment resets hard to `remote/git_ref`. If `false`, deployment uses `git pull --ff-only`.

`url`
: Optional. Used by bootstrap when cloning or repairing the checkout. It should be private-app-specific.

## `compose`

```yaml
compose:
  project_name: demo_laravel
  files:
    - docker-compose.yml
    - production.docker-compose.yml
  build_service: web
  app_services:
    - web
    - queues
    - scheduler
  queue_service: queues
  nginx_service: nginx
```

`project_name`
: Docker Compose project name.

`files`
: Ordered Compose files relative to `app.app_dir`. Files must exist after checkout.

`build_service`
: Service built on the VM and used for migrations.

`app_services`
: Services created/recreated during every normal app rollout. This is an explicit allowlist; services omitted here are not touched by recurring deploys.

`one_time_services`
: Optional services created only when their Compose container does not exist yet. Use this for single-VM staging dependencies such as `postgres` and `redis` when first deploy should create them but later app deploys should not recreate them.

`queue_service`
: Optional service used for `horizon:terminate` and `queue:restart`.

`nginx_service`
: Optional service name for app-owned Nginx containers.

### Recurring Versus One-Time Services

For single-VM staging, keep app services recurring and infrastructure dependencies one-time:

```yaml
environments:
  staging:
    compose:
      app_services:
        - web
        - queues
        - scheduler
      one_time_services:
        - postgres
        - redis
```

On first staging deploy, missing `postgres` and `redis` containers are created with `docker compose up -d --no-recreate`. On later deploys, if those containers already exist, including stopped containers, deploy skips them.

For production, omit DB/Redis from both lists unless the app intentionally owns those services:

```yaml
environments:
  production:
    compose:
      app_services:
        - web
        - queues
        - scheduler
        - ws
```

If you want deploys to also restart or repair staging DB/Redis whenever needed, put them in `app_services` instead of `one_time_services`. Do not put the same service in both lists.

## `build`

```yaml
build:
  mode: per_vm
  preserve_cache: true
  progress: plain
```

`mode`
: Must be `per_vm`. CI-built images and private-LAN image distribution are not the default path.

`preserve_cache`
: Documents the expected cache policy. Deploy cleanup should not destroy build cache unless explicitly configured.

`progress`
: Compose build progress mode: `auto`, `plain`, `tty`, or `quiet`.

## `cleanup`

```yaml
cleanup:
  policy: disk_pressure_only
  min_free_kb: 10485760
  prune_build_cache: false
  scheduled_deep_cleanup: false
```

`policy`
: `disk_pressure_only` or `never`.

`min_free_kb`
: Free-space threshold for disk-pressure cleanup.

`prune_build_cache`
: If `false`, Docker build cache is preserved during cleanup.

`scheduled_deep_cleanup`
: Documentation flag for app operations. It is not part of the normal deploy path.

## `database`

```yaml
database:
  migrations:
    enabled: true
    run_once: true
    command: php artisan migrate --force
```

This section controls Laravel migrations only. DB VM provisioning is handled by separate one-time workflows.

`enabled`
: Run migrations during deploy.

`run_once`
: Run migrations once across a serial multi-VM rollout.

`command`
: Migration command executed inside `compose.build_service`.

## `health`

```yaml
health:
  type: http
  url: http://127.0.0.1:8080/health
  retries: 6
  delay: 5
```

HTTP health checks require `url`. Command health checks use `command` instead:

```yaml
health:
  type: command
  command: docker compose ps
```

`retries` and `delay` control retry behavior.

## `secrets`

Secret providers normalize source values into classes:

- `app`
- `deploy`
- `db`
- `redis`
- `monitoring`

Only configured render classes, normally `app`, are written to Laravel `.env`.

### SOPS + Age

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
    - name: app_deploy
      file: deploy/secrets/{{ app_env }}.deploy.sops.yml
      class: deploy
```

Each SOPS source needs `name`, `file`, and `class`.

### Infisical Cloud Or Self-Hosted

```yaml
secrets:
  provider: infisical_self_hosted
  url: https://secrets.internal.invalid
  auth:
    method: oidc
  sources:
    - name: shared_runtime
      project_id: demo-shared
      env_slug: "{{ app_env }}"
      path: /app
      class: app
```

Each Infisical source needs `name`, `project_id`, `env_slug`, `path`, and `class`. `url` is required for self-hosted examples and omitted for Infisical Cloud when the CLI default is used.

### Merge Order

```yaml
merge:
  override_order:
    - shared_runtime
    - app_runtime
    - app_deploy
  fail_on_duplicate_keys: false
```

Sources are merged in order. Later sources override earlier sources unless duplicate-key failure is enabled.

`override_order` must contain each source name exactly once.

### `.env` Rendering

```yaml
render:
  app_env_file:
    enabled: true
    target: .env
    mode: "0600"
    include_classes:
      - app
```

`target`
: Path relative to `app.app_dir`, unless absolute.

`include_classes`
: Secret classes to render. Keep this to `app` unless there is a deliberate reason to include another runtime class.

## What Does Not Belong In The Manifest

- Plaintext secret values.
- SSH private keys.
- Age private keys.
- Real public/private topology in this public kit.
- App `.env` content.
- Regular production DB/Redis provisioning instructions.

Private inventory is resolved by workflow inputs/secrets, not by the manifest itself.
