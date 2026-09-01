import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { useEffect, useRef, useState, type ReactNode } from 'react'
import { api } from '../api/client'
import type { HealthStatus, ResponseProposal } from '../api/types'
import { useAuth } from '../auth/AuthContext'

const NAV_ITEMS = [
  { to: '/', label: 'Command Overview', end: true, icon: 'grid' },
  { to: '/incidents', label: 'Incident Queue', icon: 'alert' },
  { to: '/approvals', label: 'Approval Centre', icon: 'check' },
  { to: '/mcp-tools', label: 'MCP Tool History', icon: 'terminal' },
  { to: '/audit', label: 'Audit Log', icon: 'log' },
  { to: '/health', label: 'System Health', icon: 'pulse' },
  { to: '/settings', label: 'Settings', icon: 'settings' },
]
const PAGE_TITLES: Record<string,string> = {'/':'Command Overview','/incidents':'Incident Queue','/approvals':'Approval Centre','/mcp-tools':'MCP Tool History','/audit':'Audit Log','/health':'System Health','/settings':'SIEM Settings'}

function Icon({name}:{name:string}) {
  const paths:Record<string,ReactNode> = {
    grid:<><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
    alert:<><path d="M12 3 2.8 19h18.4L12 3Z"/><path d="M12 9v4M12 17h.01"/></>,
    check:<><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/></>,
    terminal:<><rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 9 3 3-3 3M13 15h4"/></>,
    log:<><path d="M5 3h11l3 3v15H5z"/><path d="M16 3v4h4M9 11h6M9 15h6"/></>,
    pulse:<path d="M3 12h4l2-6 4 12 2-6h6"/>,
    settings:<><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3V2.8h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z"/></>,
  }
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>
}

function MatrixRain(){
  const ref=useRef<HTMLCanvasElement>(null)
  useEffect(()=>{const canvas=ref.current;if(!canvas)return;const ctx=canvas.getContext('2d');if(!ctx)return;const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;let frame=0,last=0;let drops:{x:number;y:number;speed:number;alpha:number}[]=[];const cell=8;const glyphs='01001101VCORE<>[]{}';const resize=()=>{const ratio=Math.min(window.devicePixelRatio||1,2);const width=window.innerWidth;const height=window.innerHeight;canvas.width=width*ratio;canvas.height=height*ratio;canvas.style.width=`${width}px`;canvas.style.height=`${height}px`;ctx.setTransform(ratio,0,0,ratio,0,0);drops=Array.from({length:Math.ceil(width/cell)},(_,i)=>({x:i*cell+(Math.random()*3-1.5),y:Math.random()*-height,speed:reduced?0:.52+Math.random()*.48,alpha:.1+Math.random()*.3}))};const draw=(time:number)=>{if(time-last>44){last=time;const width=window.innerWidth;const height=window.innerHeight;const coreX=width*.52;const coreY=Math.min(420,155+(Math.min(1024,width*.8)/1800)*338);ctx.clearRect(0,0,width,height);ctx.font=`600 8px ${getComputedStyle(document.body).fontFamily}`;ctx.textAlign='center';drops.forEach(drop=>{if(drop.y>coreY+10){drop.y=-20-Math.random()*height*.55;drop.x=Math.random()*width}const progress=Math.max(0,Math.min(1,drop.y/coreY));const pull=Math.pow(progress,3)*.72;const x=drop.x+(coreX-drop.x)*pull;const edgeFade=Math.max(.12,1-Math.abs(x-coreX)/(width*.58));ctx.fillStyle=`rgba(40,201,255,${drop.alpha*edgeFade})`;ctx.shadowColor='#149dff';ctx.shadowBlur=progress>.72?4:1;ctx.fillText(glyphs[Math.floor(Math.random()*glyphs.length)],x,drop.y);if(!reduced)drop.y+=drop.speed})}frame=requestAnimationFrame(draw)};resize();window.addEventListener('resize',resize);frame=requestAnimationFrame(draw);return()=>{cancelAnimationFrame(frame);window.removeEventListener('resize',resize)}},[])
  return <canvas ref={ref} className="aegis-matrix"/>
}

