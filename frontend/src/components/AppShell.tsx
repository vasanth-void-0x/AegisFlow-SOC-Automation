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
  useEffect(()=>{const canvas=ref.current;if(!canvas)return;const ctx=canvas.getContext('2d');if(!ctx)return;let frame=0,last=0,drops:number[]=[];const fontSize=22;const resize=()=>{const ratio=Math.min(window.devicePixelRatio||1,2);canvas.width=window.innerWidth*ratio;canvas.height=window.innerHeight*ratio;canvas.style.width=`${window.innerWidth}px`;canvas.style.height=`${window.innerHeight}px`;ctx.setTransform(ratio,0,0,ratio,0,0);drops=Array.from({length:Math.ceil(window.innerWidth/fontSize)},()=>Math.random()*-45)};const glyphs='01◇⋄AEGIS<>[]';const draw=(time:number)=>{if(time-last>110){last=time;ctx.clearRect(0,0,window.innerWidth,window.innerHeight);ctx.font=`500 ${fontSize}px ${getComputedStyle(document.body).fontFamily}`;drops.forEach((drop,i)=>{if(i%2===0){ctx.fillStyle=`rgba(190,244,255,${.2+Math.random()*.28})`;ctx.shadowColor='#8eeeff';ctx.shadowBlur=2;ctx.fillText(glyphs[Math.floor(Math.random()*glyphs.length)],i*fontSize,drop*fontSize)}drops[i]=drop*fontSize>window.innerHeight&&Math.random()>.992?Math.random()*-24:drop+.18})}frame=requestAnimationFrame(draw)};resize();window.addEventListener('resize',resize);frame=requestAnimationFrame(draw);return()=>{cancelAnimationFrame(frame);window.removeEventListener('resize',resize)}},[])
  return <canvas ref={ref} className="aegis-matrix"/>
}

function ProcessorNodes(){
  const paths=['M700 315 L640 282 L580 225 L520 225 L470 180 L410 180','M690 334 L620 334 L565 355 L500 355 L445 326 L330 326','M735 430 L670 430 L615 470 L555 470 L510 510 L410 510','M1100 300 L1190 250 L1270 250 L1330 190 L1445 190','M1110 355 L1210 355 L1280 382 L1340 420 L1400 458 L1490 458','M900 180 L900 130 L860 95 L860 45','M710 290 L650 250 L600 205 L545 205 L500 160 L430 160','M705 370 L630 390 L575 420 L520 420 L470 390 L385 390','M1090 280 L1170 225 L1240 225 L1300 165 L1410 165','M1095 390 L1180 405 L1250 445 L1310 490 L1420 490']
  const endpoints=[[392,111],[305,300],[392,493],[1667,161],[1713,460]]
  const junctions=[[700,315],[640,282],[580,225],[690,334],[565,355],[735,430],[615,470],[1100,300],[1190,250],[1110,355],[1280,382],[1400,458],[900,180],[900,130],[710,290],[705,370],[1090,280],[1095,390]]
  return <svg className="processor-node-layer" viewBox="0 0 1800 675" preserveAspectRatio="xMidYMid meet"><defs><filter id="traceGlow"><feGaussianBlur stdDeviation="4" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter><linearGradient id="traceEnergy"><stop offset="0" stopColor="#086fff" stopOpacity="0"/><stop offset=".42" stopColor="#19bfff"/><stop offset=".68" stopColor="#72e8ff"/><stop offset="1" stopColor="#087cff" stopOpacity="0"/></linearGradient></defs>{paths.map((path,i)=><path key={path} d={path} pathLength="100" className={`data-trace trace-${i+1}`} filter="url(#traceGlow)"/>)}{junctions.map(([cx,cy],i)=><circle key={`j${i}`} cx={cx} cy={cy} r="3.5" className={`circuit-junction pulse-delay-${i%6}`}/>)}{endpoints.map(([cx,cy],i)=><g key={`e${i}`} className={`endpoint-beacon pulse-delay-${i}`}><circle cx={cx} cy={cy} r="12" className="beacon-ring"/><circle cx={cx} cy={cy} r="4" className="beacon-core"/></g>)}</svg>
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
    {location.pathname==='/'&&<div className="aegis-bg-scene" aria-hidden="true"><MatrixRain/><div className="aegis-bg-picture"/><ProcessorNodes/></div>}
    <div className="mobile-bar"><button onClick={()=>setMobileNavOpen(true)} aria-label="Open navigation"><Icon name="grid"/></button><span>AEGISFLOW</span></div>
    {mobileNavOpen&&<div className="drawer-overlay" onClick={()=>setMobileNavOpen(false)}/>}
    <aside className={`sidebar ${mobileNavOpen?'open':''}`}>
      <div className="brand-lockup"><div className="brand-mark crystal-v"><img src="/aegisflow-crystal-v.png" alt="AegisFlow crystal V"/></div><div><div className="brand-name">AEGIS<span>FLOW</span></div><div className="brand-caption">SOC AUTOMATION</div></div></div>
      <div className="nav-label">OPERATIONS</div>
      <nav className="sidebar-nav">{NAV_ITEMS.map(item=><NavLink key={item.to} to={item.to} end={item.end} onClick={()=>setMobileNavOpen(false)} className={({isActive})=>`nav-item ${isActive?'active':''}`}><Icon name={item.icon}/><span>{item.label}</span><span className="nav-chevron">›</span></NavLink>)}</nav>
      <div className="v-sticker" aria-label="V Security Automation">
        <img src="/v-wings-sticker.png" alt="Blue V with white wings"/>
        <div><b>V</b><span>SECURITY AUTOMATION</span></div>
      </div>
      <div className="sidebar-status"><div className="status-row"><span className={`status-orb ${healthError?'offline':''}`}/><div><b>{healthLabel}</b><small>{health?health.environment+' environment':'Connecting to core'}</small></div></div><div className="status-meta"><span>SECURITY CORE</span><b>{healthError?'OFFLINE':'ACTIVE'}</b></div></div>
    </aside>
    <main className="workspace"><div className="ambient-grid" aria-hidden="true"/><header className="command-bar"><div><span className="eyebrow">SOC OPERATIONS /</span><strong>{currentTitle}</strong></div><div className="command-actions"><span className="utc-clock">LIVE TELEMETRY</span><span className="live-dot"/><div className="operator-avatar">VK</div></div></header><div className="workspace-content"><Outlet/></div></main>
  </div>
}
