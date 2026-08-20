import { useEffect, useState } from 'react'
import { CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { clinicalApi, APIError } from '@/api/client'
import type { HealthResponse } from '@/types/api'

interface SystemStats {
  chunks: number
  sources: number
  precision: number
  recall: number
  hitRate: number
  refusalAccuracy: number
  citationTraceability: number
  claimVerification: number
  p50Latency: number
  p95Latency: number
}

const CONSTANT_STATS: SystemStats = {
  chunks: 525,
  sources: 2,
  precision: 0.740,
  recall: 0.967,
  hitRate: 0.967,
  refusalAccuracy: 1.0,
  citationTraceability: 1.0,
  claimVerification: 0.983,
  p50Latency: 348,
  p95Latency: 843,
}

const APPROVED_SOURCES = [
  {
    id: 'gold-2026',
    name: 'GOLD 2026 Global Strategy Report',
    publisher: 'Global Initiative for Chronic Obstructive Lung Disease',
    version: '2026 v1.3',
    chunks: 408,
    url: 'https://goldcopd.org/2026-gold-report/',
    jurisdiction: 'Global',
  },
  {
    id: 'nice-ng115',
    name: 'NICE NG115: Chronic obstructive pulmonary disease in over 16s: diagnosis and management',
    publisher: 'National Institute for Health and Care Excellence',
    version: 'NG115',
    chunks: 117,
    url: 'https://www.nice.org.uk/guidance/ng115',
    jurisdiction: 'United Kingdom',
  },
]

function MetricCard({
  label,
  value,
  percentage = false,
}: {
  label: string
  value: number
  percentage?: boolean
}) {
  return (
    <div className="rounded-lg border border-clinical-200 bg-white p-6 text-center">
      <p className="text-clinical-600 text-sm font-medium mb-2">{label}</p>
      <p className="text-3xl font-bold text-clinical-900">
        {percentage ? `${(value * 100).toFixed(1)}%` : value}
      </p>
    </div>
  )
}

export function SystemPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [isHealthLoading, setIsHealthLoading] = useState(true)
  const [healthError, setHealthError] = useState<string | null>(null)

  useEffect(() => {
    const checkHealth = async () => {
      setIsHealthLoading(true)
      setHealthError(null)
      try {
        const response = await clinicalApi.health()
        setHealth(response)
      } catch (err) {
        if (err instanceof APIError) {
          setHealthError(`API Error: ${err.detail}`)
        } else {
          setHealthError('Unable to connect to backend')
        }
      } finally {
        setIsHealthLoading(false)
      }
    }

    checkHealth()
    const interval = setInterval(checkHealth, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-8">
      {/* Backend Health */}
      <div className="rounded-lg border border-clinical-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-clinical-900 mb-4">
          Backend Status
        </h2>

        {isHealthLoading && (
          <div className="flex items-center gap-2 text-clinical-600">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Checking health...</span>
          </div>
        )}

        {healthError && (
          <div className="flex items-center gap-2 text-alert">
            <AlertCircle className="w-5 h-5" />
            <span>{healthError}</span>
          </div>
        )}

        {health && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-safe">
              <CheckCircle className="w-5 h-5" />
              <span className="font-medium">API Online</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm text-clinical-600">
              <div>
                <p className="font-medium">Service</p>
                <p>{health.service}</p>
              </div>
              <div>
                <p className="font-medium">Version</p>
                <p>{health.version}</p>
              </div>
              <div>
                <p className="font-medium">Last Check</p>
                <p>{new Date(health.timestamp).toLocaleTimeString()}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Knowledge Base Overview */}
      <div className="rounded-lg border border-clinical-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-clinical-900 mb-6">
          Knowledge Base Overview
        </h2>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
          <MetricCard label="Indexed Chunks" value={CONSTANT_STATS.chunks} />
          <MetricCard label="Approved Sources" value={CONSTANT_STATS.sources} />
        </div>

        <div className="space-y-4">
          <h3 className="font-semibold text-clinical-900">Approved Guidelines</h3>
          {APPROVED_SOURCES.map((source) => (
            <div
              key={source.id}
              className="p-4 border border-clinical-200 rounded-lg hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h4 className="font-semibold text-clinical-900">
                    {source.name}
                  </h4>
                  <p className="text-sm text-clinical-600 mt-1">
                    {source.publisher}
                  </p>
                </div>
                <span className="text-xs bg-clinical-100 text-clinical-700 px-3 py-1 rounded-full font-medium">
                  {source.chunks} chunks
                </span>
              </div>
              <div className="grid grid-cols-2 text-sm text-clinical-600 gap-2">
                <div>
                  <span className="font-medium">Version:</span> {source.version}
                </div>
                <div>
                  <span className="font-medium">Jurisdiction:</span>{' '}
                  {source.jurisdiction}
                </div>
              </div>
              {source.url && (
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-clinical-700 hover:underline text-sm mt-2 inline-block"
                >
                  Official guideline →
                </a>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Evaluation Metrics */}
      <div className="rounded-lg border border-clinical-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-clinical-900 mb-2">
          Evaluation Metrics
        </h2>
        <p className="text-sm text-clinical-600 mb-6">
          Results from 60-case evaluation benchmark using GOLD 2026 and NICE NG115
          guidelines
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard label="Precision@5" value={CONSTANT_STATS.precision} percentage />
          <MetricCard label="Recall@5" value={CONSTANT_STATS.recall} percentage />
          <MetricCard label="Hit Rate@5" value={CONSTANT_STATS.hitRate} percentage />
          <MetricCard
            label="Refusal Accuracy"
            value={CONSTANT_STATS.refusalAccuracy}
            percentage
          />
          <MetricCard
            label="Citation Traceability"
            value={CONSTANT_STATS.citationTraceability}
            percentage
          />
          <MetricCard
            label="Claim Verification"
            value={CONSTANT_STATS.claimVerification}
            percentage
          />
        </div>
      </div>

      {/* Performance */}
      <div className="rounded-lg border border-clinical-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-clinical-900 mb-6">
          Performance Characteristics
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <MetricCard label="P50 Latency (warm)" value={CONSTANT_STATS.p50Latency} />
          <MetricCard label="P95 Latency (warm)" value={CONSTANT_STATS.p95Latency} />
        </div>

        <div className="mt-6 p-4 bg-clinical-50 rounded-lg border border-clinical-200">
          <p className="text-sm text-clinical-700">
            <strong>Note:</strong> Latency values are in milliseconds for warm
            instances. Cold initialization requires approximately 28.6 seconds.
            Production deployments should maintain a warm instance pool.
          </p>
        </div>
      </div>

      {/* Architecture Info */}
      <div className="rounded-lg border border-clinical-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-clinical-900 mb-4">
          System Architecture
        </h2>

        <div className="space-y-2 text-sm text-clinical-700">
          <div className="flex items-center gap-2">
            <span className="text-clinical-600">✓</span>
            <span>Dense semantic retrieval (sentence-transformers)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-clinical-600">✓</span>
            <span>BM25 lexical retrieval</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-clinical-600">✓</span>
            <span>Hybrid retrieval with deterministic reranking</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-clinical-600">✓</span>
            <span>COPD scope detection</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-clinical-600">✓</span>
            <span>Confidence gating with threshold safety</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-clinical-600">✓</span>
            <span>Citation validation</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-clinical-600">✓</span>
            <span>Claim verification</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-clinical-600">✓</span>
            <span>ChromaDB vector indexing</span>
          </div>
        </div>
      </div>
    </div>
  )
}
