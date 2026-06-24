#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/workspace"
TARGET="ubuntu-app"
SSH_OPTS=(
  -o StrictHostKeyChecking=no
  -o UserKnownHostsFile=/dev/null
)

export ANSIBLE_CONFIG="$ROOT_DIR/ansible/ansible.cfg"
export ANSIBLE_ROLES_PATH="$ROOT_DIR/ansible/roles"
export ANSIBLE_FILTER_PLUGINS="$ROOT_DIR/ansible/filter_plugins"

wait_for_ssh() {
  for _ in $(seq 1 60); do
    if sshpass -p ldk ssh "${SSH_OPTS[@]}" "root@$TARGET" "true" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "Timed out waiting for SSH target" >&2
  return 1
}

seed_repo() {
  sshpass -p ldk ssh "${SSH_OPTS[@]}" "root@$TARGET" "bash -s" <<'REMOTE'
set -euo pipefail

rm -rf /srv/ldk-integration
mkdir -p /srv/ldk-integration/seed
cd /srv/ldk-integration/seed

cat > Dockerfile <<'EOF'
FROM python:3.12-alpine
WORKDIR /app
RUN printf 'ok\n' > index.html
CMD ["python", "-m", "http.server", "8080"]
EOF

cat > docker-compose.yml <<'EOF'
services:
  web:
    build:
      context: .
    image: ldk-integration-web:local
    command: ["python", "-m", "http.server", "8080"]
    env_file:
      - .env
EOF

cat > staging.docker-compose.yml <<'EOF'
services:
  redis:
    image: alpine:3.20
    command: ["sh", "-c", "sleep 3600"]
EOF

git init --initial-branch=staging
git config user.email ldk@example.invalid
git config user.name "Laravel Deploy Kit"
git add .
git commit -m "seed integration app"
git clone --bare . /srv/ldk-integration/source.git
git clone /srv/ldk-integration/source.git /srv/ldk-integration/current
cd /srv/ldk-integration/current
git remote set-url origin /srv/ldk-integration/source.git
REMOTE
}

cleanup_remote_compose() {
  sshpass -p ldk ssh "${SSH_OPTS[@]}" "root@$TARGET" \
    "cd /srv/ldk-integration/current 2>/dev/null && docker compose --project-name ldk_integration -f docker-compose.yml -f staging.docker-compose.yml down -v --remove-orphans || true" \
    >/dev/null 2>&1 || true
}

main() {
  wait_for_ssh
  seed_repo
  trap cleanup_remote_compose EXIT

  ansible-playbook \
    -i "$ROOT_DIR/tests/integration/ubuntu24/inventory.ini" \
    "$ROOT_DIR/ansible/playbooks/laravel-vm-deploy.yml" \
    -e "manifest_path=$ROOT_DIR/tests/integration/ubuntu24/manifest.yml" \
    -e "app_env=staging" \
    -e "ldk_sops_binary=$ROOT_DIR/tests/integration/ubuntu24/fake-sops"
}

main "$@"
