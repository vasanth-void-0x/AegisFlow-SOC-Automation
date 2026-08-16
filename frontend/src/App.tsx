import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { OverviewPage } from './pages/OverviewPage'
import { IncidentQueuePage } from './pages/IncidentQueuePage'
import { IncidentDetailPage } from './pages/IncidentDetailPage'
import { ApprovalCentrePage } from './pages/ApprovalCentrePage'
import { McpToolHistoryPage } from './pages/McpToolHistoryPage'
import { AuditLogPage } from './pages/AuditLogPage'
import { SystemHealthPage } from './pages/SystemHealthPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/incidents" element={<IncidentQueuePage />} />
          <Route path="/incidents/:id" element={<IncidentDetailPage />} />
          <Route path="/approvals" element={<ApprovalCentrePage />} />
          <Route path="/mcp-tools" element={<McpToolHistoryPage />} />
          <Route path="/audit" element={<AuditLogPage />} />
          <Route path="/health" element={<SystemHealthPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
