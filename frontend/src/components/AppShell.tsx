import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useEffect, useRef, useState, type ReactNode } from 'react'
import { api } from '../api/client'
import type { HealthStatus } from '../api/types'

const NAV_ITEMS = [
  { to: '/', label: 'Command Overview', end: true, icon: 'grid' },
  { to: '/incidents', label: 'Incident Queue', icon: 'alert' },
  { to: '/approvals', label: 'Approval Centre', icon: 'check' },
  { to: '/mcp-tools', label: 'MCP Tool History', icon: 'terminal' },
  { to: '/audit', label: 'Audit Log', icon: 'log' },
  { to: '/health', label: 'System Health', icon: 'pulse' },
]
const PAGE_TITLES: Record<string,string> = {'/':'Command Overview','/incidents':'Incident Queue','/approvals':'Approval Centre','/mcp-tools':'MCP Tool History','/audit':'Audit Log','/health':'System Health'}

function Icon({name}:{name:string}) {
  const paths:Record<string,ReactNode> = {
    grid:<><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
    alert:<><path d="M12 3 2.8 19h18.4L12 3Z"/><path d="M12 9v4M12 17h.01"/></>,
    check:<><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/></>,
    terminal:<><rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 9 3 3-3 3M13 15h4"/></>,
    log:<><path d="M5 3h11l3 3v15H5z"/><path d="M16 3v4h4M9 11h6M9 15h6"/></>,
    pulse:<path d="M3 12h4l2-6 4 12 2-6h6"/>,
  }
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>
}

function MatrixRain(){
  const ref=useRef<HTMLCanvasElement>(null)
  useEffect(()=>{const canvas=ref.current;if(!canvas)return;const ctx=canvas.getContext('2d');if(!ctx)return;let frame=0,last=0,drops:number[]=[];const fontSize=17;const resize=()=>{const ratio=Math.min(window.devicePixelRatio||1,2);canvas.width=window.innerWidth*ratio;canvas.height=window.innerHeight*ratio;canvas.style.width=`${window.innerWidth}px`;canvas.style.height=`${window.innerHeight}px`;ctx.setTransform(ratio,0,0,ratio,0,0);drops=Array.from({length:Math.ceil(window.innerWidth/fontSize)},()=>Math.random()*-55)};const glyphs='01AEGISFLOW<>[]{}';const draw=(time:number)=>{if(time-last>90){last=time;ctx.fillStyle='rgba(0,2,5,.11)';ctx.fillRect(0,0,window.innerWidth,window.innerHeight);ctx.font=`500 ${fontSize}px ${getComputedStyle(document.body).fontFamily}`;drops.forEach((drop,i)=>{ctx.fillStyle=`rgba(22,174,255,${.06+Math.random()*.16})`;ctx.shadowColor='#0aaeff';ctx.shadowBlur=3;ctx.fillText(glyphs[Math.floor(Math.random()*glyphs.length)],i*fontSize,drop*fontSize);drops[i]=drop*fontSize>window.innerHeight&&Math.random()>.985?Math.random()*-28:drop+.28})}frame=requestAnimationFrame(draw)};resize();window.addEventListener('resize',resize);frame=requestAnimationFrame(draw);return()=>{cancelAnimationFrame(frame);window.removeEventListener('resize',resize)}},[])
  return <canvas ref={ref} className="aegis-matrix"/>
}

export function AppShell() {
  const [health,setHealth]=useState<HealthStatus|null>(null)
  const [healthError,setHealthError]=useState(false)
  const [mobileNavOpen,setMobileNavOpen]=useState(false)
  const location=useLocation()
  useEffect(()=>{let cancelled=false;const poll=()=>api.health().then(h=>!cancelled&&(setHealth(h),setHealthError(false))).catch(()=>!cancelled&&setHealthError(true));poll();const timer=setInterval(poll,15000);return()=>{cancelled=true;clearInterval(timer)}},[])
  const healthLabel=healthError?'Backend offline':health?.status==='ok'?'All systems operational':'Checking systems'
  const currentTitle=location.pathname.startsWith('/incidents/')?'Incident Investigation':PAGE_TITLES[location.pathname]||'AegisFlow'
  return <div className="app-frame">
    {location.pathname==='/'&&<div className="aegis-bg-scene" aria-hidden="true"><MatrixRain/><div className="aegis-bg-picture"/><div className="aegis-bg-scanline"/></div>}
    <div className="mobile-bar"><button onClick={()=>setMobileNavOpen(true)} aria-label="Open navigation"><Icon name="grid"/></button><span>AEGISFLOW</span></div>
    {mobileNavOpen&&<div className="drawer-overlay" onClick={()=>setMobileNavOpen(false)}/>}
    <aside className={`sidebar ${mobileNavOpen?'open':''}`}>
      <div className="brand-lockup"><div className="brand-mark crystal-v"><img src="/aegisflow-crystal-v.png" alt="AegisFlow crystal V"/></div><div><div className="brand-name">AEGIS<span>FLOW</span></div><div className="brand-caption">SOC AUTOMATION</div></div></div>
      <div className="nav-label">OPERATIONS</div>
      <nav className="sidebar-nav">{NAV_ITEMS.map(item=><NavLink key={item.to} to={item.to} end={item.end} onClick={()=>setMobileNavOpen(false)} className={({isActive})=>`nav-item ${isActive?'active':''}`}><Icon name={item.icon}/><span>{item.label}</span><span className="nav-chevron">›</span></NavLink>)}</nav>
      <div className="sidebar-automation"><div className="automation-orb"><span/></div><div><b>AUTOMATION ACTIVE</b><small>6-stage response workflow</small></div><em>LIVE</em></div>
      <div className="sidebar-status"><div className="status-row"><span className={`status-orb ${healthError?'offline':''}`}/><div><b>{healthLabel}</b><small>{health?health.environment+' environment':'Connecting to core'}</small></div></div><div className="status-meta"><span>SECURITY CORE</span><b>{healthError?'OFFLINE':'ACTIVE'}</b></div></div>
    </aside>
    <main className="workspace"><div className="ambient-grid" aria-hidden="true"/><header className="command-bar"><div><span className="eyebrow">SOC OPERATIONS /</span><strong>{currentTitle}</strong></div><div className="command-actions"><span className="utc-clock">LIVE TELEMETRY</span><span className="live-dot"/><div className="operator-avatar">VK</div></div></header><div className="workspace-content"><Outlet/></div></main>
  </div>
}