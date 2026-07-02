// frontend/src/api/client.ts

export interface Source {
  chunk_id: string
  issue_key: string
  title: string
  chunk_type: string
  jira_url: string
  score: number
}

export interface StreamEvent {
  type: 'token' | 'sources' | 'done' | 'error'
  content?: string
  sources?: Source[]
  message?: string
}

export interface HistoryMessage {
  role: 'user' | 'assistant'
  content: string
}

export async function* streamQuery(
  question: string,
  history: HistoryMessage[],
  filters?: { status?: string; sprint?: string },
): AsyncGenerator<StreamEvent> {
  const response = await fetch('/api/rag/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, history, ...filters }),
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }
  if (!response.body) throw new Error('No response body')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6).trim()
        if (data) {
          yield JSON.parse(data) as StreamEvent
        }
      }
    }
  }
}
