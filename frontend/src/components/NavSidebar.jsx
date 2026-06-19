import React, { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  Home, Cpu, Calendar, GitMerge, Brain, Zap, MapPin,
  CheckCircle, Circle, AlertCircle, Menu, X
} from 'lucide-react'
import { useApp } from '../context/AppContext'
import { api } from '../utils/api'

const NAV = [
  { to: '/', icon: Home, label: 'Home', sub: 'Overview' },
  { to: '/co1', icon: MapPin, label: 'CO1 — Agent', sub: 'PEAS · Graph' },
  { to: '/co2', icon: Cpu, label: 'CO2 — Search', sub: 'A* · BFS · DFS' },
  { to: '/co3', icon: Calendar, label: 'CO3 — CSP', sub: 'Scheduling' },
  { to: '/co4', icon: GitMerge, label: 'CO4 — Decision', sub: 'Utility · Minimax' },
  { to: '/co5', icon: Brain, label: 'CO5 — Prob.', sub: 'Bayes · HMM' },
  { to: '/co6', icon: Zap, label: 'CO6 — Hybrid', sub: 'Full pipeline' },
]

const CO_COLORS = {
  '/co1': 'text-slate-600',
  '/co2': 'text-blue-600',
  '/co3': 'text-emerald-600',
  '/co4': 'text-amber-600',
  '/co5': 'text-violet-600',
  '/co6': 'text-orange-600',
}

