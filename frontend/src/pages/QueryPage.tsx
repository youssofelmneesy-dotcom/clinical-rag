import { Loader2 } from 'lucide-react'
import { useState } from 'react'
import type { QueryRequest, ClinicalQueryResponse } from '@/types/api'
import { clinicalApi, APIError } from '@/api/client'
import { AnswerPanel } from '@/components/AnswerPanel'
import { EvidenceSection } from '@/components/Evidence'

const EXAMPLE_QUESTIONS = [
  'What does GOLD recommend regarding inhaled corticosteroids for COPD?',
  'What are the criteria for diagnosing COPD according to NICE guidelines?',
  'What is the role of pulmonary rehabilitation in COPD management?',
  'When should oxygen therapy be considered in COPD patients?',
]

export function QueryPage() {
  const [question, setQuestion] = useState('')
  const [response, setResponse] = useState<ClinicalQueryResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [queryHistory, setQueryHistory] = useState<
    Array<{ question: string; response: ClinicalQueryResponse }>
  >([])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim()) return

    setIsLoading(true)
    setError(null)
    setResponse(null)

    try {
      const request: QueryRequest = {
        question: question.trim(),
        k: 5,
        show_evidence: true,
      }

      const result = await clinicalApi.query(request)
      setResponse(result)
      setQueryHistory((prev) => [{ question: question.trim(), response: result }, ...prev])
    } catch (err) {
      if (err instanceof APIError) {
        setError(`Error ${err.status}: ${err.detail}`)
      } else if (err instanceof TypeError) {
        setError('Unable to connect to backend. Is the API server running?')
      } else {
        setError('An unexpected error occurred')
      }
      console.error('Query error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleExampleQuestion = (exampleQuestion: string) => {
    setQuestion(exampleQuestion)
  }

  const handleClear = () => {
    setQuestion('')
    setResponse(null)
    setError(null)
  }

  return (
    <div className="space-y-8">
      {/* Query Form */}
      <div className="rounded-lg border border-clinical-200 bg-white p-8 shadow-sm">
        <h2 className="text-2xl font-bold text-clinical-900 mb-2">
          Ask a Clinical Question
        </h2>
        <p className="text-clinical-600 mb-6">
          Query evidence-grounded COPD guidance from approved clinical guidelines
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="question"
              className="block text-sm font-medium text-clinical-900 mb-2"
            >
              Your Question
            </label>
            <textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={isLoading}
              placeholder="For example: What are the diagnostic criteria for COPD?"
              className="w-full px-4 py-3 border border-clinical-300 rounded-lg font-medium focus:outline-none focus:ring-2 focus:ring-clinical-700 focus:border-transparent disabled:bg-clinical-50 disabled:text-clinical-600"
              rows={3}
            />
          </div>

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={!question.trim() || isLoading}
              className="px-6 py-3 bg-clinical-700 text-white font-semibold rounded-lg hover:bg-clinical-800 disabled:bg-clinical-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
              {isLoading ? 'Processing...' : 'Ask'}
            </button>

            <button
              type="button"
              onClick={handleClear}
              disabled={!question && !response}
              className="px-6 py-3 border border-clinical-300 text-clinical-700 font-semibold rounded-lg hover:bg-clinical-50 disabled:text-clinical-400 disabled:cursor-not-allowed transition-colors"
            >
              Clear
            </button>
          </div>
        </form>

        {/* Example Questions */}
        {!response && (
          <div className="mt-8 pt-8 border-t border-clinical-200">
            <p className="text-sm font-medium text-clinical-700 mb-4">
              Example Questions:
            </p>
            <div className="space-y-2">
              {EXAMPLE_QUESTIONS.map((example, idx) => (
                <button
                  key={idx}
                  onClick={() => handleExampleQuestion(example)}
                  className="w-full text-left px-4 py-2 bg-clinical-50 hover:bg-clinical-100 text-clinical-800 rounded-lg transition-colors text-sm"
                >
                  • {example}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      <AnswerPanel response={response} isLoading={isLoading} error={error} />

      {/* Evidence Section */}
      {response && response.evidence && response.evidence.length > 0 && (
        <EvidenceSection
          evidence={response.evidence}
          citations={response.citations}
        />
      )}

      {/* Query History */}
      {queryHistory.length > 1 && (
        <div className="rounded-lg border border-clinical-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-clinical-900 mb-4">
            Query History (This Session)
          </h3>
          <div className="space-y-2">
            {queryHistory.slice(1, 6).map((item, idx) => (
              <button
                key={idx}
                onClick={() => setQuestion(item.question)}
                className="w-full text-left px-4 py-2 bg-clinical-50 hover:bg-clinical-100 rounded-lg transition-colors"
              >
                <p className="text-sm font-medium text-clinical-900">
                  {item.question.substring(0, 80)}
                  {item.question.length > 80 ? '...' : ''}
                </p>
                <p className="text-xs text-clinical-600 mt-1">
                  Status: {item.response.status}
                </p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
