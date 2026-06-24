# Decisions

## Public Generic Kit

Decision: keep this repository public and generic.

Why:

- App repos can live under different users or organizations.
- Public reusable templates avoid copying deployment folders between apps.
- Public code forces examples to use fake values and keeps private topology elsewhere.

## Tiny App Workflow

Decision: app repos keep a small workflow that calls a versioned deploy-kit workflow.

Why:

- The app repo owns branch triggers and environment protection.
- The kit owns reusable deployment mechanics.
- Updating the kit does not require copying a full workflow into every app.

## VM-Side Docker Builds

Decision: default to VM-side builds with preserved Docker cache.

Why:

- Keeps CI minutes low.
- Avoids requiring a private registry for the default path.
- Matches simple VM deployments where production deploys are less frequent than staging deploys.

## Disk Cleanup

Decision: default cleanup policy is `disk_pressure_only`.

Why:

- Routine pruning destroys useful build cache.
- Never pruning can fill disks.
- Disk-pressure cleanup preserves speed until free space is low.

## Secret Providers

Decision: use a provider interface with SOPS + age, Infisical Cloud, and Infisical self-hosted as supported shapes.

Why:

- SOPS is easy to test without running a server.
- Infisical provides a managed or self-hosted UI and audit workflow.
- Multiple sources allow shared and app-specific secrets without assuming cross-project imports.

## App Secrets Vs Deploy Secrets

Decision: render only app runtime secrets into `.env`.

Why:

- SSH keys, deploy tokens, bootstrap credentials, and provider tokens are control-plane data.
- Application containers should not receive credentials they do not need.

