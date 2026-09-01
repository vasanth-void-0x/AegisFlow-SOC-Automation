import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export function LoginPage() {
  const { user, login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  if (user) return <Navigate to="/" replace />
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setBusy(true); setError('')
    try { await login(username, password); navigate((location.state as { from?: string } | null)?.from || '/', { replace: true }) }
    catch (e) { setError((e as Error).message) }
    finally { setBusy(false) }
  }
  return <main className="login-screen"><section className="login-card"><img src="/aegisflow-v-core.png" alt="BlueOrch"/><span>SECURE SOC ACCESS</span><h1>BLUE<span>ORCH</span></h1><p>Authenticate to access incident operations.</p><form onSubmit={submit}><label>USERNAME<input autoFocus autoComplete="username" value={username} onChange={e=>setUsername(e.target.value)} /></label><label>PASSWORD<input type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} /></label>{error&&<div className="login-error">{error}</div>}<button disabled={busy}>{busy?'AUTHENTICATING…':'SIGN IN'}</button></form><small>Role-based access · HttpOnly session · Human approval gate</small></section></main>
}
