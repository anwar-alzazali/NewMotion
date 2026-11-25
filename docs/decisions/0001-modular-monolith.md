# ADR 0001: Start with a modular monolith

- Status: Accepted as the initial architecture direction
- Date: 2026-11-25
- Context: NewMotion currently has no established application code or confirmed product workflow. The source project is a large domain-specific automation and media-production repository.
- Decision: Start with one deployable application organized into domain, application, infrastructure, interfaces, and worker boundaries. Keep vendor integrations behind ports/adapters. Add a separate service only when a measurable scaling, isolation, deployment, or ownership requirement justifies it.
- Consequences:
  - Lower initial operational complexity and fewer deployment surfaces.
  - Clear module boundaries allow later extraction without premature microservices.
  - Persistence, queue, runtime, and framework choices remain open until product requirements are known.
  - Cross-module calls should use explicit interfaces; avoid shared mutable global state.
- Revisit when: independent scaling/deployment is required, a module needs a distinct security boundary, or team ownership requires independent release cycles.
