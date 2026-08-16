from __future__ import annotations

from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

APP_DIR = Path(__file__).resolve().parents[1]
DIST_DIR = APP_DIR / "dist"

STAGES = ["incident", "coach", "data", "experiment", "analysis", "validation"]

TOOLS: dict[str, dict[str, Any]] = {
    "optical": {"label": "광학현미경 · Optical CD", "kind": "dimension", "cost": 4, "time": 3, "destructive": False},
    "ellipsometry": {"label": "Ellipsometry", "kind": "dimension", "cost": 8, "time": 5, "destructive": False},
    "sem": {"label": "SEM", "kind": "structure", "cost": 15, "time": 10, "destructive": False},
    "fib": {"label": "FIB–SEM", "kind": "structure", "cost": 35, "time": 25, "destructive": True},
    "tem": {"label": "TEM", "kind": "structure", "cost": 50, "time": 40, "destructive": True},
    "edx": {"label": "EDX", "kind": "chemistry", "cost": 18, "time": 15, "destructive": False},
    "xps": {"label": "XPS", "kind": "chemistry", "cost": 25, "time": 20, "destructive": False},
    "electrical": {"label": "I–V · Vth", "kind": "electrical", "cost": 10, "time": 8, "destructive": False},
}

SCENARIO = {
    "id": "photo-cd-drift",
    "title": "사라진 선폭의 비밀",
    "version": "0.1.0",
    "notice": "교육용 합성 시나리오이며 실제 회사 Recipe·현장 경험을 의미하지 않습니다.",
    "stages": [
        {"id": "incident", "label": "문제 발생", "station": "alert", "brief": "현상 후 wafer edge CD 산포와 결함률이 증가했다. 평균 CD는 규격 안이다."},
        {"id": "coach", "label": "LLM Coach", "station": "coach", "brief": "AI에게 정답이 아니라 경쟁 가설·반증 증거·누락 변수를 질문한다."},
        {"id": "data", "label": "데이터 판단", "station": "data", "brief": "Train 데이터의 결측·중복·단위·Tool 편중과 위치별 분포를 확인한다."},
        {"id": "experiment", "label": "실험계획", "station": "doe", "brief": "대조군·요인·수준·반복·판정기준을 고정한다."},
        {"id": "analysis", "label": "분석 툴", "station": "analysis", "brief": "구조·화학·전기 분석을 비용·시간·정보가치로 선택한다."},
        {"id": "validation", "label": "검증", "station": "validation", "brief": "Holdout과 재실험 결과로 조치 범위를 결정한다."},
    ],
    "tools": TOOLS,
    "required_analysis_kinds": ["dimension", "structure"],
    "limits": {"budget": 80, "time": 60},
}


class DecisionRequest(BaseModel):
    stage: Literal["incident", "coach", "data", "experiment", "analysis", "validation"]
    choice: str = Field(min_length=1, max_length=80)
    payload: dict[str, Any] = Field(default_factory=dict)


class SessionState(BaseModel):
    id: str
    scenario_id: str = "photo-cd-drift"
    stage_index: int = 0
    budget: int = 80
    time_left: int = 60
    score: int = 0
    evidence: list[str] = Field(default_factory=list)
    history: list[dict[str, Any]] = Field(default_factory=list)
    completed: bool = False
    verdict: str | None = None


SESSIONS: dict[str, SessionState] = {}

app = FastAPI(title="Virtual Fab Scenario API", version="0.1.0")


def current_stage(state: SessionState) -> str:
    return STAGES[min(state.stage_index, len(STAGES) - 1)]


def final_verdict(state: SessionState) -> str:
    choices = {item["stage"]: item["choice"] for item in state.history}
    analysis = next((item for item in state.history if item["stage"] == "analysis"), {})
    if choices.get("validation") == "release":
        return "새 결함 발생 · 검증 전 진행"
    if choices.get("experiment") == "immediate":
        return "원인 혼합 · 대조군 부재"
    if analysis and not analysis.get("coverage", False):
        return "증거 공백 · 분석영역 부족"
    if analysis and analysis.get("overanalysis", False):
        return "과잉분석 · 시간·비용 소진"
    if choices.get("data") == "mean_only":
        return "근거 부족 · 평균값 과신"
    return "시나리오 해결 · 입력 증거 기준"


