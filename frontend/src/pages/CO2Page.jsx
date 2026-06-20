import React, { useState, useMemo } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import PageLayout from '../components/PageLayout'
import TraceViewer from '../components/TraceViewer'
import { useApp } from '../context/AppContext'
import { api } from '../utils/api'
import { Cpu, Route, DollarSign, Clock, GitCompare } from 'lucide-react'

const ALGORITHMS = [
  { id: 'astar',   label: 'A*',       color: 'bg-orange-500' },
  { id: 'bfs',     label: 'BFS',      color: 'bg-blue-500' },
  { id: 'dfs',     label: 'DFS',      color: 'bg-emerald-500' },
  { id: 'ucs',     label: 'UCS',      color: 'bg-purple-500' },
  { id: 'greedy',  label: 'Greedy',   color: 'bg-pink-500' },
  { id: 'idastar', label: 'IDA*',     color: 'bg-teal-500' },
]

const COST_MODES = [
  { id: 'distance', label: 'Distance', icon: Route },
  { id: 'cost',     label: 'Cost',     icon: DollarSign },
  { id: 'time',     label: 'Time',     icon: Clock },
]

const ALG_COLORS = {
  astar: '#f97316', bfs: '#3b82f6', dfs: '#22c55e',
  ucs: '#a855f7', greedy: '#ec4899', idastar: '#14b8a6',
}

const GOAL_LIMITS = { dfs: 24, bfs: 12, ucs: 12, astar: 18, greedy: 24, idastar: 4 }
const COMPARE_GOAL_LIMIT = 8

