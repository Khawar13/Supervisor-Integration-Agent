# Agent Modification Guide

This guide explains how teams can add or update worker agents so the supervisor can plan, call, and reason about them reliably.

## 1) Add the agent to the registry
- File: `app/registry.py`
- Create an `AgentMetadata` entry with:
  - `name`: unique `snake_case_agent` string used in plans and responses.
  - `description`: 1–2 sentences in plain English so the LLM planner can match intents.
  - `intents`: list of supported intent strings (namespace style, e.g., `summary.create`).
  - `type`: `"http"` (preferred) or `"cli"`.
  - Connection details:
    - HTTP: `endpoint`, `healthcheck`, `timeout_ms` (milliseconds).
    - CLI: `command`, `healthcheck`, `timeout_ms`.
- Keep names/intent strings stable; planner and executor reference them directly.

## 2) Implement the worker handshake
- Request (Supervisor → Worker):
  ```json
  {
    "request_id": "uuid",
    "agent_name": "your_agent",
    "intent": "your.intent",
    "input": { "text": "payload", "metadata": { "language": "en", "extra": {} } },
    "context": { "user_id": "optional", "conversation_id": "optional", "timestamp": "ISO-8601" }
  }
  ```
- Response (Worker → Supervisor):
  - Success:
    ```json
    { "request_id": "same", "agent_name": "your_agent", "status": "success", "output": { "result": "...", "confidence": 0.9, "details": "optional" }, "error": null }
    ```
  - Error:
    ```json
    { "request_id": "same", "agent_name": "your_agent", "status": "error", "output": null, "error": { "type": "runtime_error", "message": "explanation" } }
    ```
- Hard rules: `status` ∈ {`success`,`error`}; exactly one of `output` or `error` is non-null; `request_id` must echo the request.

## 3) Make the agent planner-friendly
- Keep `description` and `intents` clear and specific; the planner prompt includes both.
- If the agent has prerequisites (e.g., needs a summary first), note it in the description.
- Avoid overlapping names/intents across agents to reduce tool-selection ambiguity.

## 4) Enable/replace simulation
- The app does not ship with built-in simulation; `call_agent` makes real HTTP calls and returns structured errors if httpx is missing or the endpoint fails.
- For offline demos or tests, monkeypatch `call_agent` to return an `AgentResponse` stub for your agent.
- When going live, ensure `agent_meta.endpoint` or `command` is set and reachable; timeouts are honored per-agent.

## 5) Test the integration
- Add tests that:
  - Call `/agents` to confirm the new entry is exposed.
- Exercise `/api/query` with a prompt that should route to the new intent and assert handshake shape and status handling.
  - Validate error cases (non-200 HTTP, bad JSON) return `status=error` with `error.type` set.

## 6) Scope & safety considerations
- The supervisor should only plan within registered agents/intents; keep descriptions narrow to avoid out-of-scope use.
- Workers should reject unsupported intents and return an `error` with a clear `message`.
- Consider input validation inside workers (length limits, allowed fields) to avoid over-broad processing.

## 7) Quick checklist
- [ ] Registry entry added in `app/registry.py` (name, description, intents, type, endpoint/command, timeout).
- [ ] Worker implements the handshake contract and echoes `request_id`.
- [ ] Optional test stub added via monkeypatching `call_agent` for offline demos.
- [ ] Tests added/updated for `/agents` and `/api/query` routing to the new agent.
- [ ] Any new config keys mirrored in `.env.example` (if applicable).
