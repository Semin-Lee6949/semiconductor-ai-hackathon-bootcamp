import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import type { AIProvider, BYOKResponse } from '../types'

const PROVIDERS: Record<AIProvider, { label: string; model: string; keyHint: string }> = {
  openai: { label: 'OpenAI', model: 'gpt-5', keyHint: 'OpenAI API key' },
  gemini: { label: 'Google Gemini', model: 'gemini-3.5-flash', keyHint: 'Google AI Studio API key' },
  anthropic: { label: 'Anthropic', model: 'claude-opus-4-6', keyHint: 'Anthropic API key' },
  deepseek: { label: 'DeepSeek', model: 'deepseek-v4-flash', keyHint: 'DeepSeek API key' },
}

type Props = {
  sessionId: string
  prompt: string
  callsUsed: number
  onResult: (result: BYOKResponse) => void
}

export function PersonalAIConnector({ sessionId, prompt, callsUsed, onResult }: Props) {
  const [provider, setProvider] = useState<AIProvider>('gemini')
  const [model, setModel] = useState(PROVIDERS.gemini.model)
  const [apiKey, setApiKey] = useState('')
  const [callsMade, setCallsMade] = useState(Number.isFinite(callsUsed) ? callsUsed : 0)
  const [status, setStatus] = useState<'idle' | 'checking' | 'connected' | 'running'>('idle')
  const [message, setMessage] = useState('')
  const secureContext = useMemo(() => window.isSecureContext || ['localhost', '127.0.0.1'].includes(window.location.hostname), [])

  useEffect(() => {
    setStatus('idle')
    setMessage('')
  }, [provider, model, apiKey])

  const changeProvider = (next: AIProvider) => {
    setProvider(next)
    setModel(PROVIDERS[next].model)
    setApiKey('')
  }

  const checkConnection = async () => {
    setStatus('checking'); setMessage('')
    try {
      const result = await api.checkPersonalAI(sessionId, { provider, model: model.trim(), api_key: apiKey.trim() })
      setModel(result.model)
      setStatus('connected')
      setMessage(`${result.provider_label} · ${result.model} 연결 확인 완료`)
    } catch (cause) {
      setStatus('idle')
      setMessage(cause instanceof Error ? cause.message : '연결을 확인하지 못했어.')
    }
  }

  const runPrompt = async () => {
    setStatus('running'); setMessage('')
    try {
      const result = await api.generatePersonalAI(sessionId, { provider, model: model.trim(), api_key: apiKey.trim() }, prompt)
      onResult(result)
      setCallsMade((current) => current + 1)
      setStatus('connected')
      setMessage(`${result.provider_label} 응답 완료 · 총 ${result.usage.total_tokens.toLocaleString()} tokens`)
    } catch (cause) {
      setStatus('connected')
      setMessage(cause instanceof Error ? cause.message : 'AI 응답을 받지 못했어.')
    }
  }

  const keyReady = apiKey.trim().length >= 20 && model.trim().length > 0
  const exhausted = callsMade >= 15

  return <section className="personal-ai" aria-labelledby="personal-ai-title">
    <header><div><span>PERSONAL API · MEMORY ONLY</span><h3 id="personal-ai-title">내 AI 연결</h3></div><strong>{status === 'connected' ? `CONNECTED · ${callsMade}/15` : `${callsMade}/15 CALLS`}</strong></header>
    <p>개인 키는 요청 순간에만 사용하고 저장하지 않아. 질문·응답·모델·토큰은 분석 과정과 최종 PT를 위해 세션에 기록되며, 키는 새로고침하면 사라져.</p>
    {!secureContext && <div className="security-block" role="alert"><b>HTTPS 연결 필요</b><span>현재 주소에서는 API 키 전송을 차단했어. 키를 입력하지 말고 아래 프롬프트 복사를 이용해.</span></div>}
    <div className="personal-ai-fields">
      <label>AI 제공사<select value={provider} onChange={(event) => changeProvider(event.target.value as AIProvider)} disabled={!secureContext || status === 'checking' || status === 'running'}>{Object.entries(PROVIDERS).map(([id, item]) => <option key={id} value={id}>{item.label}</option>)}</select></label>
      <label>모델 ID<input value={model} onChange={(event) => setModel(event.target.value)} disabled={!secureContext || status === 'checking' || status === 'running'} spellCheck={false}/></label>
      <label className="api-key-field">개인 API 키<input type="password" value={apiKey} onChange={(event) => setApiKey(event.target.value)} placeholder={PROVIDERS[provider].keyHint} autoComplete="new-password" disabled={!secureContext || status === 'checking' || status === 'running'}/></label>
    </div>
    <div className="personal-ai-actions">
      <button type="button" className="secondary" onClick={checkConnection} disabled={!secureContext || !keyReady || status === 'checking' || status === 'running' || exhausted}>{status === 'checking' ? '연결 확인 중…' : '1. 연결 확인'}</button>
      <button type="button" className="deepseek-call" onClick={runPrompt} disabled={!secureContext || status !== 'connected' || prompt.trim().length < 10 || exhausted}>{status === 'running' ? 'AI 답변 생성 중…' : '2. 질문 보내기'}</button>
    </div>
    {message && <p className={status === 'connected' ? 'connection-status' : 'inline-error'} role="status">{message}</p>}
    <small>연결 확인은 생성 비용을 발생시키지 않아. 문답 비용·쿼터는 개인 제공사 계정에 적용되고 세션당 최대 15회야.</small>
  </section>
}
