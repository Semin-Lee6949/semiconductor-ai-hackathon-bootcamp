import { useCallback, useEffect, useState } from 'react'
import { ApiError, api } from '../api'
import type { Decision, Scenario, SessionState, StageId } from '../types'

export function useFabSession(scenarioId: string) {
  const storageKey = `virtual-fab:${scenarioId}:session`
  const [scenario, setScenario] = useState<Scenario | null>(null)
  const [session, setSession] = useState<SessionState | null>(null)
  const [feedback, setFeedback] = useState('현재 스테이션을 선택해 첫 판단을 시작해.')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(true)

  useEffect(() => {
    let active = true
    const load = async () => {
      try {
        setBusy(true); setError(''); setScenario(null); setSession(null)
        const nextScenario = await api.scenario(scenarioId)
        const savedId = window.localStorage.getItem(storageKey)
        let nextSession: SessionState
        if (savedId) {
          try {
            nextSession = await api.session(savedId)
            setFeedback(nextSession.completed ? '완료한 실험을 복원했어. Evidence와 면접 자료를 다시 확인할 수 있어.' : '이전 실험을 복원했어. 마지막 스테이션부터 이어가면 돼.')
          } catch {
            window.localStorage.removeItem(storageKey)
            nextSession = await api.createSession(scenarioId)
          }
        } else {
          nextSession = await api.createSession(scenarioId)
        }
        if (!active) return
        setScenario(nextScenario)
        setSession(nextSession)
        window.localStorage.setItem(storageKey, nextSession.id)
      } catch (cause) {
        if (active) setError(cause instanceof Error ? cause.message : '가상 팹을 열지 못했어.')
      } finally {
        if (active) setBusy(false)
      }
    }
    void load()
    return () => { active = false }
  }, [scenarioId, storageKey])

  const decide = useCallback(async (decision: Decision) => {
    if (!session) return
    setBusy(true); setError('')
    try {
      const result = await api.decide(session.id, decision)
      setSession(result.state); setFeedback(result.feedback)
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 404) {
        try {
          const next = await api.createSession(scenarioId)
          setSession(next)
          window.localStorage.setItem(storageKey, next.id)
          setFeedback('서버 갱신으로 이전 세션이 만료됐어. 새 실험을 만들었으니 첫 단계부터 다시 선택해줘.')
          setError('')
        } catch (recoveryCause) {
          setError(recoveryCause instanceof Error ? recoveryCause.message : '새 세션을 만들지 못했어.')
        }
      } else setError(cause instanceof Error ? cause.message : '판단을 기록하지 못했어.')
    }
    finally { setBusy(false) }
  }, [scenarioId, session, storageKey])

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

  const rewind = useCallback(async (stage: StageId) => {
    if (!session) return
    setBusy(true); setError('')
    try {
      const result = await api.rewind(session.id, stage)
      setSession(result.state); setFeedback(result.feedback)
    } catch (cause) { setError(cause instanceof Error ? cause.message : '이전 단계로 돌아가지 못했어.') }
    finally { setBusy(false) }
  }, [session])

  return { scenario, session, feedback, error, busy, decide, rewind, restart, setFeedback }
}
