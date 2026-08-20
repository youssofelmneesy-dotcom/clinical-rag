import { ExternalLink } from 'lucide-react'

const SOURCES = [
  {
    id: 'gold-2026',
    name: 'GOLD 2026 Global Strategy Report',
    organization: 'Global Initiative for Chronic Obstructive Lung Disease',
    url: 'https://goldcopd.org/2026-gold-report/',
    version: '2026 v1.3',
    release_date: 'December 8, 2025',
    chunks: 408,
    coverage: [
      'COPD diagnosis and classification',
      'Spirometry and diagnostic testing',
      'Pharmacological treatment',
      'Inhaled therapies',
      'Exacerbation management',
      'Comorbidities',
      'Pulmonary rehabilitation',
      'Smoking cessation',
      'Oxygen therapy',
      'Follow-up strategies',
    ],
    scope: 'Global clinical guidance',
    jurisdiction: 'Worldwide',
    official_status: 'Primary guideline',
  },
  {
    id: 'nice-ng115',
    name: 'NICE NG115: Chronic obstructive pulmonary disease in over 16s: diagnosis and management',
    organization:
      'National Institute for Health and Care Excellence (NICE)',
    url: 'https://www.nice.org.uk/guidance/ng115',
    version: 'NG115',
    release_date: '2018 (updated regularly)',
    chunks: 117,
    coverage: [
      'Diagnosis criteria and spirometry',
      'Patient assessment',
      'Treatment recommendations',
      'Inhaled medicines',
      'Pulmonary rehabilitation',
      'Acute exacerbation management',
      'End of life care',
      'Patient education',
      'Integrated care pathways',
    ],
    scope: 'UK clinical guidance',
    jurisdiction: 'United Kingdom',
    official_status: 'Primary guideline',
  },
]

export function SourcesPage() {
  return (
    <div className="space-y-8">
      {/* Introduction */}
      <div className="rounded-lg border border-clinical-200 bg-white p-8 shadow-sm">
        <h1 className="text-3xl font-bold text-clinical-900 mb-4">
          Approved Clinical Guidelines
        </h1>
        <p className="text-lg text-clinical-700 leading-relaxed">
          This system provides evidence-grounded COPD clinical guidance from a
          curated set of approved clinical guidelines. Only these sources are
          included in the knowledge base and used for answering clinical
          questions.
        </p>
      </div>

      {/* Source Cards */}
      <div className="space-y-6">
        {SOURCES.map((source) => (
          <div
            key={source.id}
            className="rounded-lg border border-clinical-200 bg-white p-8 shadow-sm hover:shadow-md transition-shadow"
          >
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-clinical-900 mb-2">
                  {source.name}
                </h2>
                <p className="text-clinical-600 font-medium mb-2">
                  {source.organization}
                </p>
                <p className="text-sm text-clinical-600">
                  Version {source.version} • {source.release_date}
                </p>
              </div>
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-6 py-3 bg-clinical-700 text-white font-semibold rounded-lg hover:bg-clinical-800 transition-colors whitespace-nowrap"
              >
                View Official
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6 pb-6 border-b border-clinical-200">
              <div>
                <p className="text-sm font-medium text-clinical-600 mb-1">
                  Indexed Chunks
                </p>
                <p className="text-2xl font-bold text-clinical-900">
                  {source.chunks}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-clinical-600 mb-1">
                  Jurisdiction
                </p>
                <p className="text-lg font-semibold text-clinical-900">
                  {source.jurisdiction}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-clinical-600 mb-1">
                  Status
                </p>
                <p className="text-lg font-semibold text-safe">
                  {source.official_status}
                </p>
              </div>
            </div>

            {/* Coverage */}
            <div>
              <h3 className="font-semibold text-clinical-900 mb-3">
                Topic Coverage
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {source.coverage.map((topic, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-2 text-clinical-700"
                  >
                    <span className="text-safe">✓</span>
                    <span>{topic}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Information */}
      <div className="rounded-lg border border-clinical-200 bg-clinical-50 p-8">
        <h2 className="text-lg font-semibold text-clinical-900 mb-4">
          About These Guidelines
        </h2>
        <div className="space-y-4 text-clinical-700">
          <p>
            <strong>Source Selection:</strong> These guidelines were selected based
            on their clinical rigor, evidence base, and international adoption. They
            represent current best practices in COPD management.
          </p>
          <p>
            <strong>Whitelist Approach:</strong> All evidence retrieved to answer
            questions comes exclusively from these approved sources. The system
            will not use external sources or generate answers from general
            knowledge.
          </p>
          <p>
            <strong>Clinical Safety:</strong> When the system cannot find sufficient
            evidence in these guidelines to support an answer, it will refuse to
            answer rather than speculate or use information from other sources.
          </p>
          <p>
            <strong>Scope:</strong> This system focuses specifically on COPD
            (Chronic Obstructive Pulmonary Disease) in adult populations. Questions
            outside this scope will be declined.
          </p>
        </div>
      </div>
    </div>
  )
}
