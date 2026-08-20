/**
 * Clinical RAG API Types
 * Matches backend response schemas from backend/api.py
 */

export interface QueryMetrics {
  latency_ms: number
  retrieval_latency_ms: number
  generation_latency_ms: number
  validation_latency_ms: number
}

export interface Citation {
  chunk_id: string
  document: string
  source_filename: string
  section: string
  page: number
}

export interface Evidence {
  rank: number
  chunk_id: string
  document: string
  section: string
  page: number
  similarity: number
  preview: string
}

export type QueryStatus =
  | 'answered'
  | 'out_of_scope'
  | 'insufficient_evidence'
  | 'claim_verification_failed'

export interface ClinicalQueryResponse {
  answer: string | null
  status: QueryStatus
  confidence: number | null
  confidence_threshold: number
  citations: Citation[]
  evidence: Evidence[]
  in_scope: boolean
  claims_verified: boolean
  metrics: QueryMetrics | null
  reason: string | null
}

export interface HealthResponse {
  status: string
  service: string
  version: string
  timestamp: string
}

export interface QueryRequest {
  question: string
  k?: number
  show_evidence?: boolean
}

// Derived types for frontend
export interface QueryResult {
  question: string
  response: ClinicalQueryResponse
  timestamp: Date
}

export interface LoadingState {
  isLoading: boolean
  error: string | null
}
