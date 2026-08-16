import type { Decision, DecisionResult, ReportPayload, Scenario, SessionState } from './types'

const BASE = import.meta.env.BASE_URL

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}api/${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail ?? `요청 실패 (${response.status})`)
  return body as T
}

export const api = {
  scenario: () => request<Scenario>('scenario/photo-cd-drift'),
  createSession: () => request<SessionState>('sessions', { method: 'POST' }),
  session: (sessionId: string) => request<SessionState>(`sessions/${sessionId}`),
  decide: (sessionId: string, decision: Decision) =>
    request<DecisionResult>(`sessions/${sessionId}/decisions`, {
      method: 'POST',
      body: JSON.stringify({ ...decision, payload: decision.payload ?? {} }),
    }),
  report: async (sessionId: string, payload: ReportPayload) => {
    const response = await fetch(`${BASE}api/sessions/${sessionId}/report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      throw new Error(body.detail ?? `자료 생성 실패 (${response.status})`)
    }
    return response.blob()
  },
  restart: (sessionId: string) =>
    request<SessionState>(`sessions/${sessionId}/restart`, { method: 'POST' }),
}
