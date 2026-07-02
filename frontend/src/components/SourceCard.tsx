// frontend/src/components/SourceCard.tsx
import { useState } from 'react'
import type { Source } from '../api/client'

interface Props {
  source: Source
}

export default function SourceCard({ source }: Props) {
  const [expanded, setExpanded] = useState(false)

  const typeLabel: Record<string, string> = {
    general: 'General',
    description: 'Descripción',
    history: 'Historial',
    attachments: 'Adjuntos',
    issue_links: 'Relaciones',
    subtasks: 'Subtareas',
  }

  return (
    <div className="border border-gray-200 rounded-lg p-3 text-sm bg-white">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-mono font-semibold text-blue-700 shrink-0">
            [{source.issue_key}]
          </span>
          <span className="text-gray-700 truncate">{source.title}</span>
          <span className="text-xs text-gray-400 shrink-0">
            {typeLabel[source.chunk_type] ?? source.chunk_type}
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-gray-400">
            {(source.score * 100).toFixed(0)}%
          </span>
          <a
            href={source.jira_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-500 hover:underline text-xs"
          >
            Abrir ↗
          </a>
          <button
            onClick={() => setExpanded(v => !v)}
            className="text-gray-400 hover:text-gray-600 text-xs"
          >
            {expanded ? '▲' : '▼'}
          </button>
        </div>
      </div>
    </div>
  )
}
