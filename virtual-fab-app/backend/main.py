from __future__ import annotations

import base64
import hashlib
import html
import json
import os
import re
import secrets
import sqlite3
import time
from pathlib import Path
from threading import Lock
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request as URLRequest, urlopen
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request as FastAPIRequest
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, SecretStr

APP_DIR = Path(__file__).resolve().parents[1]
DIST_DIR = APP_DIR / "dist"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash").strip()
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DB_PATH = Path(os.getenv("VIRTUAL_FAB_DB", str(APP_DIR / ".runtime" / "sessions.sqlite3")))
DB_LOCK = Lock()
RATE_LOCK = Lock()
LLM_RATE_WINDOW: dict[str, list[float]] = {}
VERIFIED_BYOK: dict[str, tuple[str, str, str]] = {}
STAGES = ["incident", "coach", "data", "experiment", "analysis", "validation"]
AI_PROVIDERS = {"openai": "OpenAI", "anthropic": "Anthropic", "gemini": "Google Gemini", "deepseek": "DeepSeek"}
MODEL_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,99}$")

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

BASE_STAGES = [
    {"id": "incident", "label": "문제 발생", "station": "alert"},
    {"id": "coach", "label": "LLM Coach", "station": "coach", "brief": "AI에게 정답이 아니라 경쟁 가설·반증 증거·누락 변수를 질문한다."},
    {"id": "data", "label": "데이터 판단", "station": "data", "brief": "Train 데이터의 결측·중복·단위·설비 편중과 위치별 분포를 확인한다."},
    {"id": "experiment", "label": "실험계획", "station": "doe", "brief": "대조군·요인·수준·반복·판정기준을 고정한다."},
    {"id": "analysis", "label": "분석 툴", "station": "analysis", "brief": "구조·화학·전기 분석을 비용·시간·정보가치로 선택한다."},
    {"id": "validation", "label": "검증", "station": "validation", "brief": "Holdout과 재실험 결과로 조치 범위를 결정한다."},
]


def scenario_stages(incident_brief: str) -> list[dict[str, str]]:
    return [{**stage, **({"brief": incident_brief} if stage["id"] == "incident" else {})} for stage in BASE_STAGES]


PHOTO_SCENARIO = {
    "id": "photo-cd-drift",
    "module_no": "01",
    "process": "PHOTO",
    "title": "사라진 선폭의 비밀",
    "tagline": "평균 CD는 정상인데 Edge 결함이 급증했다.",
    "skills": ["공간 분포", "DOE", "CD 계측"],
    "badge": "LIVE · 검증 완료",
    "version": "0.4.0",
    "notice": "교육용 합성 시나리오이며 실제 회사 Recipe·현장 경험을 의미하지 않습니다.",
    "coach_prompt": "Photo CD edge 산포의 경쟁 가설 3개와 각 가설을 반증할 최소 증거를 제안해줘.",
    "experiment_label": "Dose·Focus·PEB Screening",
    "signal": {"title": "합성 Train 데이터 · wafer edge 결함률", "aria": "웨이퍼 중심보다 가장자리에서 결함률이 증가하는 합성 데이터 막대그래프", "start": "CENTER", "end": "EDGE", "warning": 54, "risk_from": 9, "bars": [31, 33, 34, 35, 37, 39, 42, 46, 50, 55, 62, 69, 76, 82]},
    "incident": {
        "case_id": "VF-PH-01",
        "role": "입사 3개월 차 Photo 공정기술 엔지니어",
        "deadline": "후속 Etch 투입까지 60분",
        "facts": [
            {"label": "전체 평균 CD", "value": "54.9 nm", "note": "합성 규격 53–57 nm 안"},
            {"label": "Edge 결함률", "value": "3.2%", "note": "최근 기준 0.8%, 경고선 2.0%"},
            {"label": "공정 이력", "value": "동일 Recipe", "note": "직전 Lot까지 특이사항 미보고"},
        ],
        "unknowns": ["Photo 공정의 실제 변화", "설비·위치 편중", "계측기 편향 또는 데이터 품질 문제"],
        "decision": "평균 CD를 근거로 진행할 것인가, Lot을 보류하고 공간 분포부터 확인할 것인가?",
        "choices": {"hold": ["Lot 보류", "분포와 위치 패턴부터 확인"], "release": ["공정 진행", "평균 CD가 규격 안이므로 통과"]},
    },
    "stages": scenario_stages("전체 평균은 합성 규격 안이지만 edge 결함률은 경고선을 넘었다. 후속 공정 투입 전 첫 조치를 결정해야 한다."),
    "tools": TOOLS,
    "required_analysis_kinds": ["dimension", "structure"],
    "limits": {"budget": 80, "time": 60},
}

DRY_ETCH_SCENARIO = {
    "id": "dry-etch-profile", "module_no": "02", "process": "DRY ETCH", "title": "기울어진 Sidewall", "tagline": "식각 깊이는 맞지만 Sidewall 각도가 무너졌다.",
    "skills": ["Profile", "Plasma", "SEM"], "badge": "NEW", "version": "0.4.0", "notice": PHOTO_SCENARIO["notice"],
    "coach_prompt": "Dry Etch 깊이는 정상인데 Sidewall angle과 edge residue가 악화된 경쟁 가설 3개와 최소 반증 증거를 제안해줘.", "experiment_label": "Pressure·RF Bias·Gas Ratio Screening",
    "signal": {"title": "합성 Train 데이터 · edge residue index", "aria": "웨이퍼 중심에서 가장자리로 갈수록 잔류물 지수가 증가하는 막대그래프", "start": "CENTER", "end": "EDGE", "warning": 56, "risk_from": 9, "bars": [27, 28, 29, 31, 33, 35, 39, 43, 49, 57, 63, 70, 78, 86]},
    "incident": {"case_id": "VF-DE-02", "role": "Dry Etch 공정기술 엔지니어", "deadline": "후속 세정·계측 판정까지 75분",
        "facts": [{"label": "평균 식각 깊이", "value": "119.8 nm", "note": "합성 규격 115–125 nm 안"}, {"label": "Sidewall angle", "value": "82.4°", "note": "최근 기준 88.5°, 경고 85°"}, {"label": "Edge residue", "value": "2.7%", "note": "최근 기준 0.6%"}],
        "unknowns": ["RF bias·압력·가스비 변화", "Chamber seasoning 또는 부산물", "단면 시편·계측 편향"], "decision": "깊이 평균만 보고 진행할 것인가, Lot을 보류하고 Profile과 잔류물 원인을 분리할 것인가?",
        "choices": {"hold": ["Lot 보류", "Profile·위치 분포부터 확인"], "release": ["공정 진행", "평균 깊이가 규격 안이므로 통과"]}},
    "stages": scenario_stages("식각 깊이는 규격 안이지만 Sidewall과 edge residue가 동시에 악화됐다. 평균 깊이가 가리는 구조 이상을 먼저 판단한다."), "tools": TOOLS, "required_analysis_kinds": ["structure", "chemistry"], "limits": {"budget": 85, "time": 75},
}

