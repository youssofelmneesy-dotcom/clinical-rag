import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Stethoscope } from 'lucide-react'

interface LayoutProps {
  children: React.ReactNode
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation()

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="flex flex-col min-h-screen bg-clinical-50">
      {/* Header */}
      <header className="bg-white border-b border-clinical-200 shadow-sm">
        <nav className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 no-underline">
            <Stethoscope className="w-8 h-8 text-clinical-700" />
            <div>
              <h1 className="text-2xl font-bold text-clinical-900">Clinical RAG</h1>
              <p className="text-sm text-clinical-600">Evidence-Grounded COPD Guidance</p>
            </div>
          </Link>

          <div className="flex gap-1">
            <Link
              to="/"
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                isActive('/')
                  ? 'bg-clinical-700 text-white'
                  : 'text-clinical-700 hover:bg-clinical-100'
              }`}
            >
              Query
            </Link>
            <Link
              to="/sources"
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                isActive('/sources')
                  ? 'bg-clinical-700 text-white'
                  : 'text-clinical-700 hover:bg-clinical-100'
              }`}
            >
              Sources
            </Link>
            <Link
              to="/system"
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                isActive('/system')
                  ? 'bg-clinical-700 text-white'
                  : 'text-clinical-700 hover:bg-clinical-100'
              }`}
            >
              System
            </Link>
          </div>
        </nav>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-clinical-200 bg-white mt-12">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-clinical-600">
            Clinical RAG System • Evidence-grounded answers from GOLD 2026 and NICE NG115 guidelines
          </p>
        </div>
      </footer>
    </div>
  )
}
