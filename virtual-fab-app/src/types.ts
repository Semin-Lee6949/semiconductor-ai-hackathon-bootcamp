export type StageId = 'incident' | 'coach' | 'data' | 'experiment' | 'analysis' | 'validation'

export type Tool = {
  label: string
  kind: 'dimension' | 'structure' | 'chemistry' | 'electrical'
  cost: number
  time: number
  destructive: boolean
}

export type ScenarioStage = {
  id: StageId
  label: string
  station: string
  brief: string
}

export type Scenario = {
  id: string
  title: string
  version: string
  notice: string
  stages: ScenarioStage[]
  tools: Record<string, Tool>
  required_analysis_kinds: string[]
  limits: { budget: number; time: number }
}

export type HistoryItem = {
  stage: StageId
  choice: string
  payload: Record<string, unknown>
  tools?: string[]
  cost?: number
  time?: number
  improved?: boolean
}

export type SessionState = {
  id: string
  scenario_id: string
  stage_index: number
  budget: number
  time_left: number
  score: number
  evidence: string[]
  history: HistoryItem[]
  completed: boolean
  verdict: string | null
}

export type Decision = {
  stage: StageId
  choice: string
  payload?: Record<string, unknown>
}

export type DecisionResult = { state: SessionState; feedback: string }

export type CoachResponse = { response: string; model: string }

export type ReportPayload = {
  opinion: string
  presenter: string
  target_role: string
}
