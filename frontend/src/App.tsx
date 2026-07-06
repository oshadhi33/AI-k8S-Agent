import { useCallback, useEffect, useState } from 'react'
import { fetchHistory, startInvestigation, streamInvestigation } from './api'
import type { HistoryItem, InvestigationResult, ProgressStep } from './types'
import './App.css'

const INVESTIGATION_STEPS = [
  { key: 'checking_pods', label: 'Pods Checked' },
  { key: 'reading_logs', label: 'Logs Processed' },
  { key: 'analyzing_events', label: 'Events Analyzed' },
  { key: 'inspecting_deployments', label: 'Deployments Inspected' },
  { key: 'checking_network', label: 'Network Checked' },
  { key: 'finding_root_cause', label: 'Root Cause Found' },
]

export default function App() {
  const [namespace, setNamespace] = useState('default')
  const [targetPod, setTargetPod] = useState('')
  const [incidentTitle, setIncidentTitle] = useState('')
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState<ProgressStep[]>([])
  const [result, setResult] = useState<InvestigationResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const useStream = true

  const loadHistory = useCallback(async () => {
    const items = await fetchHistory()
    setHistory(items)
  }, [])

  useEffect(() => {
    loadHistory()
  }, [loadHistory])

  const handleInvestigate = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    setProgress([])

    const params = {
      namespace,
      target_pod: targetPod || undefined,
      incident_title: incidentTitle || undefined,
    }

    try {
      if (useStream) {
        streamInvestigation(
          params,
          (step) => setProgress((prev) => [...prev, step]),
          (res) => {
            setResult(res)
            setLoading(false)
            loadHistory()
          },
          (err) => {
            setError(err)
            setLoading(false)
          },
        )
      } else {
        const res = await startInvestigation(params)
        setResult(res)
        setProgress(INVESTIGATION_STEPS.map((s) => ({ step: s.key, message: s.label, status: 'done' })))
        loadHistory()
        setLoading(false)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Investigation failed')
      setLoading(false)
    }
  }

  const completedSteps = new Set(progress.map((p) => p.step))

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>AI <span>K8s</span> Agent</h1>
          <p className="subtitle">Investigate failures, find root causes, get fixes</p>
        </div>
      </header>

      <div className="grid">
        <aside>
          <div className="panel">
            <h2>Investigate</h2>
            <div className="form-group">
              <label>Incident Title</label>
              <input
                placeholder="Payment Service Failure"
                value={incidentTitle}
                onChange={(e) => setIncidentTitle(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Namespace</label>
              <input value={namespace} onChange={(e) => setNamespace(e.target.value)} />
            </div>
            <div className="form-group">
              <label>Target Pod (optional)</label>
              <input
                placeholder="payment-service-abc123"
                value={targetPod}
                onChange={(e) => setTargetPod(e.target.value)}
              />
            </div>
            <button className="btn-primary" disabled={loading} onClick={handleInvestigate}>
              {loading ? 'Investigating...' : 'Investigate Cluster'}
            </button>
          </div>

          <div className="panel" style={{ marginTop: '1rem' }}>
            <h2>History</h2>
            {history.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No investigations yet</p>
            ) : (
              <ul className="history-list">
                {history.map((item) => (
                  <li key={item.id} className="history-item" onClick={() => setResult(item as InvestigationResult)}>
                    <div className="history-title">{item.title}</div>
                    <div className="history-meta">
                      {item.namespace} · {item.problem_type || item.status} ·{' '}
                      {new Date(item.created_at).toLocaleDateString()}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </aside>

        <main className="panel">
          <h2>Investigation</h2>

          {error && (
            <div style={{ color: 'var(--danger)', marginBottom: '1rem', fontSize: '0.9rem' }}>{error}</div>
          )}

          {!loading && !result && !error && (
            <div className="empty-state">
              <div className="empty-state-icon">⎈</div>
              <p>Configure a namespace and click Investigate to start</p>
            </div>
          )}

          {(loading || progress.length > 0) && (
            <ul className="progress-list">
              {INVESTIGATION_STEPS.map((step) => {
                const done = completedSteps.has(step.key)
                const active = loading && !done && progress.length > 0 && progress[progress.length - 1]?.step === step.key
                return (
                  <li key={step.key} className={`progress-item ${done ? 'done' : ''} ${active ? 'active' : ''}`}>
                    <span className="progress-icon">{done ? '✓' : active ? '●' : '○'}</span>
                    {step.label}
                  </li>
                )
              })}
            </ul>
          )}

          {result && (
            <div className="result-card">
              <div className="result-header">
                <span className="badge badge-danger">{result.problem_type || 'Diagnosed'}</span>
                {result.confidence != null && (
                  <span className="confidence">Confidence: {result.confidence}%</span>
                )}
                <span className="badge badge-success">{result.status}</span>
              </div>

              {result.evidence_summary && (
                <div className="summary-grid">
                  {Object.entries(result.evidence_summary).map(([key, val]) => (
                    <div key={key} className="summary-stat">
                      <div className="value">{val}</div>
                      <div className="label">{key.replace(/_/g, ' ')}</div>
                    </div>
                  ))}
                </div>
              )}

              <div className="root-cause">{result.root_cause}</div>
              {result.analysis && <p className="analysis">{result.analysis}</p>}

              {result.suggested_fixes && result.suggested_fixes.length > 0 && (
                <>
                  <h2 style={{ marginTop: '1.5rem' }}>Suggested Fixes</h2>
                  <ul className="fix-list">
                    {result.suggested_fixes.map((fix, i) => (
                      <li key={i} className="fix-item">
                        <p>
                          <strong>[{fix.type}]</strong> {fix.description}
                        </p>
                        <pre>{fix.command_or_patch}</pre>
                      </li>
                    ))}
                  </ul>
                </>
              )}

              {result.prevention && result.prevention.length > 0 && (
                <>
                  <h2 style={{ marginTop: '1rem' }}>Prevention</h2>
                  <ul style={{ paddingLeft: '1.25rem', color: 'var(--text-muted)', lineHeight: 1.8 }}>
                    {result.prevention.map((p, i) => (
                      <li key={i}>{p}</li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