function ProcessorNodes(){
  const paths=['M700 315 L640 282 L580 225 L520 225 L470 180 L410 180','M690 334 L620 334 L565 355 L500 355 L445 326 L330 326','M735 430 L670 430 L615 470 L555 470 L510 510 L410 510','M1100 300 L1190 250 L1270 250 L1330 190 L1445 190','M1110 355 L1210 355 L1280 382 L1340 420 L1400 458 L1490 458','M900 180 L900 130 L860 95 L860 45','M710 290 L650 250 L600 205 L545 205 L500 160 L430 160','M705 370 L630 390 L575 420 L520 420 L470 390 L385 390','M1090 280 L1170 225 L1240 225 L1300 165 L1410 165','M1095 390 L1180 405 L1250 445 L1310 490 L1420 490']
  const endpoints=[[392,111],[305,300],[392,493],[1667,161],[1713,460]]
  const junctions=[[700,315],[640,282],[580,225],[690,334],[565,355],[735,430],[615,470],[1100,300],[1190,250],[1110,355],[1280,382],[1400,458],[900,180],[900,130],[710,290],[705,370],[1090,280],[1095,390]]
  return <svg className="processor-node-layer" viewBox="0 0 1800 675" preserveAspectRatio="xMidYMid meet"><defs><filter id="traceGlow"><feGaussianBlur stdDeviation="4" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter><linearGradient id="traceEnergy"><stop offset="0" stopColor="#086fff" stopOpacity="0"/><stop offset=".42" stopColor="#19bfff"/><stop offset=".68" stopColor="#72e8ff"/><stop offset="1" stopColor="#087cff" stopOpacity="0"/></linearGradient></defs>{paths.map((path,i)=><path key={path} d={path} pathLength="100" className={`data-trace trace-${i+1}`} filter="url(#traceGlow)"/>)}{junctions.map(([cx,cy],i)=><circle key={`j${i}`} cx={cx} cy={cy} r="3.5" className={`circuit-junction pulse-delay-${i%6}`}/>)}{endpoints.map(([cx,cy],i)=><g key={`e${i}`} className={`endpoint-beacon pulse-delay-${i}`}><circle cx={cx} cy={cy} r="12" className="beacon-ring"/><circle cx={cx} cy={cy} r="4" className="beacon-core"/></g>)}</svg>
}

