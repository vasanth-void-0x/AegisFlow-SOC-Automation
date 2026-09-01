import { BrowserRouter, Navigate, Routes, Route, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'
import { AuthProvider, useAuth } from './auth/AuthContext'
import { AppShell } from './components/AppShell'
import { OverviewPage } from './pages/OverviewPage'
import { IncidentQueuePage } from './pages/IncidentQueuePage'
import { IncidentDetailPage } from './pages/IncidentDetailPage'
import { ApprovalCentrePage } from './pages/ApprovalCentrePage'
import { McpToolHistoryPage } from './pages/McpToolHistoryPage'
import { AuditLogPage } from './pages/AuditLogPage'
import { SystemHealthPage } from './pages/SystemHealthPage'
import { SettingsPage } from './pages/SettingsPage'
import { LoginPage } from './pages/LoginPage'

function Protected({ children, admin = false }: { children: ReactNode; admin?: boolean }) {
  const { loading, user, isAdmin } = useAuth(); const location = useLocation()
  if (loading) return <div className="auth-loading">CONNECTING TO SECURITY CORE…</div>
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (admin && !isAdmin) return <Navigate to="/" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter><AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<Protected><AppShell /></Protected>}>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/incidents" element={<IncidentQueuePage />} />
          <Route path="/incidents/:id" element={<IncidentDetailPage />} />
          <Route path="/approvals" element={<ApprovalCentrePage />} />
          <Route path="/mcp-tools" element={<McpToolHistoryPage />} />
          <Route path="/audit" element={<AuditLogPage />} />
          <Route path="/health" element={<SystemHealthPage />} />
          <Route path="/settings" element={<Protected admin><SettingsPage /></Protected>} />
        </Route>
      </Routes>
    </AuthProvider></BrowserRouter>
  )
}
