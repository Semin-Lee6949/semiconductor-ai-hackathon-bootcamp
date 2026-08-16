import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { api } from '../api'
import type { AIExchange, AIProvider, BYOKResponse } from '../types'

const PROVIDERS: Record<AIProvider, { label: string; model: string; keyHint: string }> = {
  openai: { label: 'OpenAI', model: 'gpt-5', keyHint: 'OpenAI API key' },
  gemini: { label: 'Google Gemini', model: 'gemini-3.5-flash', keyHint: 'Google AI Studio API key' },
  anthropic: { label: 'Anthropic', model: 'claude-opus-4-6', keyHint: 'Anthropic API key' },
  deepseek: { label: 'DeepSeek', model: 'deepseek-v4-flash', keyHint: 'DeepSeek API key' },
}

type Props = {
  sessionId: string
  prompt: string
  promptReady?: boolean
  callsUsed: number
  conversation: AIExchange[]
  onPromptChange: (prompt: string) => void
  onResult: (result: BYOKResponse) => void
}

export function PersonalAIConnector({ sessionId, prompt, promptReady = true, callsUsed, conversation, onPromptChange, onResult }: Props) {
  const [provider, setProvider] = useState<AIProvider>('gemini')
  const [model, setModel] = useState(PROVIDERS.gemini.model)
  const [apiKey, setApiKey] = useState('')
  const [callsMade, setCallsMade] = useState(Number.isFinite(callsUsed) ? callsUsed : 0)
  const [status, setStatus] = useState<'idle' | 'checking' | 'connected' | 'running'>('idle')
  const [message, setMessage] = useState('')
  const [chatOpen, setChatOpen] = useState(false)
  const [copyStatus, setCopyStatus] = useState('')
  const chatEndRef = useRef<HTMLDivElement>(null)
  const followUpRef = useRef<HTMLTextAreaElement>(null)
  const secureContext = useMemo(() => window.isSecureContext || ['localhost', '127.0.0.1'].includes(window.location.hostname), [])

  useEffect(() => {
    setStatus('idle')
    setMessage('')
  }, [provider, model, apiKey])

  useEffect(() => {
    if (!chatOpen) return
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === 'Escape') setChatOpen(false) }
    window.addEventListener('keydown', closeOnEscape)
    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', closeOnEscape)
    }
  }, [chatOpen])

  useEffect(() => {
    if (!chatOpen) return
    chatEndRef.current?.scrollIntoView({ block: 'end' })
    followUpRef.current?.focus({ preventScroll: true })
  }, [chatOpen, conversation.length])

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
      setChatOpen(true)
      setCopyStatus('')
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
  const latestResponse = conversation.at(-1)?.response ?? ''

  const copyLatestResponse = async () => {
    try {
      await navigator.clipboard.writeText(latestResponse)
      setCopyStatus('최근 응답을 복사했어.')
    } catch {
      setCopyStatus('복사가 막혔어. 응답 본문을 직접 선택해 복사해줘.')
    }
  }

  return <><section className="personal-ai" aria-labelledby="personal-ai-title">
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
      <button type="button" className="deepseek-call" onClick={runPrompt} disabled={!secureContext || status !== 'connected' || prompt.trim().length < 10 || !promptReady || exhausted}>{status === 'running' ? 'AI 답변 생성 중…' : '2. 질문 보내기'}</button>
    </div>
    {conversation.length > 0 && <button type="button" className="open-ai-chat" onClick={() => setChatOpen(true)}>AI 대화창 열기 · {conversation.length}/15</button>}
    {message && <p className={status === 'connected' ? 'connection-status' : 'inline-error'} role="status">{message}</p>}
    <small>{promptReady ? '연결 확인은 생성 비용을 발생시키지 않아. 문답 비용·쿼터는 개인 제공사 계정에 적용되고 세션당 최대 15회야.' : '질문에 위 공정 핵심 키워드를 1개 이상 포함해야 전송할 수 있어.'}</small>
  </section>{chatOpen && createPortal(
    <div className="ai-chat-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setChatOpen(false) }}>
      <section className="ai-chat-modal" role="dialog" aria-modal="true" aria-labelledby="ai-chat-title">
        <header className="ai-chat-header">
          <div><span>PROCESS COACH · LIVE DIALOGUE</span><h2 id="ai-chat-title">AI와 공정 문제 좁히기</h2><p>{PROVIDERS[provider].label} · {model} · {conversation.length}/15회</p></div>
          <button type="button" onClick={() => setChatOpen(false)} aria-label="AI 대화창 닫기"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5l14 14M19 5L5 19"/></svg></button>
        </header>
        <div className="ai-chat-layout">
          <div className="ai-chat-transcript" aria-live="polite">
            {conversation.map((exchange) => <article key={exchange.turn_no}>
              <div className="chat-question"><header><b>Q{exchange.turn_no} · {exchange.phase?.label ?? '문답'}</b><small>{exchange.keywords?.join(' · ') || '공정 키워드'}</small></header><p>{exchange.question}</p></div>
              <div className="chat-answer"><header><b>{exchange.provider_label}</b><small>{exchange.model} · {exchange.usage.total_tokens.toLocaleString()} tokens</small></header><p>{exchange.response}</p></div>
            </article>)}
            <div ref={chatEndRef}/>
          </div>
          <aside className="ai-chat-composer">
            <div><span>NEXT TURN</span><b>응답을 읽고 후속 질문</b><p>동의·반박·누락된 증거를 짚고 다음 질문을 수정해. 공정 키워드를 최소 1개 포함해야 해.</p></div>
            <label>다음 질문<textarea ref={followUpRef} value={prompt} onChange={(event) => onPromptChange(event.target.value)} placeholder="방금 답변에서 검증이 필요한 가설과 공정 키워드를 넣어 후속 질문을 작성해." /></label>
            <p className={`chat-prompt-status ${promptReady ? 'ready' : ''}`}>{promptReady ? `전송 가능 · ${15 - callsMade}회 남음` : '공정 핵심 키워드를 추가해야 해.'}</p>
            <button type="button" className="chat-send" onClick={runPrompt} disabled={status !== 'connected' || prompt.trim().length < 10 || !promptReady || exhausted}>{status === 'running' ? 'AI 답변 기다리는 중…' : exhausted ? '15회 문답 완료' : '후속 질문 보내기'}</button>
            <button type="button" className="chat-copy" onClick={copyLatestResponse} disabled={!latestResponse}>최근 응답 복사</button>
            {copyStatus && <p className="chat-copy-status" role="status">{copyStatus}</p>}
          </aside>
        </div>
      </section>
    </div>, document.body
  )}</>
}
