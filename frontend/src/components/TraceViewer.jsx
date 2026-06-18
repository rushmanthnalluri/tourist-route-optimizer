import React, { useState, useRef, useEffect } from 'react'
import { Play, Pause, SkipForward, RotateCcw } from 'lucide-react'

const ACTION_COLORS = {
  INIT:               'text-gray-500',
  EXPAND:             'text-blue-600',
  GENERATE:           'text-cyan-600',
  BACKTRACK:          'text-red-500',
  ASSIGN:             'text-emerald-600',
  CONSTRAINT_FAIL:    'text-orange-500',
  FORWARD_CHECK_FAIL: 'text-orange-500',
  ALPHA_BETA_PRUNE:   'text-amber-600',
  TERMINAL:           'text-violet-600',
  SOLUTION_FOUND:     'text-emerald-600 font-bold',
  NEW_ITERATION:      'text-gray-600',
  AC3_PRUNE:          'text-orange-500',
  AC3_FAIL:           'text-red-500',
  MAX_NODE:           'text-blue-600',
  MIN_NODE:           'text-red-500',
  DEPTH_LIMIT:        'text-gray-400',
}

const ACTION_BG = {
  EXPAND:          'bg-blue-50',
  SOLUTION_FOUND:  'bg-emerald-50',
  BACKTRACK:       'bg-red-50',
  ALPHA_BETA_PRUNE:'bg-amber-50',
  ASSIGN:          'bg-emerald-50',
  CONSTRAINT_FAIL: 'bg-orange-50',
}