export default function CO2Page() {
  const { attractions, startId, goalIds, routePath, setRoutePath, setTraceSteps, setLoading, setStatus, loading, routingPayload } = useApp()
  const [algorithm, setAlgorithm] = useState('astar')
  const [costMode, setCostMode]   = useState('distance')
  const [budget, setBudget]       = useState(600)
  const [maxTime, setMaxTime]     = useState(400)
  const [result, setResult]       = useState(null)
  const [profile, setProfile]     = useState(null)

  const bestAlgorithm = useMemo(() => {
    if (!profile) return null;
    const successful = Object.entries(profile).filter(([_, d]) => d.success);
    if (!successful.length) return null;
    
    // Find min distance
    const minDist = Math.min(...successful.map(([_, d]) => d.total_distance_km));
    
    // Filter optimal ones
    const optimal = successful.filter(([_, d]) => Math.abs(d.total_distance_km - minDist) < 0.01);
    
    // Sort by nodes expanded, then by runtime
    optimal.sort((a, b) => {
      if (a[1].nodes_expanded !== b[1].nodes_expanded) {
        return a[1].nodes_expanded - b[1].nodes_expanded;
      }
      return a[1].runtime_ms - b[1].runtime_ms;
    });
    
    return optimal[0];
  }, [profile]);

  async function runSearch() {
    if (startId === null || startId === undefined) { setStatus('⚠ Select Start on the Home page first'); return }
    if (!goalIds.length) { setStatus('⚠ Select at least 1 goal on the Home page'); return }
    const payload = routingPayload({
      budget_inr: budget, max_time_min: maxTime,
      algorithm, cost_mode: costMode,
    })
    if (!payload.goal_ids.length) { setStatus('⚠ Select at least 1 routable goal on the Home page'); return }
    const limit = GOAL_LIMITS[algorithm]
    if (limit && payload.goal_ids.length > limit) {
      setStatus(`⚠ ${algorithm.toUpperCase()} supports max ${limit} goals. Select fewer goals or choose another algorithm.`)
      return
    }
    setLoading(true); setStatus(`Running ${algorithm.toUpperCase()}...`)
    try {
      const data = await api.runSearch(payload)
      setResult(data)
      if (data.success && data.path) {
        setRoutePath(data.path)
        setTraceSteps(data.trace || [])
        setStatus(`✅ ${algorithm.toUpperCase()} — ${data.path.length} stops, ${data.nodes_expanded} expanded`)
      } else {
        setStatus(`❌ No path found — try relaxing budget/time`)
      }
    } catch (e) { setStatus('⚠ Backend error') }
    setLoading(false)
  }

  async function compareAll() {
    if (startId === null || startId === undefined) { setStatus('⚠ Select Start on the Home page first'); return }
    if (!goalIds.length) { setStatus('⚠ Select at least 1 goal on the Home page'); return }
    const payload = routingPayload({
      budget_inr: budget, max_time_min: maxTime,
      algorithm: 'all', cost_mode: costMode,
    })
    if (!payload.goal_ids.length) { setStatus('⚠ Select at least 1 routable goal on the Home page'); return }
    if (payload.goal_ids.length > COMPARE_GOAL_LIMIT) {
      setStatus(`⚠ Compare All is limited to max ${COMPARE_GOAL_LIMIT} goals to prevent server timeout.`)
      return
    }
    setLoading(true); setStatus('Comparing all algorithms...')
    try {
      const data = await api.compareSearch(payload)
      const comparison = data.comparison || {}
      setProfile(comparison)
      const successCount = Object.values(comparison).filter(d => d.success).length
      if (successCount > 0) {
        setStatus(`✅ Comparison done — ${successCount} algorithm${successCount === 1 ? '' : 's'} found a route`)
      } else {
        setStatus('⚠ No algorithm found a route — increase budget/time or remove distant expensive goals')
      }
    } catch (e) { setStatus('⚠ Error') }
    setLoading(false)
  }

  const chartData = profile ? Object.entries(profile).map(([alg, d]) => ({
    alg, expanded: d.nodes_expanded, time: d.runtime_ms,
    dist: d.total_distance_km, success: d.success,
  })) : []

  return (
    <PageLayout
      title="CO2 — Search Algorithms"
      subtitle="BFS · DFS · UCS · A* · Greedy · IDA* — with heuristic design & empirical profiling"
      accentClass="text-blue-700"
    >
      
      <div className="co-banner bg-blue-50 border-blue-200 text-blue-800">
        <strong>Search Algorithms</strong> — BFS ensures completeness, UCS finds min-cost,
        A* (f=g+h) is optimally efficient with an admissible heuristic,
        Greedy (f=h) is fast but not optimal, IDA* is memory-bounded.
        Heuristic: straight-line distance to nearest unvisited goal (admissible + consistent).
      </div>

      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">Algorithm</p>
        <div className="grid grid-cols-6 gap-1.5">
          {ALGORITHMS.map(a => (
            <button key={a.id} onClick={() => setAlgorithm(a.id)}
              className={`py-2 text-xs font-bold rounded-lg transition-all
                ${algorithm === a.id
                  ? `${a.color} text-white shadow-sm`
                  : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}>
              {a.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">Cost Mode</p>
        <div className="flex gap-2">
          {COST_MODES.map(m => (
            <button key={m.id} onClick={() => setCostMode(m.id)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-medium rounded-lg transition-all
                ${costMode === m.id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}>
              <m.icon size={14} />
              {m.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <div className="text-xs font-medium text-gray-500 mb-1 block">Budget (₹)</div>
          <input title="Input field" aria-label="Input field" id="inp-cc3826" type="number" value={budget} onChange={e => setBudget(+e.target.value)}
            className="inp text-sm" />
        </div>
        <div>
          <div className="text-xs font-medium text-gray-500 mb-1 block">Max Time (min)</div>
          <input title="Input field" aria-label="Input field" id="inp-393d39" type="number" value={maxTime} onChange={e => setMaxTime(+e.target.value)}
            className="inp text-sm" />
        </div>
      </div>

      <div className="flex gap-2">
        <button onClick={runSearch} disabled={loading}
          className="btn-primary flex-1">
          <Cpu size={15} /> Run {algorithm.toUpperCase()}
        </button>
        <button onClick={compareAll} disabled={loading}
          className="btn-secondary">
          <GitCompare size={15} /> Compare All
        </button>
      </div>

      {result && (
        <div className={`card p-4 ${result.success ? 'border-emerald-200 bg-emerald-50' : 'border-red-200 bg-red-50'}`}>
          {result.success ? (
            <div className="space-y-2">
              <p className="text-sm font-bold text-emerald-700">✅ Path Found</p>
              <div className="flex flex-wrap gap-1">
                {result.path.map((id, idx) => {
                  const a = attractions.find(x => x.id === id)
                  return (
                    <span key={id}
                      className="text-xs bg-white px-2 py-1 rounded-full border border-gray-200 font-medium text-gray-700">
                      {idx > 0 && <span className="text-gray-300 mr-1">→</span>}
                      {a?.name || `#${id}`}
                    </span>
                  )
                })}
              </div>
              <div className="grid grid-cols-3 gap-2 pt-1">
                {[
                  { label: 'Distance', value: `${result.total_distance_km?.toFixed(2)} km` },
                  { label: 'Cost', value: `₹${result.total_cost?.toFixed(0)}` },
                  { label: 'Time', value: `${result.total_time_min?.toFixed(0)} min` },
                  { label: 'Expanded', value: `${result.nodes_expanded} nodes` },
                  { label: 'Generated', value: `${result.nodes_generated}` },
                  { label: 'Runtime', value: `${result.runtime_ms?.toFixed(1)} ms` },
                ].map(s => (
                  <div key={s.label} className="bg-white rounded-lg px-3 py-2 border border-gray-100 text-center">
                    <p className="text-[10px] text-gray-400 uppercase tracking-wider">{s.label}</p>
                    <p className="text-sm font-bold text-gray-800">{s.value}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-sm text-red-600">
              ❌ {result.failure_reason || 'No path found — try relaxing constraints or selecting different goals'}
            </div>
          )}
        </div>
      )}

      {profile && chartData.length > 0 && (
        <div className="card p-4 space-y-3">
          {!bestAlgorithm && (
            <div className="bg-amber-50 border border-amber-200 text-amber-800 p-3 rounded-lg text-xs">
              <strong className="font-bold">No feasible route found.</strong>
              <p className="mt-0.5">
                Try increasing budget/time or removing distant expensive goals.
              </p>
            </div>
          )}
          {bestAlgorithm && (
            <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3 rounded-lg text-xs flex items-center justify-between">
              <div>
                <strong className="font-bold text-sm">🏆 Best Performer: {bestAlgorithm[0]}</strong>
                <p className="mt-0.5 text-emerald-600">
                  Optimal path found while expanding only <b>{bestAlgorithm[1].nodes_expanded} nodes</b> in <b>{bestAlgorithm[1].runtime_ms?.toFixed(1)} ms</b>.
                </p>
              </div>
            </div>
          )}
          <p className="text-xs font-bold uppercase tracking-wider text-gray-400 mt-2">
            Algorithm Comparison — Nodes Expanded (lower = better)
          </p>
          <ResponsiveContainer width="100%" height={130}>
            <BarChart data={chartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <XAxis dataKey="alg" tick={{ fontSize: 10, fill: '#64748b' }} />
              <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
              <Tooltip
                contentStyle={{ background: '#fff', border: '1px solid #e2e8f0', fontSize: 11, borderRadius: 8 }}
              />
              <Bar dataKey="expanded" radius={[4, 4, 0, 0]}>
                {chartData.map((d, i) => (
                  <Cell key={i} fill={d.success ? (ALG_COLORS[d.alg] || '#64748b') : '#cbd5e1'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-gray-500">
              <thead>
                <tr className="border-b border-gray-100 text-gray-400">
                  <th className="text-left py-1 font-semibold">Algorithm</th>
                  <th className="text-right py-1 font-semibold">Expanded</th>
                  <th className="text-right py-1 font-semibold">Dist (km)</th>
                  <th className="text-right py-1 font-semibold">Runtime (ms)</th>
                  <th className="text-right py-1 font-semibold">Gap %</th>
                  <th className="text-left py-1 pl-3 font-semibold">Reason</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(profile).map(([alg, d]) => (
                  <tr key={alg} className="border-b border-gray-50">
                    <td className="py-1 font-semibold" style={{ color: ALG_COLORS[alg] }}>{alg}</td>
                    <td className="text-right py-1">{d.nodes_expanded}</td>
                    <td className="text-right py-1">{d.success ? d.total_distance_km?.toFixed(2) : '—'}</td>
                    <td className="text-right py-1">{d.runtime_ms?.toFixed(1)}</td>
                    <td className="text-right py-1">{d.success && d.optimality_gap_pct != null ? `${d.optimality_gap_pct}%` : '—'}</td>
                    <td className="py-1 pl-3 text-[11px] text-gray-400">{d.success ? 'Route found' : (d.failure_reason || 'No path within constraints')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {result?.trace && (
        <TraceViewer trace={result.trace} title={`${algorithm.toUpperCase()} Trace`} routePath={routePath} attractions={attractions} />
      )}
    </PageLayout>
  )
}
