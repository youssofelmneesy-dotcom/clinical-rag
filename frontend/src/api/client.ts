/**
 * Clinical RAG API Client
 * Centralized API communication with the backend
 */

import {
  ClinicalQueryResponse,
  HealthResponse,
  QueryRequest,
} from '../types/api'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

class APIError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(`API Error ${status}: ${detail}`)
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `HTTP ${response.status}`
    try {
      const data = await response.json()
      detail = data.detail || detail
    } catch {
      detail = response.statusText || detail
    }
    throw new APIError(response.status, detail)
  }

  return response.json() as Promise<T>
}

export const clinicalApi = {
  /**
   * Query the clinical RAG system
   */
  async query(
    request: QueryRequest,
  ): Promise<ClinicalQueryResponse> {
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: request.question,
        k: request.k || 5,
        show_evidence: request.show_evidence !== false,
      }),
    })

    return handleResponse<ClinicalQueryResponse>(response)
  },

  /**
   * Check API health status
   */
  async health(): Promise<HealthResponse> {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    return handleResponse<HealthResponse>(response)
  },
}

export { APIError }
