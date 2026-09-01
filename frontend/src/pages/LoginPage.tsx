import { useState, type FormEvent } from 'react'
import { useAuth } from '../auth/AuthContext'

export function LoginPage() {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const submit = async (event: FormEvent) => { event.preventDefault(); setBusy(true); setError(''); try { await login(username, password) } catch { setError('Invalid username or password') } finally { setBusy(false) } }

  return <main className="login-page">
    <div className="login-grid" aria-hidden="true"/><div className="login-orb login-orb-one" aria-hidden="true"/><div className="login-orb login-orb-two" aria-hidden="true"/>
    <form className="login-card" onSubmit={submit} autoComplete="off">
      <div className="login-brand"><div className="login-winged-v"><span className="login-logo-ring"/><img src="/v-wings-sticker.png" alt="BlueOrch winged V"/></div><div className="login-wordmark"><b>BLUE</b><span>ORCH</span></div><small>SOC AUTOMATION CORE</small></div>
      <div className="login-heading"><span><i/> SECURE OPERATOR ACCESS</span><h1>Welcome back</h1><p>Authenticate to enter the BlueOrch command centre.</p></div>
      <label><span>USERNAME</span><div className="login-input"><i aria-hidden="true">01</i><input name="blueorch_operator" autoComplete="off" value={username} onChange={event=>setUsername(event.target.value)} placeholder="Username" required/></div></label>
      <label><span>PASSWORD</span><div className="login-input"><i aria-hidden="true">••</i><input name="blueorch_access_code" type="password" autoComplete="new-password" value={password} onChange={event=>setPassword(event.target.value)} placeholder="Password" required minLength={12}/></div></label>
      {error&&<div className="login-error" role="alert">{error}</div>}
      <button className="login-submit" disabled={busy}><span>{busy?'AUTHENTICATING…':'ENTER COMMAND CENTRE'}</span><b>→</b></button>
      <div className="login-roles"><span>ADMIN</span><span>ANALYST</span><span>VIEWER</span></div><footer><i/> ENCRYPTED SESSION · HUMAN-GATED RESPONSE</footer>
    </form>
  </main>
}
