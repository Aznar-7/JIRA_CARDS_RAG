// frontend/src/components/ChatWindow.tsx
import { useEffect, useRef, useState } from 'react'
import type { HistoryMessage, Source } from '../api/client'
import { streamQuery } from '../api/client'
import MessageBubble from './MessageBubble'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  isStreaming?: boolean
}

export default function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return
    const question = input.trim()
    setInput('')
    setLoading(true)

    const history: HistoryMessage[] = messages.map(m => ({
      role: m.role,
      content: m.content,
    }))

    setMessages(prev => [
      ...prev,
      { role: 'user', content: question },
      { role: 'assistant', content: '', isStreaming: true },
    ])

    let fullContent = ''
    let sources: Source[] = []

    try {
      for await (const event of streamQuery(question, history)) {
        if (event.type === 'token' && event.content) {
          fullContent += event.content
          setMessages(prev => [
            ...prev.slice(0, -1),
            { role: 'assistant', content: fullContent, isStreaming: true },
          ])
        } else if (event.type === 'sources' && event.sources) {
          sources = event.sources
        } else if (event.type === 'done') {
          setMessages(prev => [
            ...prev.slice(0, -1),
            { role: 'assistant', content: fullContent, sources, isStreaming: false },
          ])
        }
      }
    } catch {
      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'assistant', content: 'Error al conectar con el servidor.', isStreaming: false },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-3 flex items-center gap-3">
        <span className="text-lg font-semibold text-gray-800">Jira Knowledge RAG</span>
        <span className="text-xs text-gray-400">Consulta tus tickets con IA</span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 gap-3">
            <p className="text-4xl">💬</p>
            <p className="font-medium">¿En qué puedo ayudarte?</p>
            <div className="text-sm space-y-1 text-center">
              <p>"¿Qué pasó con el error de facturas?"</p>
              <p>"¿Quién resolvió el bug de autenticación?"</p>
              <p>"¿Qué se trabajó en el sprint 01?"</p>
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t p-4">
        <div className="flex gap-2 max-w-3xl mx-auto">
          <input
            className="flex-1 border border-gray-300 rounded-xl px-4 py-2.5 text-sm
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       disabled:bg-gray-50 disabled:text-gray-400"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Preguntá sobre tus tickets de Jira..."
            disabled={loading}
          />
          <button
            className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-xl text-sm
                       font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleSend}
            disabled={loading || !input.trim()}
          >
            {loading ? '…' : 'Enviar'}
          </button>
        </div>
      </div>
    </div>
  )
}
