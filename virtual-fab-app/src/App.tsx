import { FormEvent, useEffect, useMemo, useState, type CSSProperties } from 'react'
import { api } from './api'
import { CleanroomLobby } from './CleanroomLobby'
import { EvidenceDrawer } from './components/EvidenceDrawer'
import { PersonalAIConnector } from './components/PersonalAIConnector'
import { StageProgress } from './components/StageProgress'
import { FabScene } from './FabScene'
import { useFabSession } from './hooks/useFabSession'
import type { AIExchange, Decision, Scenario, ScenarioSummary, SessionState, StageId } from './types'
import './styles.css'

const CHOICE_LABELS: Record<string, string> = {
  hold: '판정 보류 후 분포 확인', release_by_mean: '대표 평균값만 보고 진행',
  modify: 'AI 제안을 수정해 사용', accept: 'AI 제안을 그대로 채택', reject: '근거 부족으로 보류',
  distribution: '위치·Tool·Lot 분포 분석', mean_only: '전체 평균만 확인',
  screening: '대조군 포함 Screening DOE', ofat: '한 변수씩 확인', immediate: '즉시 Recipe 변경',
  controlled: '한정 적용 후 모니터링', direct: '전체 Lot 즉시 적용', release: '검증 없이 해제',
}

const QUESTION_PHASES = [
  { id: 'understand', range: '1–2', label: '용어·데이터 이해', goal: '용어 정의와 데이터 열·단위·결측을 확인' },
  { id: 'hypothesize', range: '3–4', label: '경쟁 가설', goal: '서로 다른 원인과 예상 데이터 패턴 비교' },
  { id: 'falsify', range: '5–6', label: '반증·누락 점검', goal: '틀린 가설을 제거할 최소 증거 확인' },
  { id: 'decide', range: '7–8', label: '판단 압축', goal: '실험 우선순위·리스크·적용 한계 정리' },
  { id: 'synthesize', range: '9–15', label: 'PT 심화', goal: '반론·한계·면접 질문까지 선택적으로 보강' },
]
const MIN_DEEP_DIALOGUE_TURNS = 8

function phaseForTurn(turn: number) {
  if (turn <= 2) return QUESTION_PHASES[0]
  if (turn <= 4) return QUESTION_PHASES[1]
  if (turn <= 6) return QUESTION_PHASES[2]
  if (turn <= 8) return QUESTION_PHASES[3]
  return QUESTION_PHASES[4]
}

function tokenSummary(usage: AIExchange['usage']) {
  const thought = usage.thought_tokens ?? 0
  return thought > 0
    ? `응답 ${usage.completion_tokens.toLocaleString()} · 사고 ${thought.toLocaleString()} · 전체 ${usage.total_tokens.toLocaleString()} tokens`
    : `응답 ${usage.completion_tokens.toLocaleString()} · 전체 ${usage.total_tokens.toLocaleString()} tokens`
}

