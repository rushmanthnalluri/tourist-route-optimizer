import React from 'react'
import MapView from './MapView'
import { useApp } from '../context/AppContext'

export default function PageLayout({ children, title, subtitle, accentClass = 'text-primary-600' }) {
  const { routePath, attractions, startId, goalIds, statusMsg, loading, mapPickActive, handleMapPick } = useApp()

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
      
      <header className="shrink-0 bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between gap-3">
        <div>
          <h1 className={`text-lg font-bold leading-none ${accentClass}`}>{title}</h1>
          {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
        </div>
        {(loading || (statusMsg && statusMsg !== 'Ready')) && (
          <p className={`text-xs shrink-0 max-w-xs text-right ${loading ? 'text-primary-600' : 'text-gray-500'}`}>
            {loading ? 'Working…' : statusMsg}
          </p>
        )}
      </header>

      <div className="flex flex-col md:flex-row flex-1 min-h-0 overflow-y-auto md:overflow-hidden">
        
        <div className="flex-none md:flex-[55] min-w-0 relative p-3 h-64 md:h-auto border-b md:border-b-0 border-gray-200 z-0">
          <MapView
            attractions={attractions}
            routePath={routePath}
            startId={startId}
            goalIds={goalIds}
            mapPickActive={mapPickActive}
            onMapPick={handleMapPick}
          />
        </div>

        <div className="hidden md:block w-px bg-gray-200 shrink-0" />

        <div className="flex-1 md:flex-[45] min-w-0 md:overflow-y-auto bg-gray-50 z-0">
          <div className="p-4 md:p-5 space-y-5">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}
