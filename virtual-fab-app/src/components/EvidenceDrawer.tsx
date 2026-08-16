import { useEffect } from 'react'
import type { Scenario, SessionState } from '../types'

const CHOICE_LABELS: Record<string, string> = {
  hold: '판정 보류 후 분포 확인', release_by_mean: '대표 평균값만 보고 진행',
  modify: 'AI 제안을 수정해 사용', accept: 'AI 제안을 그대로 채택', reject: '근거 부족으로 보류',
  distribution: '위치·Tool·Lot 분포 분석', mean_only: '전체 평균만 확인',
  screening: '대조군 포함 Screening DOE', ofat: '한 변수씩 확인', immediate: '즉시 Recipe 변경',
  controlled: '한정 적용 후 모니터링', direct: '전체 Lot 즉시 적용', release: '검증 없이 해제',
}

export function EvidenceDrawer({ open, scenario, session, onClose }: { open: boolean; scenario: Scenario; session: SessionState; onClose: () => void }) {
  useEffect(() => {
    if (!open) return
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose() }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [open, onClose])

  if (!open) return null
  return <div className="drawer-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}>
    <aside className="evidence-drawer" role="dialog" aria-modal="true" aria-labelledby="evidence-title">
      <header><div><span>REACT LIVE STATE</span><h2 id="evidence-title">Evidence trail</h2></div><button type="button" onClick={onClose} aria-label="Evidence 닫기">×</button></header>
      <p className="run-metadata">scenario v{session.scenario_version} · seed {session.seed}</p>
      <div className="drawer-summary"><span>점수 <b>{session.score}</b></span><span>예산 <b>{session.budget}</b></span><span>시간 <b>{session.time_left}m</b></span></div>
      {session.history.length === 0 ? <p className="drawer-empty">첫 판단을 기록하면 이곳에 근거가 누적돼.</p> : <ol>
        {session.history.map((item, index) => {
          const stage = scenario.stages.find((candidate) => candidate.id === item.stage)
          const toolLabels = item.tools?.map((id) => scenario.tools[id]?.label).filter(Boolean).join(' + ')
          const conversation = Array.isArray(item.payload?.ai_conversation) ? item.payload.ai_conversation : []
          return <li key={`${item.stage}-${index}`}><span>{String(item.decision_no ?? index + 1).padStart(2, '0')}</span><div><b>{stage?.label}</b><p>{toolLabels || CHOICE_LABELS[item.choice] || item.choice}</p>{item.cost !== undefined && <small>{item.cost}C · {item.time}m</small>}{item.stage === 'investigation' && <details><summary>데이터 다운로드 · AI 문답 {conversation.length}회</summary>{conversation.map((exchange, turn) => {
            const phase = exchange.phase && typeof exchange.phase === 'object' ? String(exchange.phase.label ?? '문답') : '문답'
            const keywords = Array.isArray(exchange.keywords) ? exchange.keywords.map(String).join(' · ') : ''
            return <div key={turn}><strong>Q{turn + 1} · {phase} · {String(exchange.model ?? '외부 AI')}</strong>{keywords && <small>KEYWORDS · {keywords}</small>}<p>{String(exchange.question ?? '')}</p><strong>RESPONSE</strong><p>{String(exchange.response ?? '')}</p></div>
          })}</details>}</div></li>
        })}
      </ol>}
      <p className="drawer-note">현재 단계의 입력을 바꾸지 않고 완료된 판단만 보여줘.</p>
    </aside>
  </div>
}
