VENV_BIN := .venv/bin
PYTHON ?= $(if $(wildcard $(VENV_BIN)/python),$(VENV_BIN)/python,python3)
YAMLLINT ?= $(if $(wildcard $(VENV_BIN)/yamllint),$(VENV_BIN)/yamllint,yamllint)
ANSIBLE_LINT ?= $(if $(wildcard $(VENV_BIN)/ansible-lint),$(VENV_BIN)/ansible-lint,ansible-lint)
ANSIBLE_PLAYBOOK ?= $(if $(wildcard $(VENV_BIN)/ansible-playbook),$(VENV_BIN)/ansible-playbook,ansible-playbook)
SHELLCHECK ?= shellcheck
ACTIONLINT ?= actionlint
ANSIBLE_ENV := ANSIBLE_CONFIG=ansible/ansible.cfg ANSIBLE_ROLES_PATH=ansible/roles ANSIBLE_FILTER_PLUGINS=ansible/filter_plugins

.PHONY: dev-install test verify lint ansible-syntax workflow-lint compose-config container-verify container-test integration-docker

dev-install:
	@if command -v uv >/dev/null 2>&1; then \
		uv venv .venv; \
		uv pip install --python .venv/bin/python -r requirements-dev.txt; \
	else \
		python3 -m venv .venv; \
		.venv/bin/python -m pip install --upgrade pip; \
		.venv/bin/python -m pip install -r requirements-dev.txt; \
	fi

test:
	$(PYTHON) -m unittest discover -s tests
	$(PYTHON) -m py_compile ansible/filter_plugins/ldk_secrets.py ansible/filter_plugins/ldk_manifest.py bin/render-dotenv bin/resolve-inventory bin/check-workflow-version
	bash -n bin/ldk bin/validate-manifest

verify:
	bin/verify

lint:
	$(YAMLLINT) .
	$(ANSIBLE_ENV) $(ANSIBLE_LINT) ansible
	$(SHELLCHECK) bin/ldk bin/validate-manifest bin/verify tests/integration/ubuntu24/run.sh

workflow-lint:
	$(ACTIONLINT)

container-verify: test lint workflow-lint ansible-syntax

ansible-syntax:
	$(ANSIBLE_ENV) $(ANSIBLE_PLAYBOOK) --syntax-check -i examples/inventories/staging-single-vm.ini ansible/playbooks/validate-manifest.yml -e manifest_path=examples/app-repo/deploy/manifest.yml -e app_env=staging
	$(ANSIBLE_ENV) $(ANSIBLE_PLAYBOOK) --syntax-check -i examples/inventories/staging-single-vm.ini ansible/playbooks/laravel-vm-deploy.yml -e manifest_path=examples/app-repo/deploy/manifest.yml -e app_env=staging
	$(ANSIBLE_ENV) $(ANSIBLE_PLAYBOOK) --syntax-check -i examples/inventories/staging-single-vm.ini ansible/playbooks/refresh-secrets.yml -e manifest_path=examples/app-repo/deploy/manifest.yml -e app_env=staging
	$(ANSIBLE_ENV) $(ANSIBLE_PLAYBOOK) --syntax-check -i examples/inventories/staging-single-vm.ini ansible/playbooks/bootstrap-host.yml -e manifest_path=examples/app-repo/deploy/manifest.yml -e app_env=staging
	$(ANSIBLE_ENV) $(ANSIBLE_PLAYBOOK) --syntax-check -i examples/inventories/production-multi-vm.ini ansible/playbooks/provision-postgres.yml -e manifest_path=examples/app-repo/deploy/manifest.yml -e app_env=production
	$(ANSIBLE_ENV) $(ANSIBLE_PLAYBOOK) --syntax-check -i examples/inventories/production-multi-vm.ini ansible/playbooks/provision-redis.yml -e manifest_path=examples/app-repo/deploy/manifest.yml -e app_env=production

compose-config:
	@created=0; \
	if [ ! -f examples/app-repo/.env ]; then created=1; touch examples/app-repo/.env; fi; \
	docker compose -f examples/app-repo/docker-compose.yml -f examples/app-repo/staging.docker-compose.yml config --quiet; \
	status=$$?; \
	if [ $$created -eq 1 ]; then rm -f examples/app-repo/.env; fi; \
	exit $$status
	@created=0; \
	if [ ! -f examples/app-repo/.env ]; then created=1; touch examples/app-repo/.env; fi; \
	docker compose -f examples/app-repo/docker-compose.yml -f examples/app-repo/production.docker-compose.yml config --quiet; \
	status=$$?; \
	if [ $$created -eq 1 ]; then rm -f examples/app-repo/.env; fi; \
	exit $$status

container-test:
	docker compose -f docker-compose.test.yml run --rm kit-tests

integration-docker:
	@status=0; \
	docker compose -f tests/integration/ubuntu24/docker-compose.yml up --build --abort-on-container-exit --exit-code-from control || status=$$?; \
	docker compose -f tests/integration/ubuntu24/docker-compose.yml down -v --remove-orphans; \
	exit $$status
