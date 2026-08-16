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


def investigation_payload():
    return {
        "prompt": "CD CSV의 결측과 위치별 분포를 어떤 순서로 비교해야 하는지 알려줘.",
        "human_check": "CSV의 결측 플래그와 Lot·Tool·위치별 분포를 직접 계산해 AI 답변과 대조한다.",
        "llm_response": "결측을 분리한 뒤 Lot·Tool 층화와 CENTER·EDGE 분포를 비교하세요.",
        "llm_model": "Gemini",
        "ai_conversation": [{
            "turn_no": 1,
            "question": "CD CSV의 결측과 위치별 분포를 어떤 순서로 비교해야 하는지 알려줘.",
            "response": "결측을 분리한 뒤 Lot·Tool 층화와 CENTER·EDGE 분포를 비교하세요.",
            "provider_label": "Google Gemini",
            "model": "gemini-3.5-flash",
            "usage": {"prompt_tokens": 20, "completion_tokens": 20, "total_tokens": 40},
        }],
    }


def test_controlled_path_solves_scenario():
    session_id = new_session()
    assert decide(session_id, "incident", "hold").status_code == 200
    assert client.get(f"/api/sessions/{session_id}/dataset.csv").status_code == 200
    assert decide(session_id, "investigation", "distribution", investigation_payload()).status_code == 200
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
    assert "CD CSV의 결측과 위치별 분포" in report.text
    assert "CENTER·EDGE 분포" in report.text
    assert "PROCESS KEYWORD MAP" in report.text
    assert "CD" in report.text
    assert "id='total'>11" in report.text


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
        assert len(scenario.json()["keywords"]) == 6
        assert all(keyword["term"] and keyword["meaning"] and keyword["relevance"] for keyword in scenario.json()["keywords"])
        assert scenario.json()["keyword_sources"]


def test_analysis_budget_is_enforced():
    session_id = new_session()
    decide(session_id, "incident", "hold")
    client.get(f"/api/sessions/{session_id}/dataset.csv")
    decide(session_id, "investigation", "distribution", investigation_payload())
    decide(session_id, "experiment", "screening", {"repeats": 3})
    response = decide(session_id, "analysis", "select", {"tools": ["tem", "fib", "xps"]})
    assert response.status_code == 422


def test_out_of_order_decision_is_rejected():
    session_id = new_session()
    response = decide(session_id, "investigation", "distribution", investigation_payload())
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


def test_byok_requires_check_and_never_persists_api_key(monkeypatch):
    session_id = new_session()
    decide(session_id, "incident", "hold")
    api_key = "test-personal-key-abcdefghijklmnopqrstuvwxyz"
    credentials = {"provider": "openai", "model": "gpt-5", "api_key": api_key}

    monkeypatch.setattr(main, "check_llm_connection", lambda provider, model, key: {
        "status": "connected", "provider": provider, "provider_label": "OpenAI", "model": model,
    })
    monkeypatch.setattr(main, "generate_with_byok", lambda provider, model, key, prompt, scenario, state=None: {
        "response": "경쟁 가설과 반증 증거를 분리하고 가장 저비용인 측정부터 확인하세요.",
        "provider": provider,
        "provider_label": "OpenAI",
        "model": model,
        "usage": {"prompt_tokens": 80, "completion_tokens": 40, "total_tokens": 120},
    })

    unverified = client.post(
        f"/api/sessions/{session_id}/llm/generate",
        json={**credentials, "prompt": "CD 경쟁 가설 세 개와 각 가설을 반증할 최소 증거를 제안해줘."},
    )
    assert unverified.status_code == 409

    checked = client.post(f"/api/sessions/{session_id}/llm/check", json=credentials)
    assert checked.status_code == 200
    assert checked.json()["status"] == "connected"

    generated = client.post(
        f"/api/sessions/{session_id}/llm/generate",
        json={**credentials, "prompt": "CD 경쟁 가설 세 개와 각 가설을 반증할 최소 증거를 제안해줘."},
    )
    assert generated.status_code == 200
    assert generated.json()["usage"]["total_tokens"] == 120

    for turn in range(2, 16):
        response = client.post(
            f"/api/sessions/{session_id}/llm/generate",
            json={**credentials, "prompt": f"{turn}번째 질문으로 CD 경쟁 가설과 반증 증거를 다시 비교해줘."},
        )
        assert response.status_code == 200
        assert response.json()["turn_no"] == turn
    limited = client.post(
        f"/api/sessions/{session_id}/llm/generate",
        json={**credentials, "prompt": "CD 경쟁 가설 세 개와 각 가설을 반증할 최소 증거를 다시 비교해줘."},
    )
    assert limited.status_code == 429

    with sqlite3.connect(main.DB_PATH) as connection:
        stored = connection.execute("SELECT state_json FROM sessions WHERE id = ?", (session_id,)).fetchone()[0]
    assert api_key not in stored
    assert "api_key" not in stored
    restored = main.load_session(session_id)
    assert restored.llm_call_count == 15
    assert len(restored.ai_conversation) == 15


