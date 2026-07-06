import type { HistoryItem, InvestigationResult, ProgressStep } from './types'

const API_BASE = import.meta.env.VITE_API_URL || ''

export async function startInvestigation(params: {
  namespace: string
  target_pod?: string
  incident_title?: string
}): Promise<InvestigationResult> {
  const res = await fetch(`${API_BASE}/api/investigations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Investigation failed (${res.status})`)
  }
  return res.json()
}

export function streamInvestigation(
  params: { namespace: string; target_pod?: string; incident_title?: string },
  onProgress: (step: ProgressStep) => void,
  onComplete: (result: InvestigationResult) => void,
  onError: (error: string) => void,
): () => void {
  const controller = new AbortController()

  fetch(`${API_BASE}/api/investigations/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify(params),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok || !res.body) {
        throw new Error(`Stream failed (${res.status})`)
      }
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.step === 'result' && data.result) {
                onComplete(data.result)
              } else if (data.error) {
                onError(data.error)
              } else if (data.step && data.message) {
                onProgress(data)
              }
            } catch {
              /* ignore parse errors */
            }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') onError(err.message)
    })

  return () => controller.abort()
}

export async function fetchHistory(): Promise<HistoryItem[]> {
  const res = await fetch(`${API_BASE}/api/investigations`)
  if (!res.ok) return []
  const data = await res.json()
  return data.investigations || []
}
