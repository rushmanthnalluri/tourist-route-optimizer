import React from 'react'
import MapView from './MapView'
import { useApp } from '../context/AppContext'

export default function PageLayout({ children, title, subtitle, accentClass = 'text-primary-400' }) {
  const { routePath, attractions, startId, goalIds, statusMsg, loading, mapPickActive, handleMapPick } = useApp()

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-hidden bg-dark-900 text-slate-100 relative">
      
      {/* Glow orb behind header */}
      <div className="absolute top-0 left-1/4 w-96 h-32 bg-primary-500/20 rounded-full blur-[100px] pointer-events-none -z-10" />

      <header className="shrink-0 bg-dark-900/40 backdrop-blur-md border-b border-white/5 px-6 py-4 flex items-center justify-between gap-3 z-10 shadow-lg">
        <div>
          <h1 className={`text-xl font-bold tracking-tight leading-none ${accentClass} drop-shadow-md`}>{title}</h1>
          {subtitle && <p className="text-sm text-dark-400 mt-1 font-medium">{subtitle}</p>}
        </div>
        {(loading || (statusMsg && statusMsg !== 'Ready')) && (
          <div className={`px-4 py-1.5 rounded-full text-xs font-semibold tracking-wider ${loading ? 'bg-primary-500/10 text-primary-400 animate-pulse border border-primary-500/30' : 'bg-white/5 text-dark-400 border border-white/10'}`}>
            {loading ? 'PROCESSING...' : statusMsg}
          </div>
        )}
      </header>

      <div className="flex flex-col md:flex-row flex-1 min-h-0 overflow-y-auto md:overflow-hidden z-0">
        
        <div className="flex-none md:flex-[55] min-w-0 relative p-4 h-64 md:h-auto border-b md:border-b-0 border-white/5">
          <MapView
            attractions={attractions}
            routePath={routePath}
            startId={startId}
            goalIds={goalIds}
            mapPickActive={mapPickActive}
            onMapPick={handleMapPick}
          />
        </div>

        <div className="hidden md:block w-px bg-white/5 shrink-0" />

        <div className="flex-1 md:flex-[45] min-w-0 md:overflow-y-auto bg-transparent">
          <div className="p-4 md:p-6 space-y-6">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}
