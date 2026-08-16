from __future__ import annotations

import base64
import html
import json
import os
import sqlite3
import time
from pathlib import Path
from threading import Lock
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

APP_DIR = Path(__file__).resolve().parents[1]
DIST_DIR = APP_DIR / "dist"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash").strip()
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DB_PATH = Path(os.getenv("VIRTUAL_FAB_DB", str(APP_DIR / ".runtime" / "sessions.sqlite3")))
DB_LOCK = Lock()
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
    "version": "0.3.0",
    "notice": "교육용 합성 시나리오이며 실제 회사 Recipe·현장 경험을 의미하지 않습니다.",
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
    },
    "stages": [
        {"id": "incident", "label": "문제 발생", "station": "alert", "brief": "전체 평균은 합성 규격 안이지만 edge 결함률은 경고선을 넘었다. 후속 공정 투입 전 첫 조치를 결정해야 한다."},
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


class DeepSeekRequest(BaseModel):
    prompt: str = Field(min_length=20, max_length=2000)


class ReportRequest(BaseModel):
    opinion: str = Field(min_length=40, max_length=3000)
    presenter: str = Field(default="지원자", max_length=80)
    target_role: str = Field(default="반도체 공정기술", max_length=120)


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
        return SessionState.model_validate_json(row[0])
    except ValueError:
        with DB_LOCK, sqlite3.connect(DB_PATH, timeout=5) as connection:
            connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        return None


init_db()

app = FastAPI(title="Virtual Fab Scenario API", version="0.3.0")


CHOICE_LABELS = {
    "hold": "Lot 보류 후 분포 확인", "release_by_mean": "평균 CD만 보고 진행",
    "modify": "AI 제안을 수정해 사용", "accept": "AI 제안을 그대로 채택", "reject": "근거 부족으로 보류",
    "distribution": "위치·Tool·Lot 분포 분석", "mean_only": "전체 평균만 확인",
    "screening": "대조군 포함 Screening DOE", "ofat": "한 변수 확인 실험", "immediate": "검증 없이 Recipe 변경",
    "select": "정보가치 기반 분석 툴 선택",
    "controlled": "한정 적용 후 모니터링", "direct": "전체 Lot 즉시 적용", "release": "검증 없이 해제",
}


def deepseek_generate(prompt: str, user_id: str) -> dict[str, Any]:
    if not DEEPSEEK_API_KEY:
        raise HTTPException(503, "DeepSeek API 키가 아직 설정되지 않았습니다. 외부 AI 복사·붙여넣기를 이용하세요.")
    body = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "당신은 반도체 Photo 공정 학습자의 소크라테스식 멘토다. "
                    "교육용 합성 상황만 다루고 실제 회사 Recipe나 수치를 만들지 않는다. "
                    "정답을 단정하지 말고 경쟁 가설 3개, 각 가설을 반증할 최소 증거, "
                    "가장 먼저 할 저비용 측정을 한국어로 간결하게 제안한다."
                ),
            },
            {
                "role": "user",
                "content": (
                    "교육용 관찰: 전체 평균 CD 54.9 nm는 합성 규격 53–57 nm 안이지만, wafer edge 결함률은 최근 기준 0.8%에서 3.2%로 증가했다. 후속 Etch 투입까지 60분이며 아직 공정 변화·설비 편중·계측 편향은 확인하지 않았다.\n"
                    f"학습자 질문: {prompt}"
                ),
            },
        ],
        "thinking": {"type": "disabled"},
        "temperature": 0.2,
        "max_tokens": 500,
        "user_id": user_id,
    }).encode("utf-8")
    request = Request(
        DEEPSEEK_URL,
        data=body,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=90) as response:
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
        f"<li><b>{html.escape(next(stage['label'] for stage in SCENARIO['stages'] if stage['id'] == item['stage']))}</b>"
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
    return f"""<!doctype html><html lang='ko'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Virtual Fab 면접 PT · {safe_presenter}</title><style>
*{{box-sizing:border-box}}:root{{--ink:#071d24;--cyan:#00a8b5;--amber:#ffb21d;--paper:#f6f9f8}}body{{margin:0;background:var(--ink);font-family:'Malgun Gothic',sans-serif;color:var(--ink);overflow:hidden}}
.slide{{display:none;width:100vw;height:100vh;padding:7vh 7vw;background:var(--paper);position:relative}}.slide.active{{display:grid}}h1{{font-size:clamp(42px,6vw,88px);line-height:1.04;margin:0;max-width:13ch}}h2{{font-size:clamp(32px,4vw,64px);margin:0 0 4vh}}p,li{{font-size:clamp(17px,1.7vw,28px);line-height:1.6}}.dark{{background:var(--ink);color:#effafa}}.accent{{color:var(--amber)}}.grid{{grid-template-columns:1.1fr .9fr;gap:5vw;align-items:center}}img{{width:100%;max-height:62vh;object-fit:contain}}.metric{{display:flex;gap:4vw;border-top:3px solid var(--cyan);padding-top:3vh}}.metric b{{font-size:clamp(34px,5vw,72px);display:block;color:var(--amber)}}ul{{list-style:none;padding:0}}li{{display:grid;grid-template-columns:180px 1fr;gap:24px;border-top:1px solid #aababc;padding:1.5vh 0}}blockquote{{font-size:clamp(22px,2.5vw,42px);line-height:1.5;margin:0;border-top:5px solid var(--amber);padding-top:4vh}}.label{{position:absolute;top:3vh;left:7vw;font-size:14px;letter-spacing:.12em;color:var(--cyan);font-weight:700}}.nav{{position:fixed;right:24px;bottom:20px;display:flex;gap:8px;z-index:5}}button{{border:0;padding:12px 18px;background:#fff;color:var(--ink);font-weight:700;cursor:pointer}}.counter{{position:fixed;left:24px;bottom:24px;color:#9bc0c3;z-index:5}}small{{position:absolute;bottom:3vh;left:7vw;color:#637e83}}@media(max-width:760px){{.grid{{grid-template-columns:1fr}}.slide{{padding:8vh 6vw;overflow:auto}}li{{grid-template-columns:1fr;gap:4px}}}}@media print{{body{{overflow:visible}}.slide{{display:grid;page-break-after:always}}.nav,.counter{{display:none}}}}
</style></head><body>
<section class='slide dark active'><span class='label'>VIRTUAL FAB · INTERVIEW BRIEF</span><div><h1>사라진 선폭의 비밀</h1><p class='accent'>{safe_presenter} · {safe_role}</p><p>AI를 사용했지만 판단을 위임하지 않은 데이터 기반 문제해결 기록</p></div><small>교육용 합성 시나리오 · 실제 회사 Recipe 또는 현장 성과가 아님</small></section>
<section class='slide grid'><span class='label'>S · SITUATION</span><div><h2>평균은 통과했지만<br>Edge는 경고했다</h2><p>합성 평균 CD 54.9 nm는 규격 53–57 nm 안이었다. 그러나 edge 결함률은 최근 기준 0.8%에서 3.2%로 상승했고, 후속 Etch 투입까지 60분만 남았다.</p><p><b>초기 판단:</b> {html.escape(CHOICE_LABELS.get(incident.get('choice',''), '기록 없음'))}</p></div><img src='{wafer_svg}' alt='합성 wafer edge 결함 도식'></section>
<section class='slide'><span class='label'>T · TASK</span><div><h2>정답보다 입증 순서를 설계했다</h2><ul><li><b>데이터</b><span>결측·중복·단위·Tool 편중과 Center–Edge 분포 확인</span></li><li><b>실험</b><span>대조군·요인·반복·판정기준을 먼저 고정</span></li><li><b>책임</b><span>AI 제안과 사람의 검증 계획을 분리</span></li></ul></div></section>
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
    save_session(state)
    return state


@app.get("/api/sessions/{session_id}", response_model=SessionState)
def get_session(session_id: str) -> SessionState:
    state = load_session(session_id)
    if not state:
        raise HTTPException(404, "세션을 찾을 수 없습니다.")
    return state


@app.post("/api/sessions/{session_id}/deepseek")
def deepseek(session_id: str, request: DeepSeekRequest) -> dict[str, Any]:
    state = load_session(session_id)
    if not state:
        raise HTTPException(404, "세션을 찾을 수 없습니다.")
    if state.completed or current_stage(state) != "coach":
        raise HTTPException(409, "LLM Coach 단계에서만 DeepSeek을 호출할 수 있습니다.")
    return deepseek_generate(request.prompt, session_id.replace("-", ""))


@app.post("/api/sessions/{session_id}/decisions")
def decide(session_id: str, request: DecisionRequest) -> dict[str, Any]:
    state = load_session(session_id)
    if not state:
        raise HTTPException(404, "세션을 찾을 수 없습니다.")
    result = apply_decision(state, request)
    save_session(state)
    return result


@app.post("/api/sessions/{session_id}/restart", response_model=SessionState)
def restart(session_id: str) -> SessionState:
    if not load_session(session_id):
        raise HTTPException(404, "세션을 찾을 수 없습니다.")
    state = SessionState(id=session_id)
    save_session(state)
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
