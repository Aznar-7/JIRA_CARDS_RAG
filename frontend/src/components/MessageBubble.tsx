// frontend/src/components/MessageBubble.tsx
import type { Source } from '../api/client'
import SourceCard from './SourceCard'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  isStreaming?: boolean
}

interface Props {
  message: Message
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-2xl w-full ${isUser ? 'ml-12' : 'mr-12'}`}>
        <div
          className={`rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap ${
            isUser
              ? 'bg-blue-600 text-white rounded-br-sm'
              : 'bg-white border border-gray-200 text-gray-800 rounded-bl-sm'
          }`}
        >
          {message.content}
          {message.isStreaming && (
            <span className="inline-block w-1.5 h-4 bg-gray-400 animate-pulse ml-0.5 align-middle" />
          )}
        </div>

        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 space-y-1">
            <p className="text-xs text-gray-500 font-medium px-1">
              {message.sources.length} fuente{message.sources.length !== 1 ? 's' : ''}
            </p>
            {message.sources.map(s => (
              <SourceCard key={s.chunk_id} source={s} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
