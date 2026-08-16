import json
import sqlite3

from fastapi.testclient import TestClient

import backend.main as main

client = TestClient(main.app)


def new_session(scenario_id: str = "photo-cd-drift") -> str:
    response = client.post("/api/sessions", params={"scenario_id": scenario_id})
    assert response.status_code == 200
    return response.json()["id"]


def new_seeded_session(seed: int, scenario_id: str = "photo-cd-drift") -> dict:
    response = client.post("/api/sessions", params={"scenario_id": scenario_id, "seed": seed})
    assert response.status_code == 200
    return response.json()


def decide(session_id: str, stage: str, choice: str, payload=None):
    return client.post(
        f"/api/sessions/{session_id}/decisions",
        json={"stage": stage, "choice": choice, "payload": payload or {}},
    )


def test_controlled_path_solves_scenario():
    session_id = new_session()
    assert decide(session_id, "incident", "hold").status_code == 200
    assert decide(session_id, "coach", "modify", {"prompt": "경쟁 가설 세 개와 반증 증거를 질문해줘.", "human_check": "교재 원문과 Tool별 데이터로 다시 확인한다.", "llm_response": "경쟁 가설과 반증 증거를 구분하고 최소 측정부터 확인하세요.", "llm_model": "Gemini"}).status_code == 200
    assert decide(session_id, "data", "distribution").status_code == 200
    assert decide(session_id, "experiment", "screening", {"repeats": 3}).status_code == 200
    analysis = decide(session_id, "analysis", "select", {"tools": ["optical", "sem"]})
    assert analysis.status_code == 200
    result = decide(session_id, "validation", "controlled", {"metrics": {"baseline": 0.62, "holdout": 0.78, "direction": "higher"}})
    assert result.status_code == 200
    state = result.json()["state"]
    assert state["completed"] is True
    assert state["verdict"] == "시나리오 해결 · 입력 증거 기준"
    report = client.post(
        f"/api/sessions/{session_id}/report",
        json={"opinion": "평균값보다 위치별 분포를 먼저 보고 AI 제안을 측정 원리와 대조해야 한다고 판단했다.", "presenter": "테스트 지원자", "target_role": "공정기술"},
    )
    assert report.status_code == 200
    assert "virtual-fab-interview-slides.html" in report.headers["content-disposition"]
    assert "data:image/svg+xml;base64" in report.text
    assert "테스트 지원자" in report.text
    assert "Gemini" in report.text
    assert "경쟁 가설 세 개와 반증 증거" in report.text
    assert "최소 측정부터 확인" in report.text


def test_catalog_and_all_scenarios_create_independent_sessions():
    catalog = client.get("/api/scenarios")
    assert catalog.status_code == 200
    items = catalog.json()
    assert [item["process"] for item in items] == ["PHOTO", "DRY ETCH", "SPUTTER", "CVD", "CMP", "DEVICE"]
    for item in items:
        scenario = client.get(f"/api/scenario/{item['id']}")
        assert scenario.status_code == 200
        session = client.post("/api/sessions", params={"scenario_id": item["id"]})
        assert session.status_code == 200
        assert session.json()["scenario_id"] == item["id"]
        assert session.json()["time_left"] == scenario.json()["limits"]["time"]


def test_analysis_budget_is_enforced():
    session_id = new_session()
    decide(session_id, "incident", "hold")
    decide(session_id, "coach", "modify", {"prompt": "경쟁 가설 세 개와 반증 증거를 질문해줘.", "human_check": "교재 원문과 데이터로 다시 확인한다.", "llm_response": "경쟁 가설과 반증 증거를 구분하고 최소 측정부터 확인하세요."})
    decide(session_id, "data", "distribution")
    decide(session_id, "experiment", "screening", {"repeats": 3})
    response = decide(session_id, "analysis", "select", {"tools": ["tem", "fib", "xps"]})
    assert response.status_code == 422


def test_out_of_order_decision_is_rejected():
    session_id = new_session()
    response = decide(session_id, "data", "distribution")
    assert response.status_code == 409


def test_deepseek_response_includes_model_and_usage(monkeypatch):
    session_id = new_session()
    decide(session_id, "incident", "hold")
    monkeypatch.setattr(main, "deepseek_generate", lambda prompt, user_id, scenario: {
        "response": "Dose, 현상 균일도, 계측 편향 가설을 위치별 분포와 교차 측정으로 반증하세요.",
        "model": "deepseek-v4-flash",
        "usage": {"prompt_tokens": 120, "completion_tokens": 80, "total_tokens": 200},
    })
    response = client.post(
        f"/api/sessions/{session_id}/deepseek",
        json={"prompt": "Photo CD edge 산포의 경쟁 가설과 최소 반증 증거를 제안해줘."},
    )
    assert response.status_code == 200
    assert response.json()["model"] == "deepseek-v4-flash"
    assert response.json()["usage"]["total_tokens"] == 200


def test_session_is_persisted_in_sqlite():
    session_id = new_session()
    decide(session_id, "incident", "hold")
    restored = main.load_session(session_id)
    assert restored is not None
    assert restored.stage_index == 1
    assert restored.history[0]["choice"] == "hold"


def test_seeded_runs_are_reproducible_and_auditable():
    first = new_seeded_session(20260816)
    second = new_seeded_session(20260816)

    assert first["id"] != second["id"]
    assert first["scenario_version"] == main.PHOTO_SCENARIO["version"]
    assert first["seed"] == second["seed"] == 20260816

    first_result = decide(first["id"], "incident", "hold").json()["state"]
    second_result = decide(second["id"], "incident", "hold").json()["state"]
    assert first_result["score"] == second_result["score"] == 10
    assert first_result["evidence"] == second_result["evidence"]
    assert first_result["history"] == second_result["history"]
    assert first_result["history"][0]["decision_no"] == 1
    assert first_result["history"][0]["scenario_version"] == main.PHOTO_SCENARIO["version"]
    assert first_result["history"][0]["seed"] == 20260816


def test_restart_keeps_seed_for_path_comparison():
    state = new_seeded_session(77)
    decide(state["id"], "incident", "hold")
    restarted = client.post(f"/api/sessions/{state['id']}/restart")
    assert restarted.status_code == 200
    assert restarted.json()["seed"] == 77
    assert restarted.json()["scenario_version"] == main.PHOTO_SCENARIO["version"]
    assert restarted.json()["history"] == []


def test_legacy_session_gets_a_stable_seed_and_current_version():
    session_id = "00000000-0000-0000-0000-000000000123"
    legacy_state = {"id": session_id, "scenario_id": "photo-cd-drift", "budget": 80, "time_left": 60}
    with sqlite3.connect(main.DB_PATH) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO sessions(id, state_json, updated_at) VALUES(?, ?, ?)",
            (session_id, json.dumps(legacy_state), 2_000_000_000),
        )

    first = main.load_session(session_id)
    second = main.load_session(session_id)
    assert first is not None and second is not None
    assert first.seed == second.seed
    assert first.scenario_version == main.PHOTO_SCENARIO["version"]