def test_byok_rejects_question_without_process_keyword(monkeypatch):
    session_id = new_session()
    decide(session_id, "incident", "hold")
    credentials = {"provider": "gemini", "model": "gemini-3.5-flash", "api_key": "test-personal-key-abcdefghijklmnopqrstuvwxyz"}
    monkeypatch.setattr(main, "check_llm_connection", lambda provider, model, key: {
        "status": "connected", "provider": provider, "provider_label": "Google Gemini", "model": model,
    })
    assert client.post(f"/api/sessions/{session_id}/llm/check", json=credentials).status_code == 200
    response = client.post(
        f"/api/sessions/{session_id}/llm/generate",
        json={**credentials, "prompt": "원인 가설과 다음 행동을 알려줘."},
    )
    assert response.status_code == 422
    assert "공정 핵심 키워드" in response.json()["detail"]


def test_byok_is_blocked_over_public_http():
    public_client = TestClient(main.app, base_url="http://waterfirst.pro")
    session_id = new_session()
    decide(session_id, "incident", "hold")
    response = public_client.post(
        f"/api/sessions/{session_id}/llm/check",
        json={"provider": "gemini", "model": "gemini-3.5-flash", "api_key": "test-personal-key-abcdefghijklmnopqrstuvwxyz"},
    )
    assert response.status_code == 426


def test_dataset_download_is_reproducible_and_required_for_investigation():
    first = new_seeded_session(20260816)
    second = new_seeded_session(20260816)
    decide(first["id"], "incident", "hold")
    decide(second["id"], "incident", "hold")
    blocked = decide(first["id"], "investigation", "distribution", investigation_payload())
    assert blocked.status_code == 422
    first_csv = client.get(f"/api/sessions/{first['id']}/dataset.csv")
    second_csv = client.get(f"/api/sessions/{second['id']}/dataset.csv")
    assert first_csv.status_code == second_csv.status_code == 200
    assert first_csv.text == second_csv.text
    assert "lot_id,tool_id,wafer_zone" in first_csv.text
    completed = decide(first["id"], "investigation", "distribution", investigation_payload())
    assert completed.status_code == 200
    assert completed.json()["state"]["dataset_downloaded"] is True


def test_follow_up_prompt_contains_dataset_and_previous_exchange():
    state = main.SessionState(id="context-test", scenario_id="photo-cd-drift", scenario_version=main.PHOTO_SCENARIO["version"], seed=77)
    state.ai_conversation = [{"question": "결측을 먼저 어떻게 처리해?", "response": "결측 원인을 분리하고 민감도 분석을 하세요."}]
    system, messages = main.coach_messages("그다음 Tool 편중은 어떻게 확인해?", main.PHOTO_SCENARIO, state)
    assert "합성 데이터" in system
    assert "다운로드 데이터는 42행" in messages[0]["content"]
    assert messages[-3]["content"] == "결측을 먼저 어떻게 처리해?"
    assert messages[-2]["role"] == "assistant"
    assert messages[-1]["content"] == "그다음 Tool 편중은 어떻게 확인해?"


def test_all_provider_responses_are_normalized(monkeypatch):
    scenario = main.PHOTO_SCENARIO
    prompt = "경쟁 가설 세 개와 각 가설을 반증할 최소 증거를 제안해줘."
    cases = {
        "openai": ("gpt-5", {"output": [{"type": "message", "content": [{"type": "output_text", "text": "OpenAI 답변"}]}], "usage": {"input_tokens": 11, "output_tokens": 7, "total_tokens": 18}}),
        "anthropic": ("claude-opus-4-6", {"content": [{"type": "text", "text": "Anthropic 답변"}], "usage": {"input_tokens": 12, "output_tokens": 8}}),
        "gemini": ("gemini-3.5-flash", {"candidates": [{"content": {"parts": [{"text": "Gemini 답변"}]}}], "usageMetadata": {"promptTokenCount": 13, "candidatesTokenCount": 9, "totalTokenCount": 22}}),
        "deepseek": ("deepseek-v4-flash", {"choices": [{"message": {"content": "DeepSeek 답변"}}], "usage": {"prompt_tokens": 14, "completion_tokens": 10, "total_tokens": 24}}),
    }
    for provider, (model, provider_response) in cases.items():
        monkeypatch.setattr(main, "provider_json_request", lambda url, headers, body=None, response=provider_response: response)
        result = main.generate_with_byok(provider, model, "test-personal-key-abcdefghijklmnopqrstuvwxyz", prompt, scenario)
        assert result["provider"] == provider
        assert result["model"] == model
        assert result["response"].endswith("답변")
        assert result["usage"]["total_tokens"] > 0
