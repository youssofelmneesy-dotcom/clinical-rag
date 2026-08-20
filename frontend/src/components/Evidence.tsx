import { FileText, MapPin } from 'lucide-react'
import type { Citation, Evidence } from '@/types/api'

interface EvidenceCardProps {
  evidence: Evidence
}

export function EvidenceCard({ evidence }: EvidenceCardProps) {
  return (
    <div className="rounded-lg border border-clinical-200 bg-white p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-clinical-600 flex-shrink-0" />
          <div>
            <p className="font-semibold text-clinical-900">{evidence.document}</p>
            <p className="text-sm text-clinical-600">{evidence.chunk_id}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs text-clinical-600">Rank {evidence.rank}</p>
          <p className="text-sm font-semibold text-clinical-900">
            {(evidence.similarity * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      <div className="space-y-2 mb-3">
        <div className="flex items-center gap-2 text-sm">
          <MapPin className="w-4 h-4 text-clinical-600 flex-shrink-0" />
          <span className="text-clinical-700">
            <strong>Page:</strong> {evidence.page}
          </span>
        </div>
        {evidence.section && (
          <div className="text-sm text-clinical-700">
            <strong>Section:</strong> {evidence.section}
          </div>
        )}
      </div>

      <div className="p-3 bg-clinical-50 rounded border border-clinical-200">
        <p className="text-sm text-clinical-700 leading-relaxed">
          {evidence.preview}
          {evidence.preview.length === 200 && '...'}
        </p>
      </div>
    </div>
  )
}

interface CitationProps {
  citation: Citation
  index: number
}

export function CitationBadge({ citation, index }: CitationProps) {
  return (
    <div className="inline-flex items-center gap-2 px-3 py-1 bg-clinical-100 rounded-full border border-clinical-300 text-sm">
      <span className="font-semibold text-clinical-700">[{index}]</span>
      <span className="text-clinical-700">
        {citation.document} • Page {citation.page}
      </span>
    </div>
  )
}

interface EvidenceSectionProps {
  evidence: Evidence[]
  citations: Citation[]
}

export function EvidenceSection({
  evidence,
  citations,
}: EvidenceSectionProps) {
  if (evidence.length === 0) return null

  return (
    <div className="rounded-lg border border-clinical-200 bg-white p-6 shadow-sm">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-clinical-900 mb-2">Evidence</h2>
        <p className="text-sm text-clinical-600">
          Retrieved and ranked evidence chunks from approved sources
        </p>
      </div>

      <div className="space-y-4">
        {evidence.map((item) => (
          <EvidenceCard key={item.chunk_id} evidence={item} />
        ))}
      </div>

      {citations.length > 0 && (
        <div className="mt-6 pt-6 border-t border-clinical-200">
          <h3 className="font-semibold text-clinical-900 mb-4">
            Citation Details
          </h3>
          <div className="space-y-3">
            {citations.map((citation, idx) => (
              <div
                key={citation.chunk_id}
                className="p-3 bg-clinical-50 rounded border border-clinical-200"
              >
                <div className="flex gap-2 mb-2">
                  <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-clinical-700 text-white text-xs font-semibold">
                    {idx + 1}
                  </span>
                  <div className="flex-1">
                    <p className="font-medium text-clinical-900">
                      {citation.document}
                    </p>
                    <p className="text-sm text-clinical-600">
                      {citation.source_filename}
                    </p>
                  </div>
                </div>
                <div className="ml-8 space-y-1 text-sm text-clinical-700">
                  <p>
                    <strong>Section:</strong> {citation.section}
                  </p>
                  <p>
                    <strong>Page:</strong> {citation.page}
                  </p>
                  <p>
                    <strong>Chunk ID:</strong> {citation.chunk_id}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
