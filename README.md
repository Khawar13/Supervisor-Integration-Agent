# Project Info: Multi-Agent Supervisor Web App

This file captures the original system prompt describing what we are building and how we are building it.

## What We Are Building

- A web application with a Supervisor LLM that receives user queries, selects worker agents (tools), orchestrates them, and returns a unified answer.
- Worker agents expose a common JSON handshake and can be HTTP or CLI services.
- A minimal frontend sends queries and can show debug info (agents called and intermediate results).

## Architecture (From the Prompt)

- Language: Python 3, Framework: FastAPI, Server: Uvicorn.
- Frontend: simple HTML/JS (now React) via FastAPI route; fetch POST to `/api/query`.
- LLM: OpenRouter API with Google Gemini (env `OPENROUTER_API_KEY`).
- Data: in-memory/JSON agent registry; no DB required.
- Single entrypoint (`main.py`) wiring to modular app package.

## Agent Registry

- Each agent has `name`, `description`, `intents`, `type` (http/cli), and connection details (`endpoint` or `command`, `healthcheck`, `timeout_ms`).
- Used for both LLM planning (capability briefing) and actual invocation.

## JSON Contracts

- Frontend → Supervisor (`/api/query`): `{ query, user_id?, options { debug }, conversation_id? }`.
- Supervisor → Worker (request): `{ request_id, agent_name, intent, input { text, metadata }, context { user_id, conversation_id?, timestamp } }`.
- Worker → Supervisor (response): success `{ request_id, agent_name, status: success, output { result, confidence?, details? }, error: null }`; error `{ status: error, output: null, error { type, message } }`.
- Supervisor → Frontend: `{ answer, used_agents[{ name, intent, status }], intermediate_results { step_n: full worker response }, error }`.

## Supervisor Flow

1. Receive user query.
2. Load registry.
3. LLM planner selects agents/steps (plan with `step_id`, `agent`, `intent`, `input_source`).
4. Execute plan: resolve inputs (user_query or prior step output), call agents, collect responses.
5. Compose final answer via LLM (fallback stitching if unavailable).
6. Return structured response; surface errors if planning/execution fails.

## Planner Details

- Prompt includes user query and summarized agents (name/description/intents).
- Expects JSON plan: `steps: [{ step_id, agent, intent, input_source }]` with `input_source` in {`user_query`, `step:X.output.result`}.
- Fallback plan if LLM output invalid or key missing.

## Agent Caller

- Builds handshake request and performs HTTP POST with timeout/error handling. httpx is required for real calls; if httpx is missing or the endpoint fails, the supervisor returns a structured error.
- No built-in simulation is active; tests can monkeypatch `call_agent` to stub agents.
- Validates responses; status is `success` or `error` with mutually exclusive output/error.

## Frontend Requirements

- UI: textarea for query, debug checkbox, submit button.
- Sends POST `/api/query`; displays answer and (when debug) `used_agents` and `intermediate_results`.
- Routes: `GET /` (UI), `POST /api/query` (full flow), `GET /health` (status ok), optional `/agents` list.

## Implementation Notes

- Keep code clear and well-commented; educational intent.
- Default behavior attempts real agent calls; if endpoints are unreachable or httpx is absent, errors are surfaced to the UI/tests. Use monkeypatching to simulate agents in tests.
- Add new worker by updating registry and providing endpoint/command; planner auto-considers via description/intents.

## Setup and Running

### 1. Install Dependencies

```bash
pip install fastapi uvicorn openai httpx
```

### 2. Configure Environment Variables

Copy the example environment file and add your API key:

```bash
cp .env.example .env
```

Edit `.env` and set your OpenRouter API key:

```
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
OPENROUTER_MODEL=google/gemini-2.5-flash-lite
```

Get your OpenRouter API key from: https://openrouter.ai/keys

### 3. Run the Application

```bash
uvicorn main:app --reload
```

Open http://localhost:8000/ in your browser.

### 4. Alternative: Export Environment Variables Directly

```bash
export OPENROUTER_API_KEY="your-api-key-here"
uvicorn main:app --reload
```

## Running Screenshot

<img width="2058" height="3168" alt="Supervisor Frontend" src="https://github.com/user-attachments/assets/f879d1ba-9cc2-49fe-8825-cbeba037e25c" />
