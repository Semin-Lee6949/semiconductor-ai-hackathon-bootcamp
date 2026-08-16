export type StageId = 'incident' | 'investigation' | 'experiment' | 'analysis' | 'validation'

export type AIExchange = {
  turn_no: number
  question: string
  response: string
  provider_label: string
  model: string
  usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number }
}

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
  module_no: string
  process: string
  title: string
  tagline: string
  skills: string[]
  badge: string
  version: string
  notice: string
  coach_prompt: string
  experiment_label: string
  signal: {
    title: string
    aria: string
    start: string
    end: string
    warning: number
    risk_from: number
    bars: number[]
  }
  incident: {
    case_id: string
    role: string
    deadline: string
    facts: Array<{ label: string; value: string; note: string }>
    unknowns: string[]
    decision: string
    choices: { hold: [string, string]; release: [string, string] }
  }
  stages: ScenarioStage[]
  tools: Record<string, Tool>
  required_analysis_kinds: string[]
  limits: { budget: number; time: number }
}

export type ScenarioSummary = Pick<Scenario, 'id' | 'module_no' | 'process' | 'title' | 'tagline' | 'skills' | 'badge' | 'version'>

export type HistoryItem = {
  decision_no?: number
  stage: StageId
  choice: string
  payload: Record<string, unknown>
  scenario_version?: string
  seed?: number
  tools?: string[]
  cost?: number
  time?: number
  improved?: boolean
}

export type SessionState = {
  id: string
  scenario_id: string
  scenario_version: string
  seed: number
  stage_index: number
  budget: number
  time_left: number
  score: number
  llm_check_attempts: number
  llm_call_count: number
  dataset_downloaded: boolean
  ai_conversation: AIExchange[]
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

export type DeepSeekResponse = {
  response: string
  model: string
  usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number }
}

export type AIProvider = 'openai' | 'anthropic' | 'gemini' | 'deepseek'

export type BYOKCredentials = {
  provider: AIProvider
  model: string
  api_key: string
}

export type BYOKConnection = {
  status: 'connected'
  provider: AIProvider
  provider_label: string
  model: string
}

export type BYOKResponse = DeepSeekResponse & {
  provider: AIProvider
  provider_label: string
  turn_no?: number
}

export type ReportPayload = {
  opinion: string
  presenter: string
  target_role: string
}
