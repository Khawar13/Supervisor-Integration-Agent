"""
Tests for the Knowledge Base Builder agent integration. These tests keep the
supervisor in offline mode (simulated agents + planner stub) so they can run
without OpenAI or real worker endpoints.
"""
from fastapi.testclient import TestClient

from app.server import app
from app import server as server_module
from app import executor as executor_module
from app.models import AgentResponse, OutputModel, Plan, PlanStep


client = TestClient(app)


def test_agents_endpoint_includes_kb_agent():
    """Ensure the registry exposes the knowledge base builder agent."""
    resp = client.get("/agents")
    assert resp.status_code == 200
    agents = resp.json()
    assert any(a["name"] == "KnowledgeBaseBuilderAgent" for a in agents)


def test_query_routes_to_kb_agent(monkeypatch):
    """
    Force the planner to pick knowledge_base_builder_agent and verify the
    supervisor calls it successfully and returns a usable answer.
    """

    def fake_plan(query: str, registry):
        return Plan(
            steps=[
                PlanStep(
                    step_id=0,
                    agent="KnowledgeBaseBuilderAgent",
                    intent="update_wiki",
                    input_source="user_query",
                )
            ]
        )

    monkeypatch.setattr(server_module, "plan_tools_with_llm", fake_plan)

    payload = {
        "query": "Add today's meeting notes to the knowledge base under Project X",
        "user_id": "tester",
        "options": {"debug": True},
    }

    async def fake_call_agent(agent_meta, intent, text, context):
        return AgentResponse(
            request_id="test",
            agent_name=agent_meta.name,
            status="success",
            output=OutputModel(result="KB updated", confidence=0.95, details="mock"),
        )

    monkeypatch.setattr(executor_module, "call_agent", fake_call_agent)

    resp = client.post("/query", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["used_agents"], "Expected at least one agent call"
    first = data["used_agents"][0]
    assert first["name"] == "KnowledgeBaseBuilderAgent"
    assert first["status"] == "success"

    # Since we rely on simulated output, the answer should include the stubbed result text.
    assert "knowledge base" in data["answer"].lower()
    assert "step_0" in data["intermediate_results"]
