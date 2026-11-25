# NewMotion architecture overview

## Status

Proposed foundation only. The product domain, runtime, deployment target, and first user journey have not yet been confirmed. Do not treat the module names below as implemented code.

## Design goals

1. Keep domain rules independent from frameworks and vendors.
2. Make long-running work observable, resumable, and safe to retry.
3. Validate external input at system boundaries.
4. Keep provider, database, storage, and queue implementations replaceable.
5. Minimize dependencies until a concrete vertical slice requires them.
6. Make tests and operational behavior part of each feature, not a later phase.

## Proposed logical boundaries

| Boundary | Responsibility | Dependency rule |
|---|---|---|
| `domain/` | Entities, value objects, invariants, domain events | Depends on no infrastructure |
| `application/` | Use cases, orchestration, ports/interfaces | Depends on domain |
| `infrastructure/` | Database, queue, storage, AI/provider adapters | Implements application ports |
| `interfaces/` | HTTP/API, CLI, webhooks, user-facing entry points | Calls application use cases |
| `workers/` | Background execution and scheduled/queued jobs | Calls application use cases |
| `tests/` | Unit, integration, contract, and end-to-end tests | Verifies observable behavior |
| `docs/` | Architecture decisions, runbooks, contracts | Explains actual behavior |

A modular monolith may keep these boundaries in one deployable unit. Do not create separate services or databases for every module by default.

## Workflow pattern

For any workflow that performs multiple steps:

1. Accept and validate a versioned input contract.
2. Create a durable operation/task identity.
3. Record state transitions and useful error context.
4. Execute one step at a time through replaceable adapters.
5. Make retry behavior explicit; use idempotency keys for external side effects when supported.
6. Store outputs as artifacts with metadata and integrity checks where needed.
7. Expose status and failure reasons to the caller/operator.

Do not claim exactly-once execution. A timeout after a provider accepts a request can leave the outcome ambiguous. Reconcile with the provider or require an explicit operator decision before resubmitting an ambiguous side effect.

## Data and security boundaries

- Secrets belong in environment injection or a managed secret store, never source control.
- Use least-privilege credentials per integration and environment.
- Validate paths, identifiers, payload size, MIME type, and schema at ingress.
- Keep personal data and production artifacts out of public repositories and logs.
- Apply authorization at the application boundary; do not rely only on UI visibility.
- Use private object storage and expiring URLs for private outputs when applicable.
- Document retention, deletion, and backup behavior before storing user data.

## Quality gates

Every vertical slice should include:
- deterministic unit tests for domain rules;
- integration tests for persistence/provider boundaries;
- contract tests for external payloads;
- syntax/type/lint checks appropriate to the chosen stack;
- a manual acceptance path for user-visible behavior;
- explicit status when a check was not run.

## Runtime and dependency policy

No language, framework, database, queue, or cloud vendor is selected yet. Select them after the product workflow and deployment constraints are confirmed. Prefer standard-library functionality and a small number of maintained dependencies over speculative platform scaffolding.
