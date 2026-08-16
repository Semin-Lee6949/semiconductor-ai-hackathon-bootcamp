import { FormEvent, useEffect, useMemo, useState, type CSSProperties } from 'react'
import { api } from './api'
import { EvidenceDrawer } from './components/EvidenceDrawer'
import { StageProgress } from './components/StageProgress'
import { FabScene } from './FabScene'
import { useFabSession } from './hooks/useFabSession'
import type { CoachResponse, Decision, Scenario, SessionState, StageId } from './types'
import './styles.css'

const CHOICE_LABELS: Record<string, string> = {
  hold: 'Lot 보류 후 분포 확인', release_by_mean: '평균 CD만 보고 진행',
  modify: 'AI 제안을 수정해 사용', accept: 'AI 제안을 그대로 채택', reject: '근거 부족으로 보류',
  distribution: '위치·Tool·Lot 분포 분석', mean_only: '전체 평균만 확인',
  screening: '대조군 포함 Screening DOE', ofat: '한 변수씩 확인', immediate: '즉시 Recipe 변경',
  controlled: '한정 적용 후 모니터링', direct: '전체 Lot 즉시 적용', release: '검증 없이 해제',
}

function SignalPlot() {
  const bars = [38, 41, 44, 47, 52, 58, 69, 78, 72, 60, 51, 46, 43, 40]
  return (
    <figure className="signal-plot">
      <figcaption>합성 Train 데이터 · wafer edge 결함률</figcaption>
      <svg viewBox="0 0 420 130" role="img" aria-label="웨이퍼 중심보다 가장자리에서 결함률이 증가하는 합성 데이터 막대그래프">
        <line x1="24" y1="104" x2="404" y2="104" />
        <line x1="24" y1="18" x2="24" y2="104" />
        <line className="spec" x1="24" y1="54" x2="404" y2="54" />
        {bars.map((height, index) => <rect key={index} x={32 + index * 26} y={104 - height} width="15" height={height} className={index > 5 && index < 10 ? 'risk' : ''} />)}
        <text x="30" y="123">CENTER</text><text x="350" y="123">EDGE</text><text x="340" y="49">warning</text>
      </svg>
    </figure>
  )
}

function ChoiceButton({ value, selected, children, onClick }: { value: string; selected: string; children: React.ReactNode; onClick: (value: string) => void }) {
  return <button type="button" className={`choice ${selected === value ? 'selected' : ''}`} onClick={() => onClick(value)}>{children}</button>
}

function ResourceMeter({ label, value, limit, unit }: { label: string; value: number; limit: number; unit: string }) {
  const ratio = limit > 0 ? Math.min(100, Math.round((value / limit) * 100)) : 100
  const risk = value > limit
  return <div className={`resource-meter ${risk ? 'over' : ''}`}><div><span>{label}</span><b>{value}{unit} / {limit}{unit}</b></div><div className="meter-track"><span style={{ '--meter-ratio': ratio / 100 } as CSSProperties} /></div></div>
}

