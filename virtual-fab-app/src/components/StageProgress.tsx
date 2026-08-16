import type { CSSProperties } from 'react'
import type { Scenario, SessionState, StageId } from '../types'

export function StageProgress({ scenario, session, busy, onRewind }: { scenario: Scenario; session: SessionState; busy: boolean; onRewind: (stage: StageId) => void }) {
  return <nav className="stage-rail" aria-label="시나리오 진행 단계" style={{ '--stage-count': scenario.stages.length } as CSSProperties}>
    {scenario.stages.map((stage, index) => {
      const status = index === session.stage_index && !session.completed ? 'active' : index < session.stage_index || session.completed ? 'done' : ''
      const canRewind = index < session.history.length
      return <button type="button" key={stage.id} className={`${status} ${canRewind ? 'rewindable' : ''}`.trim()} aria-current={status === 'active' ? 'step' : undefined} aria-label={canRewind ? `${stage.label} 단계로 돌아가기 · 이후 판단은 되돌림` : `${stage.label} · ${status === 'active' ? '진행 중' : '대기'}`} title={canRewind ? '이 단계부터 다시 판단합니다. 이후 단계의 판단은 되돌립니다.' : undefined} disabled={!canRewind || busy} onClick={() => onRewind(stage.id)}>
        <span>{String(index + 1).padStart(2, '0')}</span>
        <b>{stage.label}</b>
        <small>{canRewind ? '돌아가기' : status === 'active' ? '진행 중' : '대기'}</small>
      </button>
    })}
  </nav>
}
