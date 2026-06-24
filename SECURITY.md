# Security Policy

This repository is public. Do not commit real secrets, real domains, real IP addresses, internal hostnames, private inventories, SSH keys, age private keys, API tokens, database passwords, or application `.env` files.

## Reporting A Security Issue

If this project is hosted on GitHub, use a private security advisory when available. If a private advisory is not available, contact the maintainer through a non-public channel before opening a public issue.

Use `security-contact@maintainer.invalid` only as a placeholder in forks until the project owner publishes a real contact path.

## Secret Handling Rules

- App runtime secrets belong in the configured provider path or encrypted SOPS files.
- Deployment/control-plane secrets belong in GitHub environment secrets, a deploy secret source, or another trusted control plane.
- Only app runtime classes should be rendered into Laravel `.env`.
- Secret-fetching and rendering tasks must use no-log behavior when implemented.
- Example values in this repository must stay fake and obviously non-production.

## Supported Versions

No stable release has been published yet. Pin app repositories to a tagged release after the first public release is cut.