function DecisionPanel({ scenario, state, onSubmit, onCoach, busy }: { scenario: Scenario; state: SessionState; onSubmit: (decision: Decision) => Promise<void>; onCoach: (question: string) => Promise<CoachResponse>; busy: boolean }) {
  const stage = scenario.stages[state.stage_index]
  const [choice, setChoice] = useState('')
  const [prompt, setPrompt] = useState('Photo CD edge 산포의 경쟁 가설 3개와 각 가설을 반증할 최소 증거를 제안해줘.')
  const [humanCheck, setHumanCheck] = useState('AI 제안은 공정 교재와 합성 데이터 분포, 측정 원리 및 대안 가설을 대조해 사람이 검증한다.')
  const [repeats, setRepeats] = useState(3)
  const [tools, setTools] = useState<string[]>(['optical', 'sem'])
  const [baseline, setBaseline] = useState('0.62')
  const [holdout, setHoldout] = useState('0.78')
  const [direction, setDirection] = useState('higher')
  const [mentorResponse, setMentorResponse] = useState('')
  const [mentorModel, setMentorModel] = useState('')
  const [coachBusy, setCoachBusy] = useState(false)
  const [coachError, setCoachError] = useState('')

  useEffect(() => setChoice(''), [stage.id])

  const totals = useMemo(() => tools.reduce((sum, id) => ({ cost: sum.cost + scenario.tools[id].cost, time: sum.time + scenario.tools[id].time }), { cost: 0, time: 0 }), [tools, scenario.tools])
  const validationPreview = useMemo(() => {
    const before = Number(baseline); const after = Number(holdout)
    if (!Number.isFinite(before) || !Number.isFinite(after)) return null
    const delta = after - before
    const improved = direction === 'higher' ? delta > 0 : delta < 0
    return { delta, improved }
  }, [baseline, holdout, direction])

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!choice) return
    const payload: Record<string, unknown> = {}
    if (stage.id === 'coach') Object.assign(payload, { prompt, human_check: humanCheck, llm_response: mentorResponse, llm_model: mentorModel })
    if (stage.id === 'experiment') payload.repeats = repeats
    if (stage.id === 'analysis') payload.tools = tools
    if (stage.id === 'validation') payload.metrics = { baseline, holdout, direction }
    await onSubmit({ stage: stage.id as StageId, choice, payload })
  }

  const askCoach = async () => {
    setCoachBusy(true); setCoachError('')
    try {
      const result = await onCoach(prompt)
      setMentorResponse(result.response); setMentorModel(result.model)
    } catch (cause) { setCoachError(cause instanceof Error ? cause.message : 'Ollama 응답을 받지 못했어.') }
    finally { setCoachBusy(false) }
  }

  return (
    <form className="decision-panel" onSubmit={submit}>
      <div className="stage-heading"><span>{String(state.stage_index + 1).padStart(2, '0')}</span><h2>{stage.label}</h2></div>
      <p className="brief">{stage.brief}</p>
      {stage.id === 'incident' && <><SignalPlot /><div className="choice-grid"><ChoiceButton value="hold" selected={choice} onClick={setChoice}>Lot 보류<br/><small>분포와 위치 패턴부터 확인</small></ChoiceButton><ChoiceButton value="release_by_mean" selected={choice} onClick={setChoice}>공정 진행<br/><small>평균 CD가 규격 안이므로 통과</small></ChoiceButton></div></>}
      {stage.id === 'coach' && <>
        <label>LLM에게 보낼 질문<textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} /></label>
        <button type="button" className="ollama-call" onClick={askCoach} disabled={coachBusy || prompt.length < 20}>{coachBusy ? '서버 Ollama가 질문 생성 중… 약 40~60초' : '검증 프레임 + Ollama 질문 생성'}</button>
        {mentorResponse && <div className="mentor-answer"><div><b>LOCAL LLM</b><span>{mentorModel}</span></div><p>{mentorResponse}</p></div>}
        {coachError && <p className="inline-error">{coachError}</p>}
        <label>사람의 검증 계획<textarea value={humanCheck} onChange={(e) => setHumanCheck(e.target.value)} /></label>
        <div className="choice-grid three"><ChoiceButton value="modify" selected={choice} onClick={setChoice}>수정 채택</ChoiceButton><ChoiceButton value="accept" selected={choice} onClick={setChoice}>그대로 채택</ChoiceButton><ChoiceButton value="reject" selected={choice} onClick={setChoice}>근거 부족</ChoiceButton></div>
        <p className="field-note">검증 프레임은 코드가 고정하고, 서버 Ollama는 사고를 확장할 질문만 만든다. CPU 추론에 약 40~60초가 걸리며 판단 책임은 사용자에게 있다.</p>
      </>}
      {stage.id === 'data' && <><SignalPlot /><div className="checklist"><span>결측·중복·단위</span><span>Tool·Lot 편중</span><span>Center–Edge 분포</span><span>Train–Holdout 분리</span></div><div className="choice-grid"><ChoiceButton value="distribution" selected={choice} onClick={setChoice}>분포로 판단</ChoiceButton><ChoiceButton value="mean_only" selected={choice} onClick={setChoice}>평균으로 판단</ChoiceButton></div></>}
      {stage.id === 'experiment' && <>
        <div className="choice-list"><ChoiceButton value="screening" selected={choice} onClick={setChoice}>대조군 + Dose·Focus·PEB Screening</ChoiceButton><ChoiceButton value="ofat" selected={choice} onClick={setChoice}>한 변수씩 변경</ChoiceButton><ChoiceButton value="immediate" selected={choice} onClick={setChoice}>검증 없이 Recipe 변경</ChoiceButton></div>
        <label>조건별 반복 횟수<input type="number" min="2" max="10" value={repeats} onChange={(e) => setRepeats(Number(e.target.value))} /></label>
        <p className="field-note">합성 실험의 판정 기준을 먼저 고정한 뒤 Holdout을 연다.</p>
      </>}
      {stage.id === 'analysis' && <>
        <div className="tool-grid">{Object.entries(scenario.tools).map(([id, tool]) => <label className={`tool ${tools.includes(id) ? 'selected' : ''}`} key={id}><input type="checkbox" checked={tools.includes(id)} onChange={() => setTools((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id])}/><b>{tool.label}</b><span>{tool.kind} · {tool.cost}C · {tool.time}m{tool.destructive ? ' · 파괴' : ''}</span></label>)}</div>
        <div className="resource-preview" aria-live="polite"><ResourceMeter label="선택 비용" value={totals.cost} limit={state.budget} unit="C"/><ResourceMeter label="소요 시간" value={totals.time} limit={state.time_left} unit="m"/></div>
        <input type="hidden" value="select" /><button type="button" className="choice selected analysis-choice" onClick={() => setChoice('select')}>이 분석 조합으로 증거 수집</button>
      </>}
      {stage.id === 'validation' && <>
        <div className="metric-grid"><label>Baseline<input inputMode="decimal" value={baseline} onChange={(e) => setBaseline(e.target.value)} /></label><label>Holdout<input inputMode="decimal" value={holdout} onChange={(e) => setHoldout(e.target.value)} /></label><label>개선 방향<select value={direction} onChange={(e) => setDirection(e.target.value)}><option value="higher">높을수록 개선</option><option value="lower">낮을수록 개선</option></select></label></div>
        {validationPreview && <div className={`validation-preview ${validationPreview.improved ? 'improved' : 'degraded'}`} role="status"><span>LIVE HOLDOUT PREVIEW</span><b>{validationPreview.delta >= 0 ? '+' : ''}{validationPreview.delta.toFixed(3)}</b><p>{validationPreview.improved ? '설정한 개선 방향과 일치해. 적용 범위를 선택해.' : '개선 방향과 불일치해. 조치보다 가설·실험을 다시 의심해야 해.'}</p></div>}
        <div className="choice-list"><ChoiceButton value="controlled" selected={choice} onClick={setChoice}>한정 적용 + 모니터링</ChoiceButton><ChoiceButton value="direct" selected={choice} onClick={setChoice}>전체 Lot 즉시 적용</ChoiceButton><ChoiceButton value="release" selected={choice} onClick={setChoice}>검증 없이 해제</ChoiceButton></div>
      </>}
      <button className="commit" disabled={!choice || busy || (stage.id === 'coach' && !mentorResponse)}>{busy ? '판단 기록 중…' : '판단을 기록하고 다음 스테이션으로'}</button>
    </form>
  )
}

