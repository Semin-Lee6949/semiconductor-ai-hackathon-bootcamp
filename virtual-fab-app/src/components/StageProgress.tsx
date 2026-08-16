import type { Scenario, SessionState } from '../types'

export function StageProgress({ scenario, session }: { scenario: Scenario; session: SessionState }) {
  return <nav className="stage-rail" aria-label="시나리오 진행 단계">
    {scenario.stages.map((stage, index) => {
      const status = index === session.stage_index && !session.completed ? 'active' : index < session.stage_index || session.completed ? 'done' : ''
      return <div key={stage.id} className={status} aria-current={status === 'active' ? 'step' : undefined}>
        <span>{String(index + 1).padStart(2, '0')}</span>
        <b>{stage.label}</b>
        <small>{status === 'done' ? '완료' : status === 'active' ? '진행 중' : '대기'}</small>
      </div>
    })}
  </nav>
}