SPUTTER_SCENARIO = {
    "id": "sputter-sheet-resistance", "module_no": "03", "process": "SPUTTER", "title": "같은 두께, 다른 저항", "tagline": "막 두께는 정상인데 Sheet resistance가 흔들린다.",
    "skills": ["박막", "4-Point Probe", "조성"], "badge": "NEW", "version": "0.4.0", "notice": PHOTO_SCENARIO["notice"],
    "coach_prompt": "Sputter 막 두께는 정상인데 sheet resistance가 edge에서 상승한 경쟁 가설 3개와 최소 반증 증거를 제안해줘.", "experiment_label": "Power·Pressure·Ar Flow Screening",
    "signal": {"title": "합성 Train 데이터 · sheet resistance", "aria": "웨이퍼 중심에서 가장자리로 갈수록 면저항이 증가하는 막대그래프", "start": "CENTER", "end": "EDGE", "warning": 58, "risk_from": 10, "bars": [34, 35, 34, 36, 37, 39, 42, 44, 47, 51, 59, 65, 73, 80]},
    "incident": {"case_id": "VF-SP-03", "role": "Sputter 박막 공정 엔지니어", "deadline": "후속 Patterning 투입까지 70분",
        "facts": [{"label": "평균 막 두께", "value": "102.1 nm", "note": "합성 규격 98–106 nm 안"}, {"label": "Edge 면저항", "value": "1.42 Ω/□", "note": "Center 1.10 Ω/□"}, {"label": "입자 계수", "value": "+18%", "note": "최근 기준 대비 증가"}],
        "unknowns": ["Target erosion·plasma 분포", "압력·wafer 온도 영향", "4-point probe 또는 두께 모델 편향"], "decision": "두께 평균만 보고 진행할 것인가, 전기특성과 조성의 위치 분포를 확인할 것인가?",
        "choices": {"hold": ["Lot 보류", "면저항·조성 분포부터 확인"], "release": ["공정 진행", "평균 두께가 규격 안이므로 통과"]}},
    "stages": scenario_stages("막 두께는 규격 안이지만 면저항과 입자 신호가 함께 변했다. 두께·조성·전기특성 중 무엇이 실제 변했는지 분리한다."), "tools": TOOLS, "required_analysis_kinds": ["electrical", "chemistry"], "limits": {"budget": 80, "time": 70},
}

CVD_SCENARIO = {
    "id": "cvd-film-uniformity", "module_no": "04", "process": "CVD", "title": "막은 쌓였지만 같지 않다", "tagline": "평균 두께 뒤에 균일도와 막질 이상이 숨어 있다.",
    "skills": ["Uniformity", "막질", "Ellipsometry"], "badge": "NEW", "version": "0.4.0", "notice": PHOTO_SCENARIO["notice"],
    "coach_prompt": "CVD 평균 두께는 정상인데 wafer 균일도와 굴절률이 악화된 경쟁 가설 3개와 최소 반증 증거를 제안해줘.", "experiment_label": "Temperature·Pressure·Gas Ratio Screening",
    "signal": {"title": "합성 Train 데이터 · thickness non-uniformity", "aria": "웨이퍼 중심에서 가장자리로 갈수록 두께 불균일도가 증가하는 막대그래프", "start": "CENTER", "end": "EDGE", "warning": 53, "risk_from": 8, "bars": [24, 26, 29, 30, 33, 37, 42, 48, 55, 61, 68, 74, 81, 88]},
    "incident": {"case_id": "VF-CV-04", "role": "CVD 박막 공정기술 엔지니어", "deadline": "후속 Lithography 투입까지 90분",
        "facts": [{"label": "평균 막 두께", "value": "201.4 nm", "note": "합성 규격 195–205 nm 안"}, {"label": "WIWNU", "value": "6.8%", "note": "경고선 3.0%"}, {"label": "굴절률 Edge", "value": "1.91", "note": "Center 1.97"}],
        "unknowns": ["Showerhead·가스 분포", "온도·전구체 고갈", "Ellipsometry 광학모델 편향"], "decision": "평균 두께만 보고 진행할 것인가, 균일도와 막질 변화를 먼저 확인할 것인가?",
        "choices": {"hold": ["Lot 보류", "두께·막질 분포부터 확인"], "release": ["공정 진행", "평균 두께가 규격 안이므로 통과"]}},
    "stages": scenario_stages("평균 막 두께는 정상이나 wafer 내 균일도와 굴절률이 동시에 벗어났다. 증착량과 막질 변화를 분리한다."), "tools": TOOLS, "required_analysis_kinds": ["dimension", "chemistry"], "limits": {"budget": 85, "time": 90},
}