export default function NavSidebar() {
  const { startId, goalIds, routePath, backendOk, statusMsg, getAttraction, setStatus, setLoading, setLiveEnv } = useApp()
  const location = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)

  const startAttr = getAttraction(startId)

  async function handleLiveWeather() {
    setLoading(true); setStatus('Fetching live weather...')
    try {
      const data = await api.getLiveWeather()
      setLiveEnv(prev => ({
        ...prev,
        weather: data.weather,
        prob_rain: data.prob_rain
      }))
      setStatus(`✅ Live weather fetched: ${data.weather} (Rain prob: ${(data.prob_rain * 100).toFixed(0)}%)`)
    } catch (e) {
      setStatus('⚠ Failed to fetch live weather')
    }
    setLoading(false)
  }

  async function handleLiveTraffic() {
    setLoading(true); setStatus('Fetching Live Traffic from OSRM...')
    try {
      const data = await api.fetchLiveTraffic()
      setStatus('✅ ' + data.message)
    } catch (e) {
      setStatus('⚠ Failed to fetch live traffic')
    }
    setLoading(false)
  }

  async function handleLiveCrowds() {
    setLoading(true); setStatus('Simulating Live Crowds...')
    try {
      const data = await api.getLiveCrowds()
      setLiveEnv({
        weather: data.weather,
        time_slot: data.time_slot,
        day_type: data.day_type
      })
      setStatus(`✅ ${data.message}`)
    } catch (e) {
      setStatus('⚠ Failed to fetch live crowds')
    }
    setLoading(false)
  }

  return (
    <>
      {/* Mobile Top Bar */}
      <div className="md:hidden bg-dark-900/80 backdrop-blur-md border-b border-white/5 px-4 py-3 flex items-center justify-between shrink-0 z-20 shadow-md">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center shrink-0 shadow-[0_0_10px_rgba(6,182,212,0.4)]">
            <MapPin size={16} className="text-white" />
          </div>
          <span className="font-bold text-white tracking-wide">HydAI</span>
        </div>
        <button onClick={() => setMobileOpen(!mobileOpen)} className="p-2 text-dark-400 rounded-lg hover:bg-white/5 transition-colors">
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      <aside className={`${mobileOpen ? 'flex absolute inset-0 z-50 bg-dark-900' : 'hidden'} md:flex w-full md:w-72 flex-col bg-dark-900/40 backdrop-blur-xl border-r border-white/5 h-screen shrink-0 overflow-hidden shadow-2xl`}>
        
        {mobileOpen && (
          <div className="md:hidden px-4 py-3 border-b border-white/5 shrink-0 flex justify-between items-center bg-white/5">
            <span className="font-bold text-white tracking-wide">Menu</span>
            <button onClick={() => setMobileOpen(false)} className="p-2 text-dark-400 rounded-lg hover:bg-white/10 transition-colors">
              <X size={20} />
            </button>
          </div>
        )}

        <div className="hidden md:flex px-6 py-5 border-b border-white/5 shrink-0 items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-primary-400 to-primary-600 rounded-xl flex items-center justify-center shrink-0 shadow-[0_0_15px_rgba(34,211,238,0.3)]">
            <MapPin size={20} className="text-white" />
          </div>
          <div>
            <p className="text-lg font-bold text-white tracking-wider leading-none">HydAI</p>
            <p className="text-[11px] font-medium text-primary-400 mt-1 uppercase tracking-widest opacity-80">Route Optimizer</p>
          </div>
        </div>

      <div className="mx-4 mt-4 space-y-2 shrink-0">
        <div
          className={`px-3 py-2 rounded-lg text-xs font-semibold tracking-wide flex items-center gap-2.5 border backdrop-blur-md transition-colors
          ${
            backendOk === true
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
              : backendOk === false
                ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                : 'bg-white/5 text-dark-400 border-white/10 animate-pulse'
          }`}
        >
          {backendOk === true ? (
            <CheckCircle size={14} />
          ) : backendOk === false ? (
            <AlertCircle size={14} />
          ) : (
            <Circle size={14} />
          )}
          <span className="truncate">
            {backendOk === true
              ? 'BACKEND CONNECTED'
              : backendOk === false
                ? 'BACKEND OFFLINE'
                : 'CONNECTING...'}
          </span>
        </div>
        {statusMsg && statusMsg !== 'Ready' && (
          <p className="px-3 py-2 rounded-lg text-xs font-medium bg-white/5 text-dark-400 leading-relaxed border border-white/5 backdrop-blur-sm shadow-inner line-clamp-2">
            {statusMsg}
          </p>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto py-6 mt-2 border-t border-white/5">
        <p className="px-6 pb-3 text-xs font-bold uppercase tracking-widest text-primary-500/70">
          Modules
        </p>
        <div className="flex flex-col gap-1.5 pr-4">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) => isActive ? 'nav-item nav-active' : 'nav-item'}
            >
              <Icon
                size={20}
                className={({ isActive }) => isActive ? 'text-primary-400 drop-shadow-[0_0_8px_rgba(34,211,238,0.8)]' : 'text-dark-400 group-hover:text-white transition-colors'}
              />
              <span className="truncate tracking-wide">{label.replace(' — ', ' ')}</span>
            </NavLink>
          ))}
        </div>
      </nav>

      <div className="border-t border-white/5 p-4 shrink-0 space-y-2.5 bg-dark-900/50">
        <p className="text-[10px] font-bold uppercase tracking-widest text-primary-500/70">
          Live Environment Data
        </p>
        <div className="flex gap-2">
           <button onClick={handleLiveWeather} className="flex-1 bg-white/5 hover:bg-blue-500/20 hover:border-blue-500/30 text-blue-400 text-[10px] py-2 rounded-lg font-bold uppercase tracking-wider transition-all border border-white/5 shadow-sm">⛅ Weather</button>
           <button onClick={handleLiveTraffic} className="flex-1 bg-white/5 hover:bg-emerald-500/20 hover:border-emerald-500/30 text-emerald-400 text-[10px] py-2 rounded-lg font-bold uppercase tracking-wider transition-all border border-white/5 shadow-sm">📡 Traffic</button>
           <button onClick={handleLiveCrowds} className="flex-1 bg-white/5 hover:bg-orange-500/20 hover:border-orange-500/30 text-orange-400 text-[10px] py-2 rounded-lg font-bold uppercase tracking-wider transition-all border border-white/5 shadow-sm">👥 Crowds</button>
        </div>
      </div>
      
      <div className="border-t border-white/5 p-4 shrink-0 space-y-2.5 bg-dark-900/80">
        <p className="text-[10px] font-bold uppercase tracking-widest text-primary-500/70">
          Selection
        </p>
        <div className="bg-white/5 border border-white/5 rounded-xl p-3 space-y-2 text-xs font-medium">
          <div className="flex items-center gap-2">
            <span className="w-5 h-5 bg-gradient-to-br from-orange-400 to-orange-600 shadow-[0_0_8px_rgba(249,115,22,0.4)] rounded-full flex items-center justify-center text-white text-[9px] font-bold shrink-0">
              S
            </span>
            <span className="text-slate-200 truncate drop-shadow-sm">{startAttr?.name || 'Not set'}</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="w-5 h-5 bg-gradient-to-br from-indigo-400 to-primary-600 shadow-[0_0_8px_rgba(99,102,241,0.4)] rounded-full flex items-center justify-center text-white text-[9px] font-bold shrink-0 mt-0.5">
              G
            </span>
            <span className="text-slate-300 leading-tight drop-shadow-sm">
              {goalIds.length
                ? goalIds.map(id => getAttraction(id)?.name).filter(Boolean).join(', ')
                : <span className="text-dark-400">No goals</span>}
            </span>
          </div>
          {routePath.length > 0 && (
            <div className="flex items-center gap-2 text-emerald-400 mt-1 pt-2 border-t border-white/5">
              <CheckCircle size={14} className="drop-shadow-[0_0_5px_rgba(52,211,153,0.5)]" />
              <span className="font-bold tracking-wide">{routePath.length}-STOP ROUTE</span>
            </div>
          )}
        </div>
        </div>
      </aside>
    </>
  )
}
