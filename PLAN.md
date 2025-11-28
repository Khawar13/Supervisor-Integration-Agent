# Supervisor Agent – Build Plan

## Goals & Scope
- Provide a supervisor that plans, routes, and executes user requests via worker agents using a consistent JSON handshake.
- Support two entry patterns: (1) user picks a worker explicitly, (2) user asks a free-form question and the LLM planner decides.
- Maintain per-session chat memory for context-aware planning/answers.
- Keep the current agent registry names/endpoints intact (including `KnowledgeBaseBuilderAgent`).
- Production-ready posture: observability, error handling, testability, and clear extension paths.

## Target Architecture
- **Backend**: FastAPI, Pydantic (v2), async HTTP (httpx), optional LangGraph wrapper around planning/execution if desired (keep existing interfaces).
- **Frontend**: React (CDN or bundled), served by FastAPI; dashboard shows agents and a conversation panel.
- **Modules (current layout to keep/refine)**:
  - `app/server.py`: routing, request validation, response assembly.
  - `app/planner.py`: LLM planner + heuristics + out-of-scope guardrails.
  - `app/executor.py`: step resolution and orchestration.
  - `app/agent_caller.py`: HTTP handshake to workers; no simulation.
  - `app/answer.py`: answer synthesis/out-of-scope messaging.
  - `app/registry.py`: agent metadata (names/endpoints unchanged).
  - `app/conversation.py`: session memory (consider persistent store later).
  - `app/web.py`: React UI renderers.
  - `tests/`: unit/integration coverage.
- **Data**: in-memory registry; no DB required. Conversation memory currently in-process; plan to swap with Redis/DB for durability.

## Contracts (must stay stable)
- **Frontend → Supervisor** (`/api/query`): `{query, user_id?, conversation_id?, options:{debug}}`.
- **Supervisor → Worker (handshake)**: `{request_id, agent_name, intent, input:{text, metadata}, context:{user_id, conversation_id, timestamp}}`.
- **Worker → Supervisor**: success `{status:"success", output:{result, confidence?, details?}}`; error `{status:"error", error:{type, message}}`.
- **Supervisor → Frontend**: `{answer, used_agents[], intermediate_results, error?}`.

## Planner Requirements
- Deterministic heuristics for well-known intents (KB updates, deadlines, summaries, onboarding, follow-ups, dependencies, email priority, progress).
- LLM path (OpenAI key required): prompt must list agents (name/description/intents) and instruct JSON-only output; if out-of-scope, return `{"steps":[]}`.
- Guardrails: validate JSON, reject unknown agent names/intents, and return empty plan on parse or safety failures.
- Optional LangGraph: encapsulate planning+execution as nodes while preserving existing models; keep HTTP contracts unchanged.

## Execution & Routing
- Resolve `input_source` (`user_query` or prior step output). If missing prior output, fail gracefully with a descriptive error.
- Enforce agent existence via registry lookup; if not found, mark step error.
- HTTP calls only; include timeouts from registry; classify errors as http_error/network_error/config_error.
- Collect `used_agents` and `intermediate_results` for UI/debug.

## Conversation Memory
- Maintain recent turns per `conversation_id` (stored on frontend localStorage).
- Use history to condition planner/answer prompts.
- Add size/TTL limits; future: persist to Redis/DB for multi-instance deployments.

## Observability & Reliability
- Add structured logging (request_id, conversation_id, agent_name, intent, status, latency).
- Health endpoints: supervisor `/health`; optional registry-driven worker health checks.
- Metrics hooks: request rate, planner failures, agent call success/error, latency percentiles.
- Config via environment variables: `OPENAI_API_KEY`, timeouts, log level, CORS.

## Security & Compliance
- Never log secrets or full payloads; redact PII in logs where possible.
- Validate agent name/intent strictly against registry to prevent prompt injection.
- Input size limits on `/api/query`; output size guard before rendering.
- HTTPS assumed in production; enable CORS only for allowed origins.

## Testing Strategy
- Unit: planner heuristics/LLM fallback, agent_caller error paths, executor input resolution.
- Integration: `/api/query` with monkeypatched planner/agent_caller; ensure `KnowledgeBaseBuilderAgent` path works.
- UI smoke: render dashboard, list agents, submit query (mock API).
- Load/reliability (optional): soak tests on planner/executor with mocked agents.

## UX Requirements
- Dashboard lists all worker agents as tools; user can submit free-form query or choose an agent explicitly (add UI affordance).
- Debug mode shows planner choices, timeline, and intermediate JSON.
- Keep current visual design, but ensure accessibility (labels, focus states).

## Rollout & Maintenance
- Keep git clean; ignore `__pycache__` and node_modules (add `.gitignore`).
- Document config in `README`/`PLAN.md`; add run commands (`uvicorn main:app --reload`).
- Future: swap in persistent conversation store; add tracing/metrics backend.