export function AppShell() {
  const {user,logout}=useAuth()
  const [health,setHealth]=useState<HealthStatus|null>(null)
  const [healthError,setHealthError]=useState(false)
  const [mobileNavOpen,setMobileNavOpen]=useState(false)
  const [notificationsOpen,setNotificationsOpen]=useState(false)
  const [pendingApprovals,setPendingApprovals]=useState<ResponseProposal[]>([])
  const [actionTab,setActionTab]=useState<'approvals'|'alerts'|'actions'|'system'>('approvals')
  const [decisionBusy,setDecisionBusy]=useState<string|null>(null)
  const location=useLocation()
  useEffect(()=>{let cancelled=false;const poll=()=>api.health().then(h=>!cancelled&&(setHealth(h),setHealthError(false))).catch(()=>!cancelled&&setHealthError(true));poll();const timer=setInterval(poll,15000);return()=>{cancelled=true;clearInterval(timer)}},[])
  useEffect(()=>{let cancelled=false;const poll=()=>api.listApprovals({status:'pending'}).then(items=>!cancelled&&setPendingApprovals(items)).catch(()=>undefined);poll();const timer=setInterval(poll,30000);return()=>{cancelled=true;clearInterval(timer)}},[])
  const healthLabel=healthError?'Backend offline':health?.status==='ok'?'All systems operational':'Checking systems'
  const currentTitle=location.pathname.startsWith('/incidents/')?'Incident Investigation':PAGE_TITLES[location.pathname]||'BlueOrch'
  const decide=async(action:'approve'|'reject',proposal:ResponseProposal)=>{if(user?.role==='viewer')return;setDecisionBusy(action);try{if(action==='approve')await api.approveProposal(proposal.id,user?.username||'local','Approved from BlueOrch Action Center');else await api.rejectProposal(proposal.id,user?.username||'local','Rejected from BlueOrch Action Center');setPendingApprovals(items=>items.filter(item=>item.id!==proposal.id))}finally{setDecisionBusy(null)}}
  return <div className="app-frame">
    {location.pathname==='/'&&<div className="aegis-bg-scene" aria-hidden="true"><MatrixRain/><div className="aegis-bg-picture"/><div className="core-energy"><span/></div><div className="core-startup-scan"/><ProcessorNodes/></div>}
    <div className="mobile-bar"><button onClick={()=>setMobileNavOpen(true)} aria-label="Open navigation"><Icon name="grid"/></button><span>BLUEORCH</span></div>
    {mobileNavOpen&&<div className="drawer-overlay" onClick={()=>setMobileNavOpen(false)}/>}
    <aside className={`sidebar ${mobileNavOpen?'open':''}`}>
      <div className="brand-lockup"><div className="brand-mark crystal-v"><img src="/blueorch-v-core.png" alt="BlueOrch crystal V"/></div><div><div className="brand-name"><span>BLUE</span>ORCH</div><div className="brand-caption">SOC AUTOMATION</div></div></div>
      <div className="nav-label">OPERATIONS</div>
      <nav className="sidebar-nav">{NAV_ITEMS.map(item=><NavLink key={item.to} to={item.to} end={item.end} onClick={()=>setMobileNavOpen(false)} className={({isActive})=>`nav-item ${isActive?'active':''}`}><Icon name={item.icon}/><span>{item.label}</span><span className="nav-chevron">›</span></NavLink>)}</nav>
      <div className="v-sticker" aria-label="V Security Automation">
        <img src="/v-wings-sticker.png" alt="Blue V with white wings"/>
        <div className="v-sticker-wordmark"><span>BLUE</span>ORCH</div>
      </div>
      <div className="sidebar-status"><div className="status-row"><span className={`status-orb ${healthError?'offline':''}`}/><div><b>{healthLabel}</b><small>{health?health.environment+' environment':'Connecting to core'}</small></div></div><div className="status-meta"><span>SECURITY CORE</span><b>{healthError?'OFFLINE':'ACTIVE'}</b></div></div>
    </aside>
    <main className="workspace"><div className="ambient-grid" aria-hidden="true"/><header className="command-bar"><div><span className="eyebrow">SOC OPERATIONS /</span><strong>{currentTitle}</strong></div><div className="command-actions"><span className="utc-clock">LIVE TELEMETRY</span><span className="live-dot"/><div className="notification-wrap"><button className="notification-button" aria-label={`${pendingApprovals.length} unread notifications`} aria-expanded={notificationsOpen} onClick={()=>setNotificationsOpen(open=>!open)}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></svg>{pendingApprovals.length>0?<b>{Math.min(pendingApprovals.length,99)}</b>:null}</button></div><button className="operator-avatar" title={user?(user.display_name+" · "+user.role+" · click to sign out"):"Local operator"} onClick={()=>user?void logout():setNotificationsOpen(open=>!open)}>{user?.display_name.slice(0,2).toUpperCase()||"VK"}</button></div></header>{notificationsOpen?<aside className="action-center" aria-label="Action Center"><div className="action-center-head"><strong>ACTION CENTER</strong><button aria-label="Close Action Center" onClick={()=>setNotificationsOpen(false)}>×</button></div><div className="action-tabs" role="tablist">{(['approvals','alerts','actions','system'] as const).map(tab=><button role="tab" aria-selected={actionTab===tab} className={actionTab===tab?'active':''} onClick={()=>setActionTab(tab)} key={tab}>{tab.toUpperCase()}</button>)}</div>{actionTab==='approvals'?<ActionApprovals approvals={pendingApprovals} busy={decisionBusy} onDecision={decide} onClose={()=>setNotificationsOpen(false)}/>:null}{actionTab==='alerts'?<ActionMessage title="ALERTS" text="New SIEM alerts will appear here after synchronization." link="/incidents" onClose={()=>setNotificationsOpen(false)}/>:null}{actionTab==='actions'?<ActionMessage title="RESPONSE ACTIONS" text="Approved, executed and failed actions are available in Approval Centre." link="/approvals" onClose={()=>setNotificationsOpen(false)}/>:null}{actionTab==='system'?<ActionMessage title="SYSTEM STATUS" text={healthError?'Backend connection is offline.':'BlueOrch security core is operational.'} link="/health" onClose={()=>setNotificationsOpen(false)}/>:null}</aside>:null}<div className="workspace-content"><Outlet/></div></main>
  </div>
}

function ActionApprovals({approvals,busy,onDecision,onClose}:{approvals:ResponseProposal[];busy:string|null;onDecision:(action:'approve'|'reject',proposal:ResponseProposal)=>Promise<void>;onClose:()=>void}){const proposal=approvals[0];if(!proposal)return <div className="action-empty"><span>✓</span><b>NO APPROVALS PENDING</b><small>New AI recommendations will appear here.</small></div>;return <div className="action-approval"><span>HUMAN APPROVAL REQUIRED</span><div className="action-risk"><b>{proposal.action_type.replaceAll('_',' ').toUpperCase()}</b><em>CRITICAL</em></div><dl><div><dt>Target</dt><dd>{proposal.target}</dd></div><div><dt>Proposed by</dt><dd>{proposal.proposed_by}</dd></div><div><dt>Request</dt><dd>{proposal.id}</dd></div></dl><p>{proposal.justification}</p><Link to={`/incidents/${proposal.incident_id}`} onClick={onClose}>VIEW EVIDENCE</Link><div><button disabled={busy!==null} onClick={()=>void onDecision('reject',proposal)}>{busy==='reject'?'…':'REJECT'}</button><button disabled={busy!==null} onClick={()=>void onDecision('approve',proposal)}>{busy==='approve'?'…':'APPROVE'}</button></div></div>}
function ActionMessage({title,text,link,onClose}:{title:string;text:string;link:string;onClose:()=>void}){return <div className="action-message"><b>{title}</b><p>{text}</p><Link to={link} onClick={onClose}>OPEN MODULE →</Link></div>}
