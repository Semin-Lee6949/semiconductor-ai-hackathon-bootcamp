import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import type { Decision, Scenario, SessionState } from '../types'

const STORAGE_KEY = 'virtual-fab:photo-cd-drift:session'

export function useFabSession() {
  const [scenario, setScenario] = useState<Scenario | null>(null)
  const [session, setSession] = useState<SessionState | null>(null)
  const [feedback, setFeedback] = useState('현재 스테이션을 선택해 첫 판단을 시작해.')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(true)

  useEffect(() => {
    let active = true
    const load = async () => {
      try {
        const nextScenario = await api.scenario()
        const savedId = window.localStorage.getItem(STORAGE_KEY)
        let nextSession: SessionState
        if (savedId) {
          try {
            nextSession = await api.session(savedId)
            setFeedback(nextSession.completed ? '완료한 실험을 복원했어. Evidence와 면접 자료를 다시 확인할 수 있어.' : '이전 실험을 복원했어. 마지막 스테이션부터 이어가면 돼.')
          } catch {
            window.localStorage.removeItem(STORAGE_KEY)
            nextSession = await api.createSession()
          }
        } else {
          nextSession = await api.createSession()
        }
        if (!active) return
        setScenario(nextScenario)
        setSession(nextSession)
        window.localStorage.setItem(STORAGE_KEY, nextSession.id)
      } catch (cause) {
        if (active) setError(cause instanceof Error ? cause.message : '가상 팹을 열지 못했어.')
      } finally {
        if (active) setBusy(false)
      }
    }
    void load()
    return () => { active = false }
  }, [])

  const decide = useCallback(async (decision: Decision) => {
    if (!session) return
    setBusy(true); setError('')
    try {
      const result = await api.decide(session.id, decision)
      setSession(result.state); setFeedback(result.feedback)
    } catch (cause) { setError(cause instanceof Error ? cause.message : '판단을 기록하지 못했어.') }
    finally { setBusy(false) }
  }, [session])

  const restart = useCallback(async () => {
    if (!session) return
    setBusy(true); setError('')
    try {
      const next = await api.restart(session.id)
      setSession(next)
      setFeedback('새 실험이 시작됐어. 이번에는 다른 판단 경로를 비교해봐.')
    } catch (cause) { setError(cause instanceof Error ? cause.message : '재시작하지 못했어.') }
    finally { setBusy(false) }
  }, [session])

  return { scenario, session, feedback, error, busy, decide, restart, setFeedback }
}