function deepQuestionForTurn(turn: number, scenario: Scenario, terms: string[]) {
  const keywords = terms.length > 0 ? terms.join(', ') : scenario.keywords.slice(0, 2).map((item) => item.term).join(', ')
  const requests = [
    '다운로드한 합성 CSV의 열·단위·결측 행을 먼저 점검하고, 분석에서 제외하거나 보존할 기준을 설명해줘.',
    '합성 CSV의 Lot·Tool·wafer zone별 평균과 범위를 비교하고, CENTER와 EDGE 차이가 의미하는 공간 패턴을 수치로 해석해줘.',
    '앞서 확인한 데이터 패턴을 설명할 수 있는 서로 독립적인 경쟁 가설 3개를 만들고, 각 가설의 공정 메커니즘을 설명해줘.',
    '세 경쟁 가설이 맞다면 Lot·Tool·wafer zone 데이터에서 각각 어떤 패턴이 나와야 하는지 예측표처럼 비교해줘.',
    '각 경쟁 가설을 기각할 최소 증거와 가장 정보가치가 높은 추가 측정 또는 대조군을 우선순위로 정리해줘.',
    '지금까지 놓친 교란변수·계측 편향·인과관계 비약을 비판하고, 현재 데이터만으로 말할 수 없는 것을 분리해줘.',
    '현재까지의 데이터와 반증 결과를 바탕으로 우선 가설, 보류 가설, 실험 조건, 판정 기준을 하나의 의사결정안으로 압축해줘.',
    '면접 PT에 넣을 수 있도록 상황, 실제 데이터 수치, 경쟁 가설, 반증 과정, 사람의 최종 판단과 한계를 연결해 요약해줘.',
  ]
  const request = requests[turn - 1] ?? '이 결론에 대한 가장 강한 반론과 추가 검증 한계를 제시하고 면접관의 예상 질문에 답해줘.'
  return `[문답 ${turn}/15 · ${phaseForTurn(turn).label}]\n[핵심 키워드] ${keywords}\n[데이터 연결] 이 사이트가 현재 세션의 서버 CSV 원문 42행과 통계 요약을 자동 첨부함. PC 다운로드 경로는 사용하지 말 것\n[데이터 조건] 첨부된 교육용 합성 CSV의 실제 행 수·결측·Lot·Tool·wafer zone 통계를 근거로 사용할 것\n[질문] ${request}\n[출력 형식] 데이터 근거 / 해석 / 가설 또는 판단 / 반증 기준 / 남은 불확실성 / 추천 후속 질문`
}

function SignalPlot({ scenario }: { scenario: Scenario }) {
  const signal = scenario.signal
  return (
    <figure className="signal-plot">
      <figcaption>{signal.title}</figcaption>
      <svg viewBox="0 0 420 130" role="img" aria-label={signal.aria}>
        <line x1="24" y1="104" x2="404" y2="104" />
        <line x1="24" y1="18" x2="24" y2="104" />
        <line className="spec" x1="24" y1={signal.warning} x2="404" y2={signal.warning} />
        {signal.bars.map((height, index) => <rect key={index} x={32 + index * 26} y={104 - height} width="15" height={height} className={index >= signal.risk_from ? 'risk' : ''} />)}
        <text x="30" y="123">{signal.start}</text><text x="350" y="123">{signal.end}</text><text x="340" y={signal.warning - 5}>warning</text>
      </svg>
    </figure>
  )
}

function IncidentBrief({ scenario }: { scenario: Scenario }) {
  const incident = scenario.incident
  return <section className="incident-case" aria-labelledby="incident-case-title">
    <header><div><span>CASE {incident.case_id}</span><h3 id="incident-case-title">교대 직전, 판단이 필요한 이상 신호</h3></div><b>{incident.deadline}</b></header>
    <p className="role-brief"><strong>너의 역할</strong>{incident.role}. 이상 신호는 확인됐지만 아직 원인은 확정되지 않았다.</p>
    <div className="incident-facts">{incident.facts.map((fact) => <div key={fact.label}><span>{fact.label}</span><b>{fact.value}</b><small>{fact.note}</small></div>)}</div>
    <div className="incident-unknowns"><strong>아직 모르는 것</strong><ul>{incident.unknowns.map((item) => <li key={item}>{item}</li>)}</ul></div>
    <p className="decision-call"><span>지금 결정할 것</span>{incident.decision}</p>
  </section>
}

function ChoiceButton({ value, selected, children, onClick }: { value: string; selected: string; children: React.ReactNode; onClick: (value: string) => void }) {
  return <button type="button" className={`choice ${selected === value ? 'selected' : ''}`} onClick={() => onClick(value)}>{children}</button>
}

function ResourceMeter({ label, value, limit, unit }: { label: string; value: number; limit: number; unit: string }) {
  const ratio = limit > 0 ? Math.min(100, Math.round((value / limit) * 100)) : 100
  const risk = value > limit
  return <div className={`resource-meter ${risk ? 'over' : ''}`}><div><span>{label}</span><b>{value}{unit} / {limit}{unit}</b></div><div className="meter-track"><span style={{ '--meter-ratio': ratio / 100 } as CSSProperties} /></div></div>
}