CMP_SCENARIO = {
    "id": "cmp-dishing", "module_no": "05", "process": "CMP", "title": "평탄화 뒤의 함몰", "tagline": "평균 제거량은 맞지만 Dense pattern이 꺼졌다.",
    "skills": ["Dishing", "Pattern Density", "Profile"], "badge": "NEW", "version": "0.4.0", "notice": PHOTO_SCENARIO["notice"],
    "coach_prompt": "CMP 평균 제거량은 정상인데 dense pattern dishing과 edge 잔막이 증가한 경쟁 가설 3개와 최소 반증 증거를 제안해줘.", "experiment_label": "Pressure·Platen Speed·Slurry Flow Screening",
    "signal": {"title": "합성 Train 데이터 · pattern dishing", "aria": "패턴 밀도가 높아질수록 디싱 값이 증가하는 막대그래프", "start": "ISO", "end": "DENSE", "warning": 55, "risk_from": 9, "bars": [22, 25, 28, 31, 34, 38, 41, 46, 51, 58, 66, 73, 80, 87]},
    "incident": {"case_id": "VF-CM-05", "role": "CMP 공정기술 엔지니어", "deadline": "세정·후속 계측까지 65분",
        "facts": [{"label": "평균 제거량", "value": "298 nm", "note": "합성 규격 290–310 nm 안"}, {"label": "Dense dishing", "value": "38 nm", "note": "경고선 20 nm"}, {"label": "Edge 잔막", "value": "+24%", "note": "최근 기준 대비 증가"}],
        "unknowns": ["Pad conditioning·마모", "Slurry 유량·압력·회전", "Pattern density·Profile 계측 편향"], "decision": "평균 제거량만 보고 진행할 것인가, 패턴 밀도별 Profile과 잔막을 확인할 것인가?",
        "choices": {"hold": ["Lot 보류", "Pattern별 Profile부터 확인"], "release": ["공정 진행", "평균 제거량이 규격 안이므로 통과"]}},
    "stages": scenario_stages("평균 제거량은 정상이나 dense pattern의 dishing과 edge 잔막이 함께 증가했다. 패턴 의존성과 장비 요인을 분리한다."), "tools": TOOLS, "required_analysis_kinds": ["dimension", "structure"], "limits": {"budget": 80, "time": 65},
}

DEVICE_SCENARIO = {
    "id": "device-vth-shift", "module_no": "06", "process": "DEVICE", "title": "오른쪽으로 밀린 I–V", "tagline": "On-current는 통과했지만 Vth와 Off-current가 변했다.",
    "skills": ["I–V", "Vth", "신뢰성"], "badge": "NEW", "version": "0.4.0", "notice": PHOTO_SCENARIO["notice"],
    "coach_prompt": "소자 On-current는 정상인데 Vth shift와 Off-current가 증가한 경쟁 가설 3개와 최소 반증 증거를 제안해줘.", "experiment_label": "Stress Voltage·Time·Temperature Screening",
    "signal": {"title": "합성 Train 데이터 · Vth shift after stress", "aria": "스트레스 시간이 증가할수록 문턱전압 이동이 증가하는 막대그래프", "start": "INITIAL", "end": "STRESS", "warning": 57, "risk_from": 9, "bars": [20, 23, 26, 29, 33, 37, 41, 46, 52, 59, 66, 72, 79, 85]},
    "incident": {"case_id": "VF-DV-06", "role": "소자·신뢰성 평가 엔지니어", "deadline": "Reliability review까지 80분",
        "facts": [{"label": "On-current", "value": "9.8 μA", "note": "합성 하한 9.0 μA 통과"}, {"label": "Vth shift", "value": "+1.15 V", "note": "경고선 +0.50 V"}, {"label": "Off-current", "value": "6.2×", "note": "초기 대비 증가"}],
        "unknowns": ["Charge trapping·결함 생성", "Contact·공정 편차", "Sweep rate·hysteresis 계측 영향"], "decision": "On-current만 보고 통과할 것인가, 스트레스 조건과 I–V 열화 메커니즘을 먼저 확인할 것인가?",
        "choices": {"hold": ["판정 보류", "I–V·Stress 분포부터 확인"], "release": ["평가 통과", "On-current가 기준 안이므로 진행"]}},
    "stages": scenario_stages("On-current는 합성 기준을 통과했지만 Vth shift와 Off-current가 악화됐다. 동작 성능과 열화 안정성을 분리해 판단한다."), "tools": TOOLS, "required_analysis_kinds": ["electrical", "structure"], "limits": {"budget": 80, "time": 80},
}

SCENARIOS = {scenario["id"]: scenario for scenario in [PHOTO_SCENARIO, DRY_ETCH_SCENARIO, SPUTTER_SCENARIO, CVD_SCENARIO, CMP_SCENARIO, DEVICE_SCENARIO]}


class DecisionRequest(BaseModel):
    stage: Literal["incident", "coach", "data", "experiment", "analysis", "validation"]
    choice: str = Field(min_length=1, max_length=80)
    payload: dict[str, Any] = Field(default_factory=dict)


class DeepSeekRequest(BaseModel):
    prompt: str = Field(min_length=20, max_length=2000)


class BYOKConnectionRequest(BaseModel):
    provider: Literal["openai", "anthropic", "gemini", "deepseek"]
    model: str = Field(min_length=1, max_length=100)
    api_key: SecretStr


class BYOKGenerateRequest(BYOKConnectionRequest):
    prompt: str = Field(min_length=20, max_length=2000)


class ReportRequest(BaseModel):
    opinion: str = Field(min_length=40, max_length=3000)
    presenter: str = Field(default="지원자", max_length=80)
    target_role: str = Field(default="반도체 공정기술", max_length=120)


class SessionState(BaseModel):
    id: str
    scenario_id: str = "photo-cd-drift"
    scenario_version: str = ""
    seed: int = Field(default=0, ge=0, le=2_147_483_647)
    stage_index: int = 0
    budget: int = 80
    time_left: int = 60
    score: int = 0
    llm_check_attempts: int = 0
    llm_call_count: int = 0
    evidence: list[str] = Field(default_factory=list)
    history: list[dict[str, Any]] = Field(default_factory=list)
    completed: bool = False
    verdict: str | None = None


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, state_json TEXT NOT NULL, updated_at INTEGER NOT NULL)"
        )
        connection.execute("DELETE FROM sessions WHERE updated_at < ?", (int(time.time()) - 86400,))


def save_session(state: SessionState) -> None:
    with DB_LOCK, sqlite3.connect(DB_PATH, timeout=5) as connection:
        connection.execute(
            "INSERT INTO sessions(id, state_json, updated_at) VALUES(?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET state_json=excluded.state_json, updated_at=excluded.updated_at",
            (state.id, state.model_dump_json(), int(time.time())),
        )
        connection.execute(
            "DELETE FROM sessions WHERE id NOT IN (SELECT id FROM sessions ORDER BY updated_at DESC LIMIT 500)"
        )


