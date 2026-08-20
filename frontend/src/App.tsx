import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from '@/layouts/MainLayout'
import { QueryPage } from '@/pages/QueryPage'
import { SourcesPage } from '@/pages/SourcesPage'
import { SystemPage } from '@/pages/SystemPage'
import '@/index.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <Layout>
              <QueryPage />
            </Layout>
          }
        />
        <Route
          path="/sources"
          element={
            <Layout>
              <SourcesPage />
            </Layout>
          }
        />
        <Route
          path="/system"
          element={
            <Layout>
              <SystemPage />
            </Layout>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