function DecisionPanel({ scenario, state, onSubmit, busy }: { scenario: Scenario; state: SessionState; onSubmit: (decision: Decision) => Promise<void>; busy: boolean }) {
  const stage = scenario.stages[state.stage_index]
  const [choice, setChoice] = useState('')
  const [prompt, setPrompt] = useState(() => deepQuestionForTurn(1, scenario, scenario.keywords.slice(0, 2).map((item) => item.term)))
  const [humanCheck, setHumanCheck] = useState('AI 제안은 공정 교재와 합성 데이터 분포, 측정 원리 및 대안 가설을 대조해 사람이 검증한다.')
  const [repeats, setRepeats] = useState(3)
  const [tools, setTools] = useState<string[]>(['optical', 'sem'])
  const [baseline, setBaseline] = useState('0.62')
  const [holdout, setHoldout] = useState('0.78')
  const [direction, setDirection] = useState('higher')
  const restoredConversation = state.ai_conversation ?? []
  const restoredLast = restoredConversation.at(-1)
  const [conversation, setConversation] = useState<AIExchange[]>(restoredConversation)
  const [externalResponse, setExternalResponse] = useState(restoredLast?.response ?? '')
  const [externalModel, setExternalModel] = useState(restoredLast ? `${restoredLast.provider_label} · ${restoredLast.model}` : 'Gemini')
  const [copyStatus, setCopyStatus] = useState('')
  const [responseCopyStatus, setResponseCopyStatus] = useState('')
  const [latestUsage, setLatestUsage] = useState<AIExchange['usage'] | null>(restoredLast?.usage ?? null)
  const [manualDraft, setManualDraft] = useState(restoredConversation.length === 0)
  const [datasetDownloaded, setDatasetDownloaded] = useState(state.dataset_downloaded)
  const [datasetBusy, setDatasetBusy] = useState(false)
  const [datasetError, setDatasetError] = useState('')
  const [selectedKeywordIds, setSelectedKeywordIds] = useState<string[]>(scenario.keywords.slice(0, 2).map((item) => item.id))
  const [questionGoal, setQuestionGoal] = useState(phaseForTurn(restoredConversation.length + 1).id)
  const datasetSourcePath = `${import.meta.env.BASE_URL}api/sessions/${state.id}/dataset.csv`

  useEffect(() => setChoice(''), [stage.id])

  const currentTurn = Math.min(conversation.length + 1, 15)
  const currentPhase = phaseForTurn(currentTurn)
  const matchedTerms = scenario.keywords.filter((item) => prompt.toLocaleLowerCase().includes(item.term.toLocaleLowerCase())).map((item) => item.term)
  const selectedTerms = scenario.keywords.filter((item) => selectedKeywordIds.includes(item.id)).map((item) => item.term)
  useEffect(() => setQuestionGoal(currentPhase.id), [conversation.length, currentPhase.id])

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
    if (stage.id === 'investigation') {
      const recordedConversation = conversation.length > 0 ? conversation : [{ turn_no: 1, question: prompt, response: externalResponse, provider_label: externalModel, model: externalModel, usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 }, keywords: matchedTerms, phase: { id: currentPhase.id, label: currentPhase.label, goal: currentPhase.goal } }]
      Object.assign(payload, { prompt, human_check: humanCheck, llm_response: externalResponse, llm_model: externalModel, ai_conversation: recordedConversation, dataset_downloaded: datasetDownloaded })
    }
    if (stage.id === 'experiment') payload.repeats = repeats
    if (stage.id === 'analysis') payload.tools = tools
    if (stage.id === 'validation') payload.metrics = { baseline, holdout, direction }
    await onSubmit({ stage: stage.id as StageId, choice, payload })
  }

  const copyPrompt = async () => {
    try { await navigator.clipboard.writeText(prompt); setCopyStatus('프롬프트를 복사했어. 외부 AI에서 실행한 뒤 답변을 붙여넣어.') }
    catch { setCopyStatus('자동 복사가 막혔어. 질문 상자를 직접 선택해 복사해줘.') }
  }

  const copyResponse = async () => {
    try { await navigator.clipboard.writeText(externalResponse); setResponseCopyStatus('응답을 복사했어.') }
    catch { setResponseCopyStatus('자동 복사가 막혔어. 응답 편집칸에서 직접 선택해 복사해줘.') }
  }

  const composeQuestion = () => {
    const facts = scenario.incident.facts.map((fact) => `${fact.label} ${fact.value}`).join(', ')
    const requests: Record<string, string> = {
      understand: '각 키워드가 CSV의 어떤 열·분포와 연결되는지 설명하고, 먼저 확인할 데이터 품질 항목을 순서대로 제시해줘.',
      hypothesize: '서로 겹치지 않는 경쟁 가설 3개를 만들고, 각 가설이 맞을 때 예상되는 Lot·Tool·위치별 패턴을 비교해줘.',
      falsify: '각 가설을 기각할 최소 증거와 아직 누락된 교란변수를 제시하고, 가장 정보가치가 높은 다음 분석을 추천해줘.',
      decide: '지금까지의 데이터와 문답을 바탕으로 우선 가설, 대조군, 판정 기준, 적용 리스크와 보류 조건을 정리해줘.',
      synthesize: '면접 PT용으로 상황, 데이터 품질, 핵심 가설, 반증 과정, 사람의 최종 판단과 한계를 STAR 구조로 요약해줘.',
    }
    setPrompt(`[문답 ${currentTurn}/15 · ${currentPhase.label}]\n[핵심 키워드] ${selectedTerms.join(', ')}\n[데이터 연결] 이 사이트가 현재 세션의 서버 CSV 원문 42행과 통계 요약을 자동 첨부함. PC 다운로드 경로는 사용하지 말 것\n[현재 관찰] ${facts}\n[질문] ${requests[questionGoal]}\n[출력 형식] 데이터 근거 / 가설 또는 판단 / 반증 기준 / 다음 행동을 구분해 한국어로 답해줘.`)
  }

  const downloadDataset = async () => {
    setDatasetBusy(true); setDatasetError('')
    try {
      const { blob, filename } = await api.dataset(state.id)
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url; anchor.download = filename; document.body.appendChild(anchor); anchor.click(); anchor.remove()
      window.setTimeout(() => URL.revokeObjectURL(url), 1000)
      setDatasetDownloaded(true)
    } catch (cause) { setDatasetError(cause instanceof Error ? cause.message : '합성 데이터를 내려받지 못했어.') }
    finally { setDatasetBusy(false) }
  }

  const receiveAIResult = (result: import('./types').BYOKResponse) => {
    const exchange: AIExchange = { turn_no: result.turn_no ?? conversation.length + 1, question: prompt, response: result.response, provider_label: result.provider_label, model: result.model, usage: result.usage, keywords: result.keywords ?? matchedTerms, phase: result.phase ?? { id: currentPhase.id, label: currentPhase.label, goal: currentPhase.goal }, finish_reason: result.finish_reason, retry_count: result.retry_count }
    setConversation((current) => [...current, exchange].slice(-15))
    setExternalResponse(result.response)
    setExternalModel(`${result.provider_label} · ${result.model}`)
    setLatestUsage(result.usage)
    setManualDraft(false)
    const nextTurn = Math.min(exchange.turn_no + 1, 15)
    if (exchange.turn_no < 15) setPrompt(deepQuestionForTurn(nextTurn, scenario, selectedTerms))
  }

  const editExternalResponse = (value: string) => {
    setExternalResponse(value)
    setResponseCopyStatus('')
    if (!manualDraft) setConversation((current) => current.map((exchange, index) => index === current.length - 1 ? { ...exchange, response: value } : exchange))
  }

  const startManualDraft = () => {
    setManualDraft(true)
    setExternalResponse('')
    setExternalModel('외부 AI · 수동 기록')
    setLatestUsage(null)
    setResponseCopyStatus('새 후속 질문의 외부 AI 답변을 붙여넣어.')
  }

  const recordManualExchange = () => {
    if (externalResponse.trim().length < 20 || matchedTerms.length === 0 || conversation.length >= 15) return
    const turn = conversation.length + 1
    const phase = phaseForTurn(turn)
    const exchange: AIExchange = { turn_no: turn, question: prompt, response: externalResponse.trim(), provider_label: '외부 AI · 수동', model: 'copy-and-paste', usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 }, keywords: matchedTerms, phase: { id: phase.id, label: phase.label, goal: phase.goal } }
    setConversation((current) => [...current, exchange].slice(-15))
    setExternalResponse('')
    setResponseCopyStatus(`Q${turn} 문답을 기록했어. 다음 질문의 답변을 붙여넣어.`)
    if (turn < 15) setPrompt(deepQuestionForTurn(turn + 1, scenario, selectedTerms))
  }

  return (
    <form className="decision-panel" onSubmit={submit}>
      <div className="stage-heading"><span>{String(state.stage_index + 1).padStart(2, '0')}</span><h2>{stage.label}</h2></div>
      <p className="brief">{stage.brief}</p>
      {stage.id === 'incident' && <><IncidentBrief scenario={scenario}/><SignalPlot scenario={scenario} /><div className="choice-grid"><ChoiceButton value="hold" selected={choice} onClick={setChoice}>{scenario.incident.choices.hold[0]}<br/><small>{scenario.incident.choices.hold[1]}</small></ChoiceButton><ChoiceButton value="release_by_mean" selected={choice} onClick={setChoice}>{scenario.incident.choices.release[0]}<br/><small>{scenario.incident.choices.release[1]}</small></ChoiceButton></div></>}
      {stage.id === 'investigation' && <>
        <SignalPlot scenario={scenario} />
        <section className={`dataset-panel ${datasetDownloaded ? 'ready' : ''}`}>
          <div><b>STEP 1 · 합성 원시 데이터 확보</b><p>3개 Lot의 위치·Tool·결측 플래그가 포함된 CSV를 내려받아 엑셀·Python 등으로 직접 확인해.</p></div>
          <button type="button" onClick={downloadDataset} disabled={datasetBusy}>{datasetBusy ? 'CSV 생성 중…' : datasetDownloaded ? 'CSV 다시 다운로드' : '합성 데이터 CSV 다운로드'}</button>
          <small>{datasetDownloaded ? `다운로드 완료 · scenario v${state.scenario_version} · seed ${state.seed} · AI 질문에 동일 CSV 42행 자동 첨부` : '데이터를 내려받아야 최종 데이터 판단을 기록할 수 있어.'}</small>
          {datasetDownloaded && <div className="dataset-ai-note" role="status"><b>AI 데이터 자동 연결됨</b><p>브라우저 보안상 PC의 Downloads 폴더 경로는 찾거나 읽지 않아. 대신 사이트가 아래 서버 데이터 경로에서 동일 seed의 CSV를 확인하고, 원문 42행과 통계 요약을 Gemini 요청에 직접 넣어.</p><code>{datasetSourcePath}</code><small>`C:\Users\…\파일.csv` 경로를 질문에 붙일 필요가 없어.</small></div>}
          {datasetError && <p className="inline-error" role="alert">{datasetError}</p>}
        </section>
        <div className="checklist"><span>결측·중복·단위</span><span>설비·Lot 편중</span><span>공간·조건별 분포</span><span>Train–Holdout 분리</span></div>
        <section className="question-strategy" aria-labelledby="question-strategy-title">
          <header><div><b id="question-strategy-title">심층 문답 · 최소 8회, 최대 15회</b><p>데이터 수치부터 반증과 판단까지 단계별로 연결해.</p></div><strong>{currentTurn}/15 · {currentPhase.label}</strong></header>
          <ol>{QUESTION_PHASES.map((phase) => <li key={phase.id} className={phase.id === currentPhase.id ? 'active' : QUESTION_PHASES.indexOf(phase) < QUESTION_PHASES.indexOf(currentPhase) ? 'done' : ''}><span>{phase.range}회</span><b>{phase.label}</b><small>{phase.goal}</small></li>)}</ol>
          <div className={`deep-dialogue-gate ${conversation.length >= MIN_DEEP_DIALOGUE_TURNS ? 'ready' : ''}`}><b>{conversation.length >= MIN_DEEP_DIALOGUE_TURNS ? '심층 분석 완료 조건 충족' : `심층 분석까지 ${MIN_DEEP_DIALOGUE_TURNS - conversation.length}회 남음`}</b><span>{conversation.length}/8 필수 · {Math.max(0, 15 - conversation.length)}회 추가 사용 가능</span></div>
          <div className="keyword-library"><div><b>{scenario.process} 핵심 키워드</b><span>뜻을 읽고 이번 질문에 사용할 용어를 선택해.</span></div>{scenario.keywords.map((keyword) => <button type="button" key={keyword.id} className={selectedKeywordIds.includes(keyword.id) ? 'selected' : ''} aria-pressed={selectedKeywordIds.includes(keyword.id)} onClick={() => setSelectedKeywordIds((current) => current.includes(keyword.id) ? current.filter((id) => id !== keyword.id) : [...current, keyword.id])}><b>{keyword.term}</b><span>{keyword.meaning}</span><small>{keyword.relevance}</small></button>)}</div>
          <div className="question-composer"><label>이번 질문의 목표<select value={questionGoal} onChange={(event) => setQuestionGoal(event.target.value)}>{QUESTION_PHASES.map((phase) => <option key={phase.id} value={phase.id}>{phase.label} · {phase.goal}</option>)}</select></label><button type="button" onClick={composeQuestion} disabled={selectedTerms.length === 0}>선택 키워드로 질문 초안 만들기</button></div>
          <p className={`prompt-quality ${matchedTerms.length > 0 ? 'ready' : ''}`}>{matchedTerms.length > 0 ? `전송 준비 · 포함 키워드: ${matchedTerms.join(', ')}` : '질문에 공정 핵심 키워드를 1개 이상 포함해야 해.'}</p>
          <p className="keyword-sources">용어 참고: {scenario.keyword_sources.map((source) => <a key={source.url} href={source.url} target="_blank" rel="noreferrer">{source.label}</a>)}</p>
        </section>
        {conversation.length > 0 && <section className="ai-dialogue" aria-label="AI 문답 기록"><header><b>STEP 2 · AI 문답 기록</b><span>{conversation.length}/15회</span></header>{conversation.map((exchange) => <article key={exchange.turn_no}><div><b>Q{exchange.turn_no} · {exchange.phase?.label ?? '문답'}</b><p>{exchange.question}</p><small>{exchange.keywords?.join(' · ') || '키워드 기록 없음'}</small></div><div><b>{exchange.provider_label}</b><p>{exchange.response}</p><small>{exchange.model} · {tokenSummary(exchange.usage)}</small></div></article>)}</section>}
        <label>AI에게 물어볼 다음 질문<textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="예: CSV의 결측을 처리한 뒤 Lot·Tool·위치 효과를 어떤 순서로 비교해야 해?" /></label>
        <PersonalAIConnector sessionId={state.id} prompt={prompt} promptReady={matchedTerms.length > 0} callsUsed={state.llm_call_count} conversation={conversation} onPromptChange={setPrompt} onResult={receiveAIResult}/>
        <section className={`ai-response-editor ${externalResponse ? 'has-response' : ''}`} aria-labelledby="ai-response-title">
          <header><div><b id="ai-response-title">최근 AI 응답</b><span>{manualDraft ? '외부 AI 답변을 붙여넣고 회차별로 기록' : '연결 AI 응답 확인·수정 가능'}</span></div><div className="response-actions"><button type="button" onClick={copyResponse} disabled={!externalResponse}>응답 복사</button>{!manualDraft && <button type="button" onClick={startManualDraft}>수동 문답 시작</button>}</div></header>
          <textarea aria-label="외부 AI 분석 답변 붙여넣기" value={externalResponse} onChange={(event) => editExternalResponse(event.target.value)} placeholder="AI 연결 응답이 여기에 자동으로 표시돼. 또는 Gemini·ChatGPT·Claude 등에서 받은 답변을 직접 붙여넣어." />
          {manualDraft && <button type="button" className="record-manual-turn" onClick={recordManualExchange} disabled={externalResponse.trim().length < 20 || matchedTerms.length === 0 || conversation.length >= 15}>현재 질문·답변을 문답 기록에 추가</button>}
          {latestUsage && <p className="response-ready" role="status">{externalModel} 응답이 자동 입력됐어 · {tokenSummary(latestUsage)}</p>}
          {responseCopyStatus && <p className="copy-status" role="status">{responseCopyStatus}</p>}
        </section>
        <button type="button" className="prompt-copy secondary full-width-action" onClick={copyPrompt} disabled={prompt.length < 10 || matchedTerms.length === 0}>개인 키 없이 외부 AI용 질문 복사</button>
        {copyStatus && <p className="copy-status" role="status">{copyStatus}</p>}
        <label>AI 문답을 검증한 내 판단<textarea value={humanCheck} onChange={(e) => setHumanCheck(e.target.value)} placeholder="데이터의 어떤 열·분포·결측과 대조했고 무엇을 채택·수정·기각했는지 적어." /></label>
        <div className="choice-grid"><ChoiceButton value="distribution" selected={choice} onClick={setChoice}>분포·품질 근거로 판단</ChoiceButton><ChoiceButton value="mean_only" selected={choice} onClick={setChoice}>전체 평균으로 판단</ChoiceButton></div>
        <p className="field-note">최소 8회의 CSV 수치 분석·가설·반증·판단 문답을 완료해야 다음 단계로 갈 수 있어. 전체 질문·응답은 최종 PT에서 2회당 한 장으로 보존돼.</p>
      </>}
      {stage.id === 'experiment' && <>
        <div className="choice-list"><ChoiceButton value="screening" selected={choice} onClick={setChoice}>대조군 + {scenario.experiment_label}</ChoiceButton><ChoiceButton value="ofat" selected={choice} onClick={setChoice}>한 변수씩 변경</ChoiceButton><ChoiceButton value="immediate" selected={choice} onClick={setChoice}>검증 없이 Recipe 변경</ChoiceButton></div>
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
      <button className="commit" disabled={!choice || busy || (stage.id === 'investigation' && (!datasetDownloaded || conversation.length < MIN_DEEP_DIALOGUE_TURNS || humanCheck.trim().length < 20))}>
        {busy ? '판단 기록 중…' : stage.id === 'investigation' ? '데이터·AI 문답·내 판단을 저장하고 다음으로' : '판단을 기록하고 다음 스테이션으로'}
      </button>
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
      anchor.href = url; anchor.download = 'virtual-fab-interview-slides.html'; document.body.appendChild(anchor); anchor.click(); anchor.remove()
      window.setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (cause) { setReportError(cause instanceof Error ? cause.message : '면접 자료를 만들지 못했어.') }
    finally { setReportBusy(false) }
  }

  return <div className="result-panel">
    <h1>{session.verdict}</h1>
    <p>점수 {session.score}/100 · 남은 예산 {session.budget} · 남은 시간 {session.time_left}분</p>
    <p className="run-metadata">scenario v{session.scenario_version} · seed {session.seed}</p>
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
      <label>내 판단·배운 점·한계<textarea value={opinion} onChange={(event) => setOpinion(event.target.value)} placeholder="왜 이 경로를 선택했는지, AI 의견 중 무엇을 수정했는지, 추가 검증할 한계를 10자 이상 적어봐." /></label>
      <p className={`report-requirement ${opinion.trim().length >= 10 ? 'ready' : ''}`}>{opinion.trim().length >= 10 ? '다운로드 준비 완료' : `의견을 ${10 - opinion.trim().length}자 더 입력하면 다운로드할 수 있어.`}</p>
      <p className="field-note">실제 합성 데이터 통계와 전체 AI 문답을 2회당 한 장으로 나누는 심층 HTML PT를 생성한다. 문답 횟수에 따라 슬라이드 수가 자동으로 늘어나며 인터넷 없이 실행하고 PDF 인쇄도 가능해.</p>
      <button className="download-report" onClick={downloadReport} disabled={reportBusy || opinion.trim().length < 10}>{reportBusy ? 'STAR 면접 자료 생성 중…' : 'HTML 면접 PT 슬라이드 다운로드'}</button>
      {reportError && <p className="inline-error">{reportError}</p>}
    </section>
    <p className="limit-note">이 결과는 교육용 합성 입력에 대한 시나리오 판정이며 실제 공정 인과관계나 현장 성과를 보장하지 않아.</p>
    <button className="commit secondary" onClick={onRestart} disabled={busy}>다른 경로로 다시 실험</button>
  </div>
}

