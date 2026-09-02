import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { OverviewPage } from './pages/OverviewPage'
import { IncidentQueuePage } from './pages/IncidentQueuePage'
import { IncidentDetailPage } from './pages/IncidentDetailPage'
import { ApprovalCentrePage } from './pages/ApprovalCentrePage'
import { McpToolHistoryPage } from './pages/McpToolHistoryPage'
import { AuditLogPage } from './pages/AuditLogPage'
import { SystemHealthPage } from './pages/SystemHealthPage'
import { SettingsPage } from './pages/SettingsPage'
import { AuthProvider, useAuth } from './auth/AuthContext'
import { LoginPage } from './pages/LoginPage'
import { AboutPage } from './pages/AboutPage'

function SecuredApp(){const {loading,enabled,user}=useAuth();if(loading)return <div className="auth-loading">CONNECTING TO SECURITY CORE…</div>;if(enabled&&!user)return <LoginPage/>;return <BrowserRouter><Routes><Route element={<AppShell />}><Route path="/" element={<OverviewPage />} /><Route path="/incidents" element={<IncidentQueuePage />} /><Route path="/incidents/:id" element={<IncidentDetailPage />} /><Route path="/approvals" element={<ApprovalCentrePage />} /><Route path="/mcp-tools" element={<McpToolHistoryPage />} /><Route path="/audit" element={<AuditLogPage />} /><Route path="/health" element={<SystemHealthPage />} /><Route path="/settings" element={<SettingsPage />} /><Route path="/about" element={<AboutPage />} /></Route></Routes></BrowserRouter>}

export default function App() {
  return (
    <AuthProvider><SecuredApp/></AuthProvider>
  )
}