function ResultPanel({ scenario, session, busy, onRestart }: { scenario: Scenario; session: SessionState; busy: boolean; onRestart: () => Promise<void> }) {
  const [presenter, setPresenter] = useState('지원자')
  const [targetRole, setTargetRole] = useState('반도체 공정기술')
  const [opinion, setOpinion] = useState('')
  const [reportBusy, setReportBusy] = useState(false)
  const [reportError, setReportError] = useState('')

  const downloadReport = async () => {
    setReportBusy(true); setReportError('')
    try {
      const blob = await api.report(session.id, { opinion, presenter, target_role: targetRole })
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url; anchor.download = 'virtual-fab-interview-slides.html'; anchor.click()
      URL.revokeObjectURL(url)
    } catch (cause) { setReportError(cause instanceof Error ? cause.message : '면접 자료를 만들지 못했어.') }
    finally { setReportBusy(false) }
  }

  return <div className="result-panel">
    <h1>{session.verdict}</h1>
    <p>점수 {session.score}/100 · 남은 예산 {session.budget} · 남은 시간 {session.time_left}분</p>
    <h2>Evidence trail</h2>
    <ol>{session.history.map((item, index) => (
      <li key={`${item.stage}-${index}`}>
        <b>{scenario.stages.find((stage) => stage.id === item.stage)?.label}</b>
        <span>{item.tools?.map((id) => scenario.tools[id]?.label).join(' + ') || CHOICE_LABELS[item.choice] || item.choice}</span>
      </li>
    ))}</ol>
    <section className="report-builder">
      <h2>내 의견을 면접 PT로 전환</h2>
      <div className="identity-grid"><label>발표자<input value={presenter} onChange={(event) => setPresenter(event.target.value)} /></label><label>지원 직무<input value={targetRole} onChange={(event) => setTargetRole(event.target.value)} /></label></div>
      <label>내 판단·배운 점·한계<textarea value={opinion} onChange={(event) => setOpinion(event.target.value)} placeholder="왜 이 경로를 선택했는지, AI 의견 중 무엇을 수정했는지, 실제 현장 적용 전 무엇을 추가 검증할지 40자 이상 적어봐." /></label>
      <p className="field-note">웨이퍼·분석 툴 SVG를 Base64로 내장한 9장 독립형 HTML 슬라이드를 생성한다. 다운로드 후 인터넷 없이 실행하고 PDF 인쇄도 가능해.</p>
      <button className="download-report" onClick={downloadReport} disabled={reportBusy || opinion.trim().length < 40}>{reportBusy ? 'STAR 면접 자료 생성 중…' : 'Base64 HTML 면접 슬라이드 다운로드'}</button>
      {reportError && <p className="inline-error">{reportError}</p>}
    </section>
    <p className="limit-note">이 결과는 교육용 합성 입력에 대한 시나리오 판정이며 실제 공정 인과관계나 현장 성과를 보장하지 않아.</p>
    <button className="commit secondary" onClick={onRestart} disabled={busy}>다른 경로로 다시 실험</button>
  </div>
}

