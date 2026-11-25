# Adoption map: mesin-video → NewMotion

## Source and target observations

- Source repository: `anwar-alzazali/mesin-video`, default branch `main`.
- Target repository: `anwar-alzazali/NewMotion`, default branch `main`.
- At the time of this baseline, NewMotion contained only its initial README.
- The source repository is large and combines video production, rendering, automation, Telegram operations, provider integrations, and Supabase-backed status/billing paths. A full copy would import domain assumptions and operational coupling that may not belong in NewMotion.

## Reuse / adapt / defer

| Source area | Evidence observed on source `main` | Decision for NewMotion |
|---|---|---|
| `otomatis.py` | Coordinates script → image → voice → assembly and supports skipping existing outputs on rerun | Reuse the resumable orchestration principle; do not copy video-specific implementation |
| `papan_buat.py`, `rakit.py` | HTML/SVG or image composition, FFmpeg, Pillow, timed subtitles/audio | Defer until NewMotion is confirmed to need video/media rendering |
| `bot/worker.js` | Telegram webhook, GitHub API, Supabase, Gemini-first/Claude-fallback path | Do not port wholesale; extract only a provider or webhook pattern if a confirmed use case needs it |
| `.github/workflows/*.yml` | Several workflows are manually dispatched; workflows install tools and run scripts | Reuse explicit/manual job triggering where appropriate; avoid push-triggered expensive jobs until CI budget is known |
| `CLAUDE.md` and `docs/ENGINEERING_AUDIT_LOG.md` | Product constraints, reuse-first guidance, audit and verification records | Reuse the discipline of recording decisions, evidence, and test status; do not copy product-specific rules |
| Supabase tables and billing paths | Video-specific tables, storage paths, user credits, and cost logging | Defer; design NewMotion's data model from its own workflows and privacy requirements |

## Important branch/snapshot caution

The source main tree inspected for this baseline does **not** contain the historical paths `papan/task_worker.py`, `papan/task_supervisor.py`, or `papan/sqlite_operation_ledger.py`. Some audit notes describe work from another branch/snapshot. Therefore those components are not considered verified current-main modules and must not be copied until their exact source branch and commit are confirmed.

## Proposed first reusable capabilities

1. **Workflow contract** — versioned input/output schemas and boundary validation.
2. **Orchestration** — explicit step state, progress reporting, and resumability.
3. **Adapter ports** — provider, storage, persistence, and queue implementations behind interfaces.
4. **Safe retries** — distinguish retryable failures from ambiguous external outcomes.
5. **Artifact metadata** — checksum, content type, size, ownership, and retention metadata when files are part of the product.
6. **Operational evidence** — logs with correlation IDs, tests, and honest verification status.

## Not copied

No source code, user content, video assets, character assets, database dumps, credentials, environment values, private keys, or production configuration are copied in this foundation change.
