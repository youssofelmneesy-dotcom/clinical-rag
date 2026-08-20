import { AlertCircle, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react'
import type { ClinicalQueryResponse } from '@/types/api'

interface StatusIndicatorProps {
  status: string
  inScope: boolean
  claimsVerified: boolean
}

export function StatusIndicator({
  status,
  inScope,
  claimsVerified,
}: StatusIndicatorProps) {
  const isAnswered = status === 'answered'
  const isOutOfScope = status === 'out_of_scope'
  const isInsufficient = status === 'insufficient_evidence'
  const isVerificationFailed = status === 'claim_verification_failed'

  return (
    <div className="space-y-2">
      {isAnswered && (
        <div className="flex items-center gap-2 text-safe">
          <CheckCircle className="w-5 h-5" />
          <span className="font-medium">Answered</span>
        </div>
      )}

      {isOutOfScope && (
        <div className="flex items-center gap-2 text-caution">
          <AlertTriangle className="w-5 h-5" />
          <span className="font-medium">Out of Scope</span>
        </div>
      )}

      {isInsufficient && (
        <div className="flex items-center gap-2 text-caution">
          <AlertCircle className="w-5 h-5" />
          <span className="font-medium">Insufficient Evidence</span>
        </div>
      )}

      {isVerificationFailed && (
        <div className="flex items-center gap-2 text-alert">
          <AlertCircle className="w-5 h-5" />
          <span className="font-medium">Verification Failed</span>
        </div>
      )}

      {inScope && (
        <div className="flex items-center gap-2 text-clinical-600 text-sm">
          <span>✓ In scope</span>
        </div>
      )}

      {claimsVerified && (
        <div className="flex items-center gap-2 text-clinical-600 text-sm">
          <span>✓ Claims verified</span>
        </div>
      )}
    </div>
  )
}

interface LoadingStateProps {
  isLoading: boolean
}

export function LoadingState({ isLoading }: LoadingStateProps) {
  if (!isLoading) return null

  return (
    <div className="flex flex-col items-center justify-center gap-4 py-12">
      <Loader2 className="w-8 h-8 text-clinical-600 animate-spin" />
      <p className="text-clinical-600 font-medium">Processing your question...</p>
      <p className="text-clinical-500 text-sm">
        Retrieving evidence from approved guidelines
      </p>
    </div>
  )
}

interface ErrorStateProps {
  error: string | null
  onRetry?: () => void
}

export function ErrorState({ error, onRetry }: ErrorStateProps) {
  if (!error) return null

  return (
    <div className="rounded-lg border border-alert bg-red-50 p-6">
      <div className="flex items-start gap-4">
        <AlertCircle className="w-6 h-6 text-alert flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="font-semibold text-alert mb-2">Error</h3>
          <p className="text-clinical-700 mb-4">{error}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-4 py-2 bg-alert text-white rounded-lg font-medium hover:bg-red-700 transition-colors"
            >
              Try Again
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

interface AnswerPanelProps {
  response: ClinicalQueryResponse | null
  isLoading: boolean
  error: string | null
}

export function AnswerPanel({
  response,
  isLoading,
  error,
}: AnswerPanelProps) {
  if (isLoading) {
    return <LoadingState isLoading={true} />
  }

  if (error) {
    return <ErrorState error={error} />
  }

  if (!response) {
    return null
  }

  const isAnswered = response.status === 'answered'
  const isOutOfScope = response.status === 'out_of_scope'

  return (
    <div className="space-y-6">
      {/* Answer Box */}
      <div className="rounded-lg border border-clinical-200 bg-white p-8 shadow-sm">
        <StatusIndicator
          status={response.status}
          inScope={response.in_scope}
          claimsVerified={response.claims_verified}
        />

        {isAnswered && (
          <div className="mt-6">
            <h2 className="text-lg font-semibold text-clinical-900 mb-4">
              Clinical Answer
            </h2>
            <div className="prose prose-sm max-w-none text-clinical-800 leading-relaxed whitespace-pre-wrap">
              {response.answer}
            </div>

            {response.confidence !== null && (
              <div className="mt-6 pt-6 border-t border-clinical-200">
                <div className="flex items-baseline gap-2">
                  <span className="text-sm font-medium text-clinical-600">
                    Confidence:
                  </span>
                  <span className="text-lg font-semibold text-clinical-900">
                    {(response.confidence * 100).toFixed(1)}%
                  </span>
                  <span className="text-sm text-clinical-500">
                    (threshold: {(response.confidence_threshold * 100).toFixed(1)}%)
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {isOutOfScope && (
          <div className="mt-6">
            <h2 className="text-lg font-semibold text-caution mb-4">
              Unable to Provide Answer
            </h2>
            <p className="text-clinical-700 mb-4">
              {response.reason ||
                'This question is outside the supported clinical scope.'}
            </p>
            <p className="text-sm text-clinical-600">
              This system provides evidence-grounded guidance for COPD management
              from approved clinical guidelines (GOLD 2026, NICE NG115).
            </p>
          </div>
        )}

        {!isAnswered && !isOutOfScope && (
          <div className="mt-6">
            <h2 className="text-lg font-semibold text-clinical-900 mb-4">
              Unable to Provide Answer
            </h2>
            <p className="text-clinical-700">
              {response.reason ||
                'The system could not provide a supported answer based on the available evidence.'}
            </p>
          </div>
        )}
      </div>

      {/* Metrics */}
      {response.metrics && (
        <div className="text-sm text-clinical-600 text-center">
          Response time: {(response.metrics.latency_ms / 1000).toFixed(3)}s
        </div>
      )}
    </div>
  )
}