function ModuleHome({ scenarios, loading, error, onSelect }: { scenarios: ScenarioSummary[]; loading: boolean; error: string; onSelect: (id: string) => void }) {
  return <CleanroomLobby scenarios={scenarios} loading={loading} error={error} onSelect={onSelect}/>
}

function ScenarioExperience({ scenarioId, onBack }: { scenarioId: string; onBack: () => void }) {
  const { scenario, session, feedback, error, busy, decide, rewind, restart, setFeedback } = useFabSession(scenarioId)
  const [drawerOpen, setDrawerOpen] = useState(false)

  if (!scenario || !session) return <main className="loading"><div className="loader"/><p>{error || '가상 팹을 준비하고 있어…'}</p></main>

  return (
    <main className="app-shell">
      <header className="topbar">
        <div><button type="button" className="brand brand-button" onClick={onBack}>VIRTUAL FAB</button><span className="scenario-name">{scenario.process} · {scenario.title}</span></div>
        <div className="status-strip"><span>SCORE <b>{session.score}</b></span><span>BUDGET <b>{session.budget}</b></span><span>TIME <b>{session.time_left}m</b></span><button type="button" onClick={() => setDrawerOpen(true)}>EVIDENCE <b>{session.history.length}</b></button></div>
      </header>
      <StageProgress scenario={scenario} session={session} busy={busy} onRewind={rewind}/>
      <section className="workspace">
        <div className="visual-column">
          <FabScene scenario={scenario} session={session} onStationSelect={(index) => setFeedback(index === session.stage_index ? `${scenario.stages[index].label} 스테이션이 열렸어.` : index < session.stage_index ? '이미 완료한 스테이션이야. 기록은 아래에서 확인해.' : '앞 단계의 근거를 먼저 남겨야 열려.')} />
          <div className="feedback" role="status"><span>LIVE NOTE</span><p>{feedback}</p></div>
        </div>
        <aside className="workbench">
          <div className="stage-transition" key={session.completed ? 'result' : scenario.stages[session.stage_index].id}>{session.completed
              ? <ResultPanel scenario={scenario} session={session} busy={busy} onRestart={restart}/>
              : <DecisionPanel scenario={scenario} state={session} onSubmit={decide} busy={busy}/>
          }</div>
          {error && <div className="error" role="alert"><b>기록 실패</b><span>{error}</span></div>}
        </aside>
      </section>
      <EvidenceDrawer open={drawerOpen} scenario={scenario} session={session} onClose={() => setDrawerOpen(false)}/>
      <footer><p>{scenario.notice}</p><p>scenario v{session.scenario_version} · seed {session.seed}</p></footer>
    </main>
  )
}