def apply_decision(state: SessionState, request: DecisionRequest) -> dict[str, Any]:
    expected = current_stage(state)
    if state.completed:
        raise HTTPException(409, "이미 완료된 세션입니다.")
    if request.stage != expected:
        raise HTTPException(409, f"현재 단계는 {expected}입니다.")

    record: dict[str, Any] = {"stage": request.stage, "choice": request.choice, "payload": request.payload}
    feedback = "판단이 기록되었습니다."

    if request.stage == "incident":
        if request.choice not in {"hold", "release_by_mean"}:
            raise HTTPException(422, "지원하지 않는 초기 조치입니다.")
        state.score += 10 if request.choice == "hold" else -12
        state.evidence.append("평균과 위치별 분포 분리" if request.choice == "hold" else "평균 CD만 확인")
        feedback = "Lot을 보류하고 관찰과 원인 추정을 분리했습니다." if request.choice == "hold" else "평균은 정상이나 edge 산포가 다음 단계로 넘어갑니다."
    elif request.stage == "coach":
        if len(str(request.payload.get("prompt", ""))) < 20 or len(str(request.payload.get("human_check", ""))) < 20:
            raise HTTPException(422, "LLM 질문과 사람의 검증 계획을 각각 20자 이상 기록하세요.")
        state.score += 12 if request.choice in {"modify", "reject"} else 6
        state.evidence.append("LLM 제안 검토")
        feedback = "AI 제안과 사람의 판단을 분리해 기록했습니다."
    elif request.stage == "data":
        if request.choice not in {"distribution", "mean_only"}:
            raise HTTPException(422, "지원하지 않는 데이터 판단입니다.")
        state.score += 18 if request.choice == "distribution" else -10
        state.evidence.append("Tool·Lot·위치별 분포" if request.choice == "distribution" else "전체 평균")
        feedback = "edge·Tool 편중과 경쟁 가설을 확보했습니다." if request.choice == "distribution" else "평균만으로는 공간 패턴을 설명할 수 없습니다."
    elif request.stage == "experiment":
        if request.choice not in {"screening", "ofat", "immediate"}:
            raise HTTPException(422, "지원하지 않는 실험계획입니다.")
        repeats = int(request.payload.get("repeats", 0) or 0)
        if request.choice != "immediate" and repeats < 2:
            raise HTTPException(422, "검증실험 반복은 최소 2회입니다.")
        state.score += {"screening": 18, "ofat": 8, "immediate": -14}[request.choice]
        state.evidence.append({"screening": "대조군 Screening DOE", "ofat": "한 변수 확인 실험", "immediate": "대조군 없는 즉시 변경"}[request.choice])
        feedback = "가설이 맞을 때와 틀릴 때의 예상 결과가 고정되었습니다."
    elif request.stage == "analysis":
        tool_ids = request.payload.get("tools", [])
        if not isinstance(tool_ids, list) or not tool_ids or any(tool not in TOOLS for tool in tool_ids):
            raise HTTPException(422, "유효한 분석 툴을 하나 이상 선택하세요.")
        selected = [TOOLS[tool] for tool in tool_ids]
        cost = sum(tool["cost"] for tool in selected)
        duration = sum(tool["time"] for tool in selected)
        if cost > state.budget or duration > state.time_left:
            raise HTTPException(422, "분석 예산 또는 시간을 초과했습니다.")
        kinds = {tool["kind"] for tool in selected}
        coverage = set(SCENARIO["required_analysis_kinds"]).issubset(kinds)
        overanalysis = len(selected) > 4 or cost > 65 or duration > 50
        state.budget -= cost
        state.time_left -= duration
        state.score += 16 if coverage and not overanalysis else -8
        state.evidence.extend(tool["label"] for tool in selected)
        record.update({"tools": tool_ids, "coverage": coverage, "overanalysis": overanalysis, "cost": cost, "time": duration})
        feedback = "필요 정보영역을 최소 비용으로 확보했습니다." if coverage and not overanalysis else "분석영역 공백 또는 과잉분석 위험이 남았습니다."
    elif request.stage == "validation":
        if request.choice not in {"controlled", "direct", "release"}:
            raise HTTPException(422, "지원하지 않는 최종 조치입니다.")
        metrics = request.payload.get("metrics", {})
        try:
            baseline = float(metrics["baseline"])
            holdout = float(metrics["holdout"])
        except (KeyError, TypeError, ValueError):
            raise HTTPException(422, "Baseline과 Holdout 수치를 입력하세요.")
        direction = metrics.get("direction", "higher")
        improved = holdout > baseline if direction == "higher" else holdout < baseline
        state.score += (14 if improved else -10) + {"controlled": 14, "direct": 2, "release": -18}[request.choice]
        record["improved"] = improved
        state.evidence.append("Holdout 검증")
        feedback = "검증 결과와 적용 한계가 기록되었습니다."

    state.history.append(record)
    state.stage_index += 1
    if state.stage_index >= len(STAGES):
        state.completed = True
        state.stage_index = len(STAGES) - 1
        state.verdict = final_verdict(state)
    state.score = max(0, min(100, state.score))
    return {"state": state.model_dump(), "feedback": feedback}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "virtual-fab"}


@app.get("/api/scenario/photo-cd-drift")
def get_scenario() -> dict[str, Any]:
    return SCENARIO


@app.post("/api/sessions", response_model=SessionState)
def create_session() -> SessionState:
    state = SessionState(id=str(uuid4()))
    SESSIONS[state.id] = state
    return state


@app.get("/api/sessions/{session_id}", response_model=SessionState)
def get_session(session_id: str) -> SessionState:
    state = SESSIONS.get(session_id)
    if not state:
        raise HTTPException(404, "세션을 찾을 수 없습니다.")
    return state


@app.post("/api/sessions/{session_id}/decisions")
def decide(session_id: str, request: DecisionRequest) -> dict[str, Any]:
    state = SESSIONS.get(session_id)
    if not state:
        raise HTTPException(404, "세션을 찾을 수 없습니다.")
    return apply_decision(state, request)


@app.post("/api/sessions/{session_id}/restart", response_model=SessionState)
def restart(session_id: str) -> SessionState:
    if session_id not in SESSIONS:
        raise HTTPException(404, "세션을 찾을 수 없습니다.")
    state = SessionState(id=session_id)
    SESSIONS[session_id] = state
    return state


if DIST_DIR.exists():
    assets = DIST_DIR / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{path:path}")
    def spa(path: str) -> FileResponse:
        candidate = (DIST_DIR / path).resolve()
        if path and DIST_DIR.resolve() in candidate.parents and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(DIST_DIR / "index.html")
