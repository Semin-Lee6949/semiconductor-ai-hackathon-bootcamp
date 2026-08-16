import type { BYOKConnection, BYOKCredentials, BYOKResponse, Decision, DecisionResult, DeepSeekResponse, ReportPayload, Scenario, ScenarioSummary, SessionState, StageId } from './types'

const BASE = import.meta.env.BASE_URL

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) { super(message); this.name = 'ApiError'; this.status = status }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}api/${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new ApiError(body.detail ?? `요청 실패 (${response.status})`, response.status)
  return body as T
}

export const api = {
  scenarios: () => request<ScenarioSummary[]>('scenarios'),
  scenario: (scenarioId: string) => request<Scenario>(`scenario/${encodeURIComponent(scenarioId)}`),
  createSession: (scenarioId: string) => request<SessionState>(`sessions?scenario_id=${encodeURIComponent(scenarioId)}`, { method: 'POST' }),
  session: (sessionId: string) => request<SessionState>(`sessions/${sessionId}`),
  decide: (sessionId: string, decision: Decision) =>
    request<DecisionResult>(`sessions/${sessionId}/decisions`, {
      method: 'POST',
      body: JSON.stringify({ ...decision, payload: decision.payload ?? {} }),
    }),
  rewind: (sessionId: string, stage: StageId) =>
    request<DecisionResult>(`sessions/${sessionId}/rewind`, {
      method: 'POST',
      body: JSON.stringify({ stage }),
    }),
  deepseek: (sessionId: string, prompt: string) =>
    request<DeepSeekResponse>(`sessions/${sessionId}/deepseek`, {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    }),
  checkPersonalAI: (sessionId: string, credentials: BYOKCredentials) =>
    request<BYOKConnection>(`sessions/${sessionId}/llm/check`, {
      method: 'POST',
      body: JSON.stringify(credentials),
    }),
  generatePersonalAI: (sessionId: string, credentials: BYOKCredentials, prompt: string) =>
    request<BYOKResponse>(`sessions/${sessionId}/llm/generate`, {
      method: 'POST',
      body: JSON.stringify({ ...credentials, prompt }),
    }),
  dataset: async (sessionId: string) => {
    const response = await fetch(`${BASE}api/sessions/${sessionId}/dataset.csv`)
    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      throw new ApiError(body.detail ?? `데이터 다운로드 실패 (${response.status})`, response.status)
    }
    return { blob: await response.blob(), filename: response.headers.get('content-disposition')?.match(/filename="?([^";]+)"?/)?.[1] ?? 'virtual-fab-data.csv' }
  },
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
