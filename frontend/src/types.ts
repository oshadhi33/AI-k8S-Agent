export interface SuggestedFix {
  type: string
  description: string
  command_or_patch: string
}

export interface InvestigationResult {
  id: string
  title: string
  namespace: string
  target_pod: string | null
  status: string
  root_cause?: string
  problem_type?: string
  confidence?: number
  analysis?: string
  suggested_fixes?: SuggestedFix[]
  prevention?: string[]
  affected_resources?: string[]
  evidence_summary?: Record<string, number>
  completed_at?: string
}

export interface ProgressStep {
  step: string
  message: string
  status: string
}

export interface HistoryItem {
  id: string
  title: string
  namespace: string
  status: string
  root_cause?: string
  problem_type?: string
  confidence?: number
  created_at: string
}
