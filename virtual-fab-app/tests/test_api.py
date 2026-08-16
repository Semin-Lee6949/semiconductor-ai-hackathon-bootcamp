from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def new_session() -> str:
    response = client.post("/api/sessions")
    assert response.status_code == 200
    return response.json()["id"]


def decide(session_id: str, stage: str, choice: str, payload=None):
    return client.post(
        f"/api/sessions/{session_id}/decisions",
        json={"stage": stage, "choice": choice, "payload": payload or {}},
    )


def test_controlled_path_solves_scenario():
    session_id = new_session()
    assert decide(session_id, "incident", "hold").status_code == 200
    assert decide(session_id, "coach", "modify", {"prompt": "경쟁 가설 세 개와 반증 증거를 질문해줘.", "human_check": "교재 원문과 Tool별 데이터로 다시 확인한다."}).status_code == 200
    assert decide(session_id, "data", "distribution").status_code == 200
    assert decide(session_id, "experiment", "screening", {"repeats": 3}).status_code == 200
    analysis = decide(session_id, "analysis", "select", {"tools": ["optical", "sem"]})
    assert analysis.status_code == 200
    result = decide(session_id, "validation", "controlled", {"metrics": {"baseline": 0.62, "holdout": 0.78, "direction": "higher"}})
    assert result.status_code == 200
    state = result.json()["state"]
    assert state["completed"] is True
    assert state["verdict"] == "시나리오 해결 · 입력 증거 기준"


def test_analysis_budget_is_enforced():
    session_id = new_session()
    decide(session_id, "incident", "hold")
    decide(session_id, "coach", "modify", {"prompt": "경쟁 가설 세 개와 반증 증거를 질문해줘.", "human_check": "교재 원문과 데이터로 다시 확인한다."})
    decide(session_id, "data", "distribution")
    decide(session_id, "experiment", "screening", {"repeats": 3})
    response = decide(session_id, "analysis", "select", {"tools": ["tem", "fib", "xps"]})
    assert response.status_code == 422


def test_out_of_order_decision_is_rejected():
    session_id = new_session()
    response = decide(session_id, "data", "distribution")
    assert response.status_code == 409