export default function App() {
  const { scenario, session, feedback, error, busy, decide, restart, setFeedback } = useFabSession()
  const [drawerOpen, setDrawerOpen] = useState(false)

  if (!scenario || !session) return <main className="loading"><div className="loader"/><p>{error || '가상 팹을 준비하고 있어…'}</p></main>

  return (
    <main className="app-shell">
      <header className="topbar">
        <div><a className="brand" href="./">VIRTUAL FAB</a><span className="scenario-name">{scenario.title}</span></div>
        <div className="status-strip"><span>SCORE <b>{session.score}</b></span><span>BUDGET <b>{session.budget}</b></span><span>TIME <b>{session.time_left}m</b></span><button type="button" onClick={() => setDrawerOpen(true)}>EVIDENCE <b>{session.history.length}</b></button></div>
      </header>
      <StageProgress scenario={scenario} session={session}/>
      <section className="workspace">
        <div className="visual-column">
          <FabScene scenario={scenario} session={session} onStationSelect={(index) => setFeedback(index === session.stage_index ? `${scenario.stages[index].label} 스테이션이 열렸어.` : index < session.stage_index ? '이미 완료한 스테이션이야. 기록은 아래에서 확인해.' : '앞 단계의 근거를 먼저 남겨야 열려.')} />
          <div className="feedback" role="status"><span>LIVE NOTE</span><p>{feedback}</p></div>
        </div>
        <aside className="workbench">
          <div className="stage-transition" key={session.completed ? 'result' : scenario.stages[session.stage_index].id}>{session.completed
              ? <ResultPanel scenario={scenario} session={session} busy={busy} onRestart={restart}/>
              : <DecisionPanel scenario={scenario} state={session} onSubmit={decide} onCoach={(question) => api.coach(session.id, question)} busy={busy}/>
          }</div>
          {error && <div className="error" role="alert"><b>기록 실패</b><span>{error}</span></div>}
        </aside>
      </section>
      <EvidenceDrawer open={drawerOpen} scenario={scenario} session={session} onClose={() => setDrawerOpen(false)}/>
      <footer><p>{scenario.notice}</p><p>React · Three.js · FastAPI / scenario v{scenario.version}</p></footer>
    </main>
  )
}
