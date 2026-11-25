# NewMotion

NewMotion is being prepared as a clean, domain-neutral application foundation.

## Architecture direction

Start with a **modular monolith**: explicit domain boundaries, application use cases, replaceable infrastructure adapters, and thin interfaces. Split services only when scale, deployment, or ownership creates a concrete need.

## Current status

- [x] Repository baseline inspected.
- [x] Initial architecture and migration boundaries documented.
- [ ] Product domain and primary user workflow confirmed.
- [ ] Runtime, language, and deployment target selected.
- [ ] First vertical slice implemented and tested.

No application runtime or third-party dependency has been introduced yet. This is intentional: the source repository contains video-specific workflows and integrations that should not be copied into a product whose domain is not yet defined.

## Documents

- [Architecture overview](docs/architecture/overview.md)
- [Adoption map from mesin-video](docs/architecture/adoption-map.md)
- [ADR 0001 — Modular monolith](docs/decisions/0001-modular-monolith.md)

## Security

Never commit credentials, API keys, access tokens, private user data, production exports, or local environment files. Use the target platform's secret manager and provide only sanitized examples in the repository.