export default function App() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([])
  const [catalogError, setCatalogError] = useState('')
  const [catalogLoading, setCatalogLoading] = useState(true)
  const [selectedId, setSelectedId] = useState(() => window.location.hash.slice(1))

  useEffect(() => {
    const onHashChange = () => setSelectedId(window.location.hash.slice(1))
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  useEffect(() => {
    let active = true
    api.scenarios().then((items) => { if (active) setScenarios(items) })
      .catch((cause) => { if (active) setCatalogError(cause instanceof Error ? cause.message : '시나리오 목록을 열지 못했어.') })
      .finally(() => { if (active) setCatalogLoading(false) })
    return () => { active = false }
  }, [])

  const select = (id: string) => { window.location.hash = id; setSelectedId(id) }
  const back = () => { window.history.pushState(null, '', window.location.pathname + window.location.search); setSelectedId('') }
  const validSelection = scenarios.some((item) => item.id === selectedId)

  if (selectedId && (validSelection || catalogLoading)) return <ScenarioExperience key={selectedId} scenarioId={selectedId} onBack={back}/>
  return <ModuleHome scenarios={scenarios} loading={catalogLoading} error={selectedId && !validSelection ? '선택한 시나리오를 찾지 못했어. 아래 목록에서 다시 골라줘.' : catalogError} onSelect={select}/>
}