def load_session(session_id: str) -> SessionState | None:
    with DB_LOCK, sqlite3.connect(DB_PATH, timeout=5) as connection:
        row = connection.execute("SELECT state_json FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not row:
        return None
    try:
        raw_state = json.loads(row[0])
        scenario = SCENARIOS.get(raw_state.get("scenario_id", "photo-cd-drift"))
        if scenario:
            raw_state.setdefault("scenario_version", scenario["version"])
        legacy_seed = int.from_bytes(session_id.encode("utf-8"), "little") % 2_147_483_648
        raw_state.setdefault("seed", legacy_seed)
        return SessionState.model_validate(raw_state)
    except (json.JSONDecodeError, TypeError, ValueError):
        with DB_LOCK, sqlite3.connect(DB_PATH, timeout=5) as connection:
            connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        return None


init_db()

app = FastAPI(title="Virtual Fab Scenario API", version="0.4.0")


CHOICE_LABELS = {
    "hold": "판정 보류 후 분포 확인", "release_by_mean": "대표 평균값만 보고 진행",
    "modify": "AI 제안을 수정해 사용", "accept": "AI 제안을 그대로 채택", "reject": "근거 부족으로 보류",
    "distribution": "위치·Tool·Lot 분포 분석", "mean_only": "전체 평균만 확인",
    "screening": "대조군 포함 Screening DOE", "ofat": "한 변수 확인 실험", "immediate": "검증 없이 Recipe 변경",
    "select": "정보가치 기반 분석 툴 선택",
    "controlled": "한정 적용 후 모니터링", "direct": "전체 Lot 즉시 적용", "release": "검증 없이 해제",
}


def scenario_for(state: SessionState) -> dict[str, Any]:
    scenario = SCENARIOS.get(state.scenario_id)
    if not scenario:
        raise HTTPException(409, "이 세션의 시나리오를 더 이상 찾을 수 없습니다.")
    if state.scenario_version != scenario["version"]:
        raise HTTPException(409, "시나리오 버전이 갱신되었습니다. 같은 seed를 유지한 채 실험을 다시 시작하세요.")
    return scenario


def validate_byok_request(request: BYOKConnectionRequest) -> tuple[str, str]:
    model = request.model.strip()
    api_key = request.api_key.get_secret_value().strip()
    if not MODEL_ID_PATTERN.fullmatch(model):
        raise HTTPException(422, "모델 ID 형식을 확인하세요.")
    if not 20 <= len(api_key) <= 300:
        raise HTTPException(422, "API 키 형식을 확인하세요.")
    return model, api_key


def byok_fingerprint(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def require_secure_byok(request: FastAPIRequest) -> None:
    hostname = (request.url.hostname or "").lower()
    forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip().lower()
    secure = request.url.scheme == "https" or forwarded_proto == "https"
    if not secure and hostname not in {"127.0.0.1", "localhost", "testserver"}:
        raise HTTPException(426, "개인 API 키 연결은 HTTPS에서만 사용할 수 있습니다.")


def enforce_llm_rate_limit(request: FastAPIRequest) -> None:
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with RATE_LOCK:
        recent = [stamp for stamp in LLM_RATE_WINDOW.get(client, []) if now - stamp < 60]
        if len(recent) >= 10:
            raise HTTPException(429, "AI 연결 요청이 너무 많습니다. 1분 뒤 다시 시도하세요.")
        recent.append(now)
        LLM_RATE_WINDOW[client] = recent


def provider_json_request(url: str, headers: dict[str, str], body: dict[str, Any] | None = None) -> dict[str, Any]:
    encoded = json.dumps(body).encode("utf-8") if body is not None else None
    request = URLRequest(url, data=encoded, headers={"Content-Type": "application/json", **headers})
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code in {401, 403}:
            message = "API 키 인증에 실패했습니다. 키의 상태와 권한을 확인하세요."
        elif exc.code == 404:
            message = "이 계정에서 모델 ID를 찾을 수 없습니다. 모델명을 확인하세요."
        elif exc.code == 429:
            message = "제공사의 사용량 또는 결제 한도에 도달했습니다."
        else:
            message = f"제공사 API 요청에 실패했습니다 ({exc.code})."
        raise HTTPException(502, message) from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(502, "제공사 API 응답을 30초 안에 확인하지 못했습니다.") from exc


def check_llm_connection(provider: str, model: str, api_key: str) -> dict[str, str]:
    encoded_model = quote(model.removeprefix("models/"), safe="-._:")
    if provider == "openai":
        result = provider_json_request(
            f"https://api.openai.com/v1/models/{encoded_model}",
            {"Authorization": f"Bearer {api_key}"},
        )
        resolved = str(result.get("id") or model)
    elif provider == "anthropic":
        result = provider_json_request(
            f"https://api.anthropic.com/v1/models/{encoded_model}",
            {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        )
        resolved = str(result.get("id") or model)
    elif provider == "gemini":
        result = provider_json_request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{encoded_model}",
            {"x-goog-api-key": api_key},
        )
        resolved = str(result.get("name") or model).removeprefix("models/")
    else:
        result = provider_json_request(
            "https://api.deepseek.com/models",
            {"Authorization": f"Bearer {api_key}"},
        )
        available = {str(item.get("id")) for item in result.get("data", [])}
        if model not in available:
            raise HTTPException(422, "이 DeepSeek 키에서 선택한 모델을 찾을 수 없습니다.")
        resolved = model
    return {"status": "connected", "provider": provider, "provider_label": AI_PROVIDERS[provider], "model": resolved}


def coach_messages(prompt: str, scenario: dict[str, Any]) -> tuple[str, str]:
    system = (
        f"당신은 반도체 {scenario['process']} 공정 학습자의 소크라테스식 멘토다. "
        "교육용 합성 상황만 다루고 실제 회사 Recipe나 수치를 만들지 않는다. "
        "정답을 단정하지 말고 경쟁 가설 3개, 각 가설을 반증할 최소 증거, "
        "가장 먼저 할 저비용 측정을 한국어로 간결하게 제안한다."
    )
    user = (
        "교육용 관찰: "
        + "; ".join(f"{fact['label']} {fact['value']} ({fact['note']})" for fact in scenario["incident"]["facts"])
        + f". 제한시간은 {scenario['incident']['deadline']}이다. 미확인 항목은 "
        + ", ".join(scenario["incident"]["unknowns"])
        + f".\n학습자 질문: {prompt}"
    )
    return system, user


def normalize_usage(prompt_tokens: int = 0, completion_tokens: int = 0, total_tokens: int = 0) -> dict[str, int]:
    return {
        "prompt_tokens": int(prompt_tokens or 0),
        "completion_tokens": int(completion_tokens or 0),
        "total_tokens": int(total_tokens or (prompt_tokens or 0) + (completion_tokens or 0)),
    }


def generate_with_byok(provider: str, model: str, api_key: str, prompt: str, scenario: dict[str, Any]) -> dict[str, Any]:
    system, user = coach_messages(prompt, scenario)
    if provider == "openai":
        result = provider_json_request(
            "https://api.openai.com/v1/responses",
            {"Authorization": f"Bearer {api_key}"},
            {"model": model, "input": [{"role": "system", "content": system}, {"role": "user", "content": user}], "max_output_tokens": 500},
        )
        texts = [
            str(content.get("text", ""))
            for item in result.get("output", []) if item.get("type") == "message"
            for content in item.get("content", []) if content.get("type") == "output_text"
        ]
        content = "\n".join(text for text in texts if text).strip()
        usage_raw = result.get("usage", {})
        usage = normalize_usage(usage_raw.get("input_tokens", 0), usage_raw.get("output_tokens", 0), usage_raw.get("total_tokens", 0))
    elif provider == "anthropic":
        result = provider_json_request(
            "https://api.anthropic.com/v1/messages",
            {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
            {"model": model, "max_tokens": 500, "system": system, "messages": [{"role": "user", "content": user}]},
        )
        content = "\n".join(str(block.get("text", "")) for block in result.get("content", []) if block.get("type") == "text").strip()
        usage_raw = result.get("usage", {})
        usage = normalize_usage(usage_raw.get("input_tokens", 0), usage_raw.get("output_tokens", 0))
    elif provider == "gemini":
        encoded_model = quote(model.removeprefix("models/"), safe="-._:")
        result = provider_json_request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{encoded_model}:generateContent",
            {"x-goog-api-key": api_key},
            {"systemInstruction": {"parts": [{"text": system}]}, "contents": [{"role": "user", "parts": [{"text": user}]}], "generationConfig": {"maxOutputTokens": 500, "temperature": 0.2}},
        )
        candidates = result.get("candidates", [])
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        content = "\n".join(str(part.get("text", "")) for part in parts if part.get("text")).strip()
        usage_raw = result.get("usageMetadata", {})
        usage = normalize_usage(usage_raw.get("promptTokenCount", 0), usage_raw.get("candidatesTokenCount", 0), usage_raw.get("totalTokenCount", 0))
    else:
        result = provider_json_request(
            "https://api.deepseek.com/chat/completions",
            {"Authorization": f"Bearer {api_key}"},
            {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "thinking": {"type": "disabled"}, "temperature": 0.2, "max_tokens": 500},
        )
        choices = result.get("choices", [])
        content = str(choices[0].get("message", {}).get("content", "")).strip() if choices else ""
        usage_raw = result.get("usage", {})
        usage = normalize_usage(usage_raw.get("prompt_tokens", 0), usage_raw.get("completion_tokens", 0), usage_raw.get("total_tokens", 0))
    if not content:
        raise HTTPException(502, "선택한 AI가 빈 답변을 반환했습니다.")
    return {"response": content, "provider": provider, "provider_label": AI_PROVIDERS[provider], "model": model, "usage": usage}


def deepseek_generate(prompt: str, user_id: str, scenario: dict[str, Any]) -> dict[str, Any]:
    if not DEEPSEEK_API_KEY:
        raise HTTPException(503, "DeepSeek API 키가 아직 설정되지 않았습니다. 외부 AI 복사·붙여넣기를 이용하세요.")
    body = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    f"당신은 반도체 {scenario['process']} 공정 학습자의 소크라테스식 멘토다. "
                    "교육용 합성 상황만 다루고 실제 회사 Recipe나 수치를 만들지 않는다. "
                    "정답을 단정하지 말고 경쟁 가설 3개, 각 가설을 반증할 최소 증거, "
                    "가장 먼저 할 저비용 측정을 한국어로 간결하게 제안한다."
                ),
            },
            {
                "role": "user",
                "content": (
                    "교육용 관찰: "
                    + "; ".join(f"{fact['label']} {fact['value']} ({fact['note']})" for fact in scenario["incident"]["facts"])
                    + f". 제한시간은 {scenario['incident']['deadline']}이다. 미확인 항목은 "
                    + ", ".join(scenario["incident"]["unknowns"])
                    + ".\n"
                    f"학습자 질문: {prompt}"
                ),
            },
        ],
        "thinking": {"type": "disabled"},
        "temperature": 0.2,
        "max_tokens": 500,
        "user_id": user_id,
    }).encode("utf-8")
    request = URLRequest(
        DEEPSEEK_URL,
        data=body,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = "인증 또는 잔액을 확인하세요." if exc.code in {401, 402, 403} else "잠시 후 다시 시도하세요."
        raise HTTPException(502, f"DeepSeek API 호출 실패 ({exc.code}). {detail}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(502, "DeepSeek API 응답을 받지 못했습니다. 복사·붙여넣기 방식으로 계속할 수 있습니다.") from exc
    choices = result.get("choices", [])
    content = str(choices[0].get("message", {}).get("content", "")).strip() if choices else ""
    if not content:
        raise HTTPException(502, "DeepSeek API가 빈 답변을 반환했습니다.")
    usage = result.get("usage", {})
    return {
        "response": content,
        "model": str(result.get("model") or DEEPSEEK_MODEL),
        "usage": {
            "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
            "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
            "total_tokens": int(usage.get("total_tokens", 0) or 0),
        },
    }


def svg_data_uri(svg: str) -> str:
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def build_report(state: SessionState, request: ReportRequest) -> str:
    scenario = scenario_for(state)
    safe_presenter = html.escape(request.presenter)
    safe_role = html.escape(request.target_role)
    safe_opinion = html.escape(request.opinion).replace("\n", "<br>")
    history_by_stage = {item["stage"]: item for item in state.history}
    incident = history_by_stage.get("incident", {})
    coach = history_by_stage.get("coach", {})
    analysis = history_by_stage.get("analysis", {})
    validation = history_by_stage.get("validation", {})
    tools = [TOOLS[item]["label"] for item in analysis.get("tools", []) if item in TOOLS]
    metrics = validation.get("payload", {}).get("metrics", {})
    mentor_text = str(coach.get("payload", {}).get("llm_response", "기록 없음"))[:1500]
    prompt_text = str(coach.get("payload", {}).get("prompt", "기록 없음"))[:1200]
    model_text = str(coach.get("payload", {}).get("llm_model", "외부 AI"))[:80]
    safe_mentor = html.escape(mentor_text).replace("\n", "<br>")
    safe_prompt = html.escape(prompt_text).replace("\n", "<br>")
    safe_model = html.escape(model_text)
    choice_rows = "".join(
        f"<li><b>{html.escape(next(stage['label'] for stage in scenario['stages'] if stage['id'] == item['stage']))}</b>"
        f"<span>{html.escape(CHOICE_LABELS.get(item['choice'], item['choice']))}</span></li>"
        for item in state.history
    )
    wafer_svg = svg_data_uri("""<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 640 360'>
      <rect width='640' height='360' fill='#eaf1f1'/><circle cx='320' cy='180' r='128' fill='#a9e1e3' stroke='#092d35' stroke-width='8'/>
      <path d='M308 52h24v18h-24z' fill='#eaf1f1'/><circle cx='225' cy='100' r='12' fill='#e58a00'/><circle cx='414' cy='112' r='16' fill='#e58a00'/>
      <circle cx='438' cy='210' r='13' fill='#e58a00'/><circle cx='205' cy='235' r='11' fill='#e58a00'/><circle cx='370' cy='292' r='14' fill='#e58a00'/>
      <circle cx='318' cy='178' r='42' fill='none' stroke='#fff' stroke-width='3' stroke-dasharray='8 8'/>
      <text x='28' y='326' font-family='Arial,sans-serif' font-size='22' fill='#092d35'>SYNTHETIC WAFER · EDGE CD DISPERSION</text></svg>""")
    tool_svg = svg_data_uri("""<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 640 360'>
      <rect width='640' height='360' fill='#071d24'/><g fill='#dff6f6' stroke='#00a8b5' stroke-width='5'>
      <rect x='55' y='88' width='140' height='190'/><rect x='250' y='55' width='140' height='223'/><rect x='445' y='112' width='140' height='166'/></g>
      <g fill='#ffb21d'><circle cx='125' cy='154' r='34'/><rect x='295' y='92' width='50' height='105'/><path d='M480 235l35-76 35 76z'/></g>
      <g font-family='Arial,sans-serif' font-size='22' font-weight='700' fill='#dff6f6'><text x='83' y='320'>DIMENSION</text><text x='274' y='320'>STRUCTURE</text><text x='472' y='320'>VERIFY</text></g></svg>""")
    verdict = html.escape(state.verdict or "판정 없음")
    safe_title = html.escape(scenario["title"])
    safe_process = html.escape(scenario["process"])
    safe_tagline = html.escape(scenario["tagline"])
    situation_facts = " ".join(
        f"{html.escape(fact['label'])} <b>{html.escape(fact['value'])}</b> ({html.escape(fact['note'])})."
        for fact in scenario["incident"]["facts"]
    )
    return f"""<!doctype html><html lang='ko'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Virtual Fab 면접 PT · {safe_presenter}</title><style>
*{{box-sizing:border-box}}:root{{--ink:#071d24;--cyan:#00a8b5;--amber:#ffb21d;--paper:#f6f9f8}}body{{margin:0;background:var(--ink);font-family:'Malgun Gothic',sans-serif;color:var(--ink);overflow:hidden}}
.slide{{display:none;width:100vw;height:100vh;padding:7vh 7vw;background:var(--paper);position:relative}}.slide.active{{display:grid}}h1{{font-size:clamp(42px,6vw,88px);line-height:1.04;margin:0;max-width:13ch}}h2{{font-size:clamp(32px,4vw,64px);margin:0 0 4vh}}p,li{{font-size:clamp(17px,1.7vw,28px);line-height:1.6}}.dark{{background:var(--ink);color:#effafa}}.accent{{color:var(--amber)}}.grid{{grid-template-columns:1.1fr .9fr;gap:5vw;align-items:center}}img{{width:100%;max-height:62vh;object-fit:contain}}.metric{{display:flex;gap:4vw;border-top:3px solid var(--cyan);padding-top:3vh}}.metric b{{font-size:clamp(34px,5vw,72px);display:block;color:var(--amber)}}ul{{list-style:none;padding:0}}li{{display:grid;grid-template-columns:180px 1fr;gap:24px;border-top:1px solid #aababc;padding:1.5vh 0}}blockquote{{font-size:clamp(22px,2.5vw,42px);line-height:1.5;margin:0;border-top:5px solid var(--amber);padding-top:4vh}}.label{{position:absolute;top:3vh;left:7vw;font-size:14px;letter-spacing:.12em;color:var(--cyan);font-weight:700}}.nav{{position:fixed;right:24px;bottom:20px;display:flex;gap:8px;z-index:5}}button{{border:0;padding:12px 18px;background:#fff;color:var(--ink);font-weight:700;cursor:pointer}}.counter{{position:fixed;left:24px;bottom:24px;color:#9bc0c3;z-index:5}}small{{position:absolute;bottom:3vh;left:7vw;color:#637e83}}@media(max-width:760px){{.grid{{grid-template-columns:1fr}}.slide{{padding:8vh 6vw;overflow:auto}}li{{grid-template-columns:1fr;gap:4px}}}}@media print{{body{{overflow:visible}}.slide{{display:grid;page-break-after:always}}.nav,.counter{{display:none}}}}
</style></head><body>
<section class='slide dark active'><span class='label'>VIRTUAL FAB · {safe_process} · INTERVIEW BRIEF</span><div><h1>{safe_title}</h1><p class='accent'>{safe_presenter} · {safe_role}</p><p>AI를 사용했지만 판단을 위임하지 않은 데이터 기반 문제해결 기록</p><p>scenario v{html.escape(state.scenario_version)} · seed {state.seed}</p></div><small>교육용 합성 시나리오 · 실제 회사 Recipe 또는 현장 성과가 아님</small></section>
<section class='slide grid'><span class='label'>S · SITUATION</span><div><h2>{safe_tagline}</h2><p>{situation_facts}</p><p><b>제한:</b> {html.escape(scenario['incident']['deadline'])}</p><p><b>초기 판단:</b> {html.escape(CHOICE_LABELS.get(incident.get('choice',''), '기록 없음'))}</p></div><img src='{wafer_svg}' alt='합성 공정 이상 신호 도식'></section>
<section class='slide'><span class='label'>T · TASK</span><div><h2>정답보다 입증 순서를 설계했다</h2><ul><li><b>데이터</b><span>결측·중복·단위·설비 편중과 조건별 분포 확인</span></li><li><b>실험</b><span>대조군·요인·반복·판정기준을 먼저 고정</span></li><li><b>책임</b><span>AI 제안과 사람의 검증 계획을 분리</span></li></ul></div></section>
<section class='slide grid dark'><span class='label'>A · ACTION</span><div><h2>비용이 아니라<br>정보가치를 선택했다</h2><p>선택 도구: {html.escape(' · '.join(tools) or '기록 없음')}</p><div class='metric'><span><b>{analysis.get('cost',0)}</b>비용</span><span><b>{analysis.get('time',0)}</b>분</span></div></div><img src='{tool_svg}' alt='차원 구조 검증 분석 툴 도식'></section>
<section class='slide'><span class='label'>AI COLLABORATION · {safe_model}</span><div><h2>질문과 외부 AI 답변을 함께 기록했다</h2><p><b>PROMPT</b><br>{safe_prompt}</p><blockquote>{safe_mentor}</blockquote><p>답변은 공정 원리·합성 데이터·측정 한계와 대조하고 채택·수정·기각했다.</p></div></section>
<section class='slide'><span class='label'>DECISION TRAIL</span><div><h2>판단의 흔적</h2><ul>{choice_rows}</ul></div></section>
<section class='slide dark'><span class='label'>R · RESULT</span><div><h2>{verdict}</h2><div class='metric'><span><b>{state.score}</b>점수</span><span><b>{state.budget}</b>남은 예산</span><span><b>{state.time_left}</b>남은 시간</span></div><p>Baseline {html.escape(str(metrics.get('baseline','-')))} → Holdout {html.escape(str(metrics.get('holdout','-')))}</p></div><small>이 수치는 교육용 합성 입력에 대한 시나리오 결과다.</small></section>
<section class='slide'><span class='label'>MY DISCUSSION</span><div><h2>내 판단과 한계</h2><blockquote>{safe_opinion}</blockquote></div></section>
<section class='slide dark'><span class='label'>INTERVIEW CLOSE</span><div><h2>제가 증명한 것은<br><span class='accent'>정답이 아니라 과정</span>입니다</h2><p>문제 정의 → AI 가설 → 데이터 감사 → 실험 → 분석 선택 → Holdout 검증</p><p>질문을 받겠습니다.</p></div></section>
<div class='counter'><span id='current'>1</span> / <span id='total'>9</span></div><div class='nav'><button onclick='move(-1)'>이전</button><button onclick='move(1)'>다음</button><button onclick='window.print()'>PDF</button></div>
<script>const s=[...document.querySelectorAll('.slide')];let i=0;function show(n){{i=(n+s.length)%s.length;s.forEach((x,j)=>x.classList.toggle('active',j===i));document.getElementById('current').textContent=i+1}}function move(n){{show(i+n)}}document.addEventListener('keydown',e=>{{if(e.key==='ArrowRight'||e.key===' ')move(1);if(e.key==='ArrowLeft')move(-1)}});document.getElementById('total').textContent=s.length;</script>
</body></html>"""


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
    scenario = scenario_for(state)
    expected = current_stage(state)
    if state.completed:
        raise HTTPException(409, "이미 완료된 세션입니다.")
    if request.stage != expected:
        raise HTTPException(409, f"현재 단계는 {expected}입니다.")

    record: dict[str, Any] = {
        "decision_no": len(state.history) + 1,
        "stage": request.stage,
        "choice": request.choice,
        "payload": request.payload,
        "scenario_version": state.scenario_version,
        "seed": state.seed,
    }
    feedback = "판단이 기록되었습니다."

    if request.stage == "incident":
        if request.choice not in {"hold", "release_by_mean"}:
            raise HTTPException(422, "지원하지 않는 초기 조치입니다.")
        state.score += 10 if request.choice == "hold" else -12
        state.evidence.append("평균과 조건별 분포 분리" if request.choice == "hold" else "대표 평균값만 확인")
        feedback = "Lot을 보류하고 관찰과 원인 추정을 분리했습니다." if request.choice == "hold" else "평균은 정상이나 edge 산포가 다음 단계로 넘어갑니다."
    elif request.stage == "coach":
        if (len(str(request.payload.get("prompt", ""))) < 20
                or len(str(request.payload.get("human_check", ""))) < 20
                or len(str(request.payload.get("llm_response", ""))) < 20):
            raise HTTPException(422, "LLM 질문·실제 응답·사람의 검증 계획을 모두 기록하세요.")
        state.score += 12 if request.choice in {"modify", "reject"} else 6
        state.evidence.append("LLM 제안 검토")
        feedback = "AI 제안과 사람의 판단을 분리해 기록했습니다."
    elif request.stage == "data":
        if request.choice not in {"distribution", "mean_only"}:
            raise HTTPException(422, "지원하지 않는 데이터 판단입니다.")
        state.score += 18 if request.choice == "distribution" else -10
        state.evidence.append("Tool·Lot·위치별 분포" if request.choice == "distribution" else "전체 평균")
        feedback = "설비·Lot·조건별 편중과 경쟁 가설을 확보했습니다." if request.choice == "distribution" else "평균만으로는 조건별 패턴을 설명할 수 없습니다."
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
        coverage = set(scenario["required_analysis_kinds"]).issubset(kinds)
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


@app.get("/api/scenarios")
def list_scenarios() -> list[dict[str, Any]]:
    fields = ("id", "module_no", "process", "title", "tagline", "skills", "badge", "version")
    return [{field: scenario[field] for field in fields} for scenario in SCENARIOS.values()]


@app.get("/api/scenario/{scenario_id}")
def get_scenario(scenario_id: str) -> dict[str, Any]:
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        raise HTTPException(404, "시나리오를 찾을 수 없습니다.")
    return scenario


@app.post("/api/sessions", response_model=SessionState)
def create_session(scenario_id: str = "photo-cd-drift", seed: int | None = None) -> SessionState:
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        raise HTTPException(404, "시나리오를 찾을 수 없습니다.")
    if seed is not None and not 0 <= seed <= 2_147_483_647:
        raise HTTPException(422, "seed는 0 이상 2147483647 이하의 정수여야 합니다.")
    state = SessionState(
        id=str(uuid4()),
        scenario_id=scenario_id,
        scenario_version=scenario["version"],
        seed=seed if seed is not None else secrets.randbelow(2_147_483_648),
        budget=scenario["limits"]["budget"],
        time_left=scenario["limits"]["time"],
    )
    save_session(state)
    return state


@app.get("/api/sessions/{session_id}", response_model=SessionState)
def get_session(session_id: str) -> SessionState:
    state = load_session(session_id)
    if not state:
        raise HTTPException(404, "세션을 찾을 수 없습니다.")
    return state


@app.post("/api/sessions/{session_id}/llm/check")
def check_personal_llm(session_id: str, request: BYOKConnectionRequest, http_request: FastAPIRequest) -> dict[str, str]:
    require_secure_byok(http_request)
    enforce_llm_rate_limit(http_request)
    state = load_session(session_id)
    if not state:
        raise HTTPException(404, "세션을 찾을 수 없습니다.")
    if state.completed or current_stage(state) != "coach":
        raise HTTPException(409, "LLM Coach 단계에서만 개인 AI를 연결할 수 있습니다.")
    if state.llm_check_attempts >= 5:
        raise HTTPException(429, "이 세션의 연결 확인 한도에 도달했습니다.")
    model, api_key = validate_byok_request(request)
    state.llm_check_attempts += 1
    save_session(state)
    result = check_llm_connection(request.provider, model, api_key)
    with RATE_LOCK:
        if len(VERIFIED_BYOK) >= 500 and session_id not in VERIFIED_BYOK:
            VERIFIED_BYOK.pop(next(iter(VERIFIED_BYOK)))
        VERIFIED_BYOK[session_id] = (request.provider, result["model"], byok_fingerprint(api_key))
    return result


@app.post("/api/sessions/{session_id}/llm/generate")
def generate_personal_llm(session_id: str, request: BYOKGenerateRequest, http_request: FastAPIRequest) -> dict[str, Any]:
    require_secure_byok(http_request)
    enforce_llm_rate_limit(http_request)
    state = load_session(session_id)
    if not state:
        raise HTTPException(404, "세션을 찾을 수 없습니다.")
    if state.completed or current_stage(state) != "coach":
        raise HTTPException(409, "LLM Coach 단계에서만 개인 AI를 호출할 수 있습니다.")
    if state.llm_call_count >= 2:
        raise HTTPException(429, "이 세션의 AI 분석 한도 2회에 도달했습니다.")
    model, api_key = validate_byok_request(request)
    with RATE_LOCK:
        verified = VERIFIED_BYOK.get(session_id)
    expected = (request.provider, model, byok_fingerprint(api_key))
    if verified != expected:
        raise HTTPException(409, "먼저 현재 제공사·모델·API 키의 연결을 확인하세요.")
    state.llm_call_count += 1
    save_session(state)
    return generate_with_byok(request.provider, model, api_key, request.prompt, scenario_for(state))


@app.post("/api/sessions/{session_id}/deepseek")
def deepseek(session_id: str, request: DeepSeekRequest, http_request: FastAPIRequest) -> dict[str, Any]:
    enforce_llm_rate_limit(http_request)
    state = load_session(session_id)
    if not state:
        raise HTTPException(404, "세션을 찾을 수 없습니다.")
    if state.completed or current_stage(state) != "coach":
        raise HTTPException(409, "LLM Coach 단계에서만 DeepSeek을 호출할 수 있습니다.")
    if state.llm_call_count >= 2:
        raise HTTPException(429, "이 세션의 AI 분석 한도 2회에 도달했습니다.")
    state.llm_call_count += 1
    save_session(state)
    return deepseek_generate(request.prompt, session_id.replace("-", ""), scenario_for(state))


@app.post("/api/sessions/{session_id}/decisions")
def decide(session_id: str, request: DecisionRequest) -> dict[str, Any]:
    state = load_session(session_id)
    if not state:
        raise HTTPException(404, "세션을 찾을 수 없습니다.")
    result = apply_decision(state, request)
    save_session(state)
    if request.stage == "coach":
        with RATE_LOCK:
            VERIFIED_BYOK.pop(session_id, None)
    return result


@app.post("/api/sessions/{session_id}/restart", response_model=SessionState)
def restart(session_id: str) -> SessionState:
    previous = load_session(session_id)
    if not previous:
        raise HTTPException(404, "세션을 찾을 수 없습니다.")
    scenario = SCENARIOS.get(previous.scenario_id)
    if not scenario:
        raise HTTPException(409, "이 세션의 시나리오를 더 이상 찾을 수 없습니다.")
    state = SessionState(
        id=session_id,
        scenario_id=previous.scenario_id,
        scenario_version=scenario["version"],
        seed=previous.seed,
        budget=scenario["limits"]["budget"],
        time_left=scenario["limits"]["time"],
    )
    save_session(state)
    with RATE_LOCK:
        VERIFIED_BYOK.pop(session_id, None)
    return state


@app.post("/api/sessions/{session_id}/report")
def report(session_id: str, request: ReportRequest) -> Response:
    state = load_session(session_id)
    if not state:
        raise HTTPException(404, "세션을 찾을 수 없습니다.")
    if not state.completed:
        raise HTTPException(409, "시나리오 완료 후 면접 자료를 만들 수 있습니다.")
    document = build_report(state, request)
    return Response(
        content=document,
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=virtual-fab-interview-slides.html"},
    )


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
