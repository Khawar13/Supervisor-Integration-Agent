# Testing Guide

This project uses `pytest` for API-level checks against the FastAPI supervisor. Tests run in offline mode by default (no OpenAI key needed) by monkeypatching the planner and agent caller; the app itself attempts real HTTP calls if not stubbed.

## How to run
- Install dev deps: `pip install pytest httpx fastapi uvicorn openai` (httpx/openai are used by the app; openai is optional if you stay in fallback mode).
- Run all tests: `pytest -q`
- Run a single file: `pytest tests/test_knowledge_base_builder.py -q`

## What the tests cover
- `tests/test_knowledge_base_builder.py`
  - `/agents` lists `knowledge_base_builder_agent` (registry exposure).
  - Planner monkeypatch forces routing to `knowledge_base_builder_agent`; `/api/query` returns success, used_agents contains the KB agent, and the answer/intermediate results are populated (validates handshake + supervisor flow with stubbed agent output).

## Adding more tests
- Use `fastapi.testclient.TestClient` or `httpx.AsyncClient` to hit `/api/query` and `/agents`.
- Monkeypatch `plan_tools_with_llm` for deterministic routing and `call_agent` for stubbed responses in offline tests.
- Assert the handshake shape: each step should surface `used_agents[*].name/intent/status` and `intermediate_results.step_n` with `status/output/error` per contract.
- When enabling real OpenAI or real agents, add environment-guarded tests (skip if `OPENAI_API_KEY` not set) to verify planner choices and HTTP calls.