export default function TraceViewer({ trace = [], title = 'Algorithm Trace', routePath = [], attractions = [] }) {
  const [playing, setPlaying] = useState(false)
  const [current, setCurrent] = useState(0)
  const [speed, setSpeed]     = useState(300)
  const timerRef  = useRef(null)
  const listRef   = useRef(null)

  useEffect(() => { setCurrent(0); setPlaying(false) }, [trace])

  useEffect(() => {
    if (playing) {
      timerRef.current = setInterval(() => {
        setCurrent(c => {
          if (c >= trace.length - 1) { setPlaying(false); return c }
          return c + 1
        })
      }, speed)
    }
    return () => clearInterval(timerRef.current)
  }, [playing, speed, trace.length])

  useEffect(() => {
    if (listRef.current) {
      const el = listRef.current.children[current]
      el?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  }, [current])

  const MAX_TRACE = 500
  const displayTrace = trace.length > MAX_TRACE ? trace.slice(0, MAX_TRACE) : trace

  if (!trace.length) return (
    <div className="p-4 text-xs text-gray-400 text-center border border-dashed border-gray-200 rounded-lg">
      No trace data available
    </div>
  )

  const step = trace[current] || {}
  const actionKey = step.action || step.step || ''

  return (
    <div className="flex flex-col h-full bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
      <div className="shrink-0 p-3 bg-gray-50 border-b border-gray-200 flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-gray-700 uppercase tracking-wider">{title}</span>
          <span className="text-[10px] text-gray-500 font-mono bg-white px-2 py-0.5 rounded border border-gray-200">
            {current + 1} / {trace.length} steps {trace.length > MAX_TRACE && '(Render limited)'}
          </span>
        </div>
      </div>

      <div className={`m-3 rounded-xl border border-gray-200 p-3 ${ACTION_BG[actionKey] || 'bg-gray-50'}`}>
        <div className="flex items-center justify-between gap-2">
          <span className={`text-sm font-bold ${ACTION_COLORS[actionKey] || 'text-gray-600'}`}>
            {actionKey}
          </span>
          {step.depth != null && (
            <span className="text-xs text-gray-400 bg-white px-1.5 py-0.5 rounded border border-gray-200">
              depth {step.depth}
            </span>
          )}
        </div>
        <div className="mt-1.5 text-xs text-gray-600 space-y-0.5">
          {step.node_name && (
            <div>Node: <span className="font-semibold text-gray-900">{step.node_name}</span></div>
          )}
          {step.g != null && (
            <div className="flex gap-3 font-mono">
              <span>g={step.g}</span>
              <span>h={step.h}</span>
              <span className="text-indigo-600 font-semibold">f={step.f}</span>
            </div>
          )}
          {step.slot && (
            <div>Slot: <span className="font-semibold text-emerald-700">{step.slot}</span></div>
          )}
          {step.reason && (
            <div className="text-orange-600">{step.reason}</div>
          )}
          {step.bound != null && (
            <div>Bound: <span className="font-mono text-indigo-600">{step.bound}</span></div>
          )}
        </div>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-1.5">
        <div
          className="bg-indigo-500 h-1.5 rounded-full transition-all duration-200"
          style={{ width: `${((current + 1) / trace.length) * 100}%` }}
        />
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => { setCurrent(0); setPlaying(false) }}
          className="btn-ghost px-2 py-1.5 text-xs"
          title="Reset"
          aria-label="Reset trace"
        >
          <RotateCcw size={12} />
        </button>
        <button
          onClick={() => setPlaying(p => !p)}
          className="btn-primary py-1.5 px-3 text-xs flex-1"
          title={playing ? 'Pause' : 'Play'}
        >
          {playing ? <><Pause size={12} /> Pause</> : <><Play size={12} /> Play</>}
        </button>
        <button
          onClick={() => setCurrent(c => Math.min(trace.length - 1, c + 1))}
          className="btn-secondary py-1.5 px-3 text-xs"
          title="Step forward"
          aria-label="Step forward"
        >
          <SkipForward size={12} /> Step
        </button>
        <select title="Select dropdown" aria-label="Select dropdown" id="sel-5b6341"
          value={speed}
          onChange={e => setSpeed(+e.target.value)}
          className="inp text-xs py-1.5 w-24"
          title="Playback speed"
          aria-label="Playback speed"
        >
          <option value={700}>Slow</option>
          <option value={300}>Normal</option>
          <option value={100}>Fast</option>
          <option value={30}>Max</option>
        </select>
      </div>

      <div ref={listRef} className="max-h-52 overflow-y-auto rounded-xl border border-gray-200 bg-white divide-y divide-gray-50">
        {displayTrace.map((entry, i) => {
          const ak = entry.action || entry.step || ''
          return (
            <div
              key={i}
              onClick={() => setCurrent(i)}
              className={`trace-row flex items-center gap-2 px-3 py-1.5 cursor-pointer text-xs transition-colors
                ${i === current ? 'bg-indigo-50' : 'hover:bg-gray-50'}`}
            >
              <span className="text-gray-300 w-7 shrink-0 tabular-nums text-right">{i + 1}</span>
              <span className={`font-mono w-28 shrink-0 text-[11px] ${ACTION_COLORS[ak] || 'text-gray-500'}`}>
                {ak}
              </span>
              <span className="text-gray-600 truncate">
                {entry.node_name || entry.name || entry.var || ''}
                {entry.f != null ? ` f=${entry.f}` : ''}
                {entry.slot ? ` → ${entry.slot}` : ''}
                {entry.reason ? ` (${entry.reason})` : ''}
              </span>
            </div>
          )
        })}
      </div>
      
      {/* EXPORT BUTTONS */}
      {routePath && routePath.length > 0 && (
        <div className="flex gap-2 p-3 bg-gray-50 border-t border-gray-200 shrink-0">
          <button
            onClick={() => {
              // Build Google Maps Directions URL
              // Format: https://www.google.com/maps/dir/?api=1&origin=lat,lng&destination=lat,lng&waypoints=lat,lng|lat,lng...
              const waypoints = routePath.map(id => {
                const a = attractions.find(x => x.id === id)
                return a ? `${a.lat},${a.lng}` : null
              }).filter(Boolean)
              
              if (waypoints.length >= 2) {
                const origin = waypoints[0]
                const dest = waypoints[waypoints.length - 1]
                const mids = waypoints.slice(1, -1).join('|')
                let url = `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${dest}`
                if (mids) url += `&waypoints=${mids}`
                window.open(url, '_blank')
              }
            }}
            className="flex-1 btn-primary py-2 text-xs flex items-center justify-center gap-2"
          >
            <svg className="lucide lucide-map" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg>
            Google Maps
          </button>
          <button
            onClick={() => window.print()}
            className="flex-1 btn-secondary py-2 text-xs flex items-center justify-center gap-2"
          >
            <svg className="lucide lucide-printer" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 6 2 18 2 18 9"></polyline><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path><rect x="6" y="14" width="12" height="8"></rect></svg>
            Print PDF
          </button>
        </div>
      )}
    </div>
  )
}
