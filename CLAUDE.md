# ai-generated: 100% - Claude Code drafted the policy and service guardrails, and the repo owner reviewed them.

# Service Desk Working Rule

This repository follows the approved ITSM decisions and the explicit lab constraints. Do not broaden the scope beyond the ticket lifecycle, SLA, and API contract in the core specification.

- Keep the ticket state machine strict.
- Preserve audit integrity for closed records.
- Respect the C1/C2/C3 decision values in DECISIONS.md.
- Prefer small, deterministic implementations.
