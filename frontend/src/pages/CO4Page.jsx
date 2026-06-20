import React, { useState, useEffect } from 'react'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts'
import PageLayout from '../components/PageLayout'
import TraceViewer from '../components/TraceViewer'
import { useApp } from '../context/AppContext'
import { api } from '../utils/api'
import { Scale, Swords, CloudRain, Users } from 'lucide-react'

const CATEGORIES = ['historical', 'nature', 'religious', 'museum', 'entertainment', 'cultural', 'shopping', 'modern']

export default function CO4Page() {
  const { attractions, routePath, setLoading, setStatus, loading, resolveRoutingId, resolveRoutingIds, startId, goalIds, liveEnv } = useApp()
  const [budget, setBudget]         = useState(600)
  const [maxTime, setMaxTime]       = useState(400)
  const [totalCost, setTotalCost]   = useState(200)
  const [totalTime, setTotalTime]   = useState(180)
  const [timeSlot, setTimeSlot]     = useState('afternoon')
  const [prefCats, setPrefCats]     = useState(['historical'])
  const [depthLimit, setDepthLimit] = useState(4)
  const [rainProb, setRainProb]     = useState(0.3)
  const [utilResult, setUtilResult] = useState(null)
  const [minimaxResult, setMinimaxResult] = useState(null)
  const [euResult, setEuResult]     = useState(null)
  const [negResult, setNegResult]   = useState(null)

  useEffect(() => {
    if (liveEnv && liveEnv.prob_rain !== undefined) {
      setRainProb(liveEnv.prob_rain)
    }
  }, [liveEnv])

  function toggleCat(cat) {
    setPrefCats(c => c.includes(cat) ? c.filter(x => x !== cat) : [...c, cat])
  }

  async function runUtility() {
    if (!routePath.length) { setStatus('⚠ Run a search first (CO2)'); return }
    setLoading(true); setStatus('Computing utility...')
    try {
      const data = await api.computeUtility({
        path: resolveRoutingIds(routePath), total_cost: totalCost, total_time_min: totalTime,
        time_slot: timeSlot, preferred_categories: prefCats,
        budget_inr: budget, max_time_min: maxTime,
      })
      setUtilResult(data)
      setStatus(`✅ Utility: ${data.utility?.toFixed(4)}`)
    } catch { setStatus('⚠ Error') }
    setLoading(false)
  }

  async function runMinimax() {
    if (!routePath.length) { setStatus('⚠ Run a search first (CO2)'); return }
    setLoading(true); setStatus('Running Minimax + Alpha-Beta...')
    try {
      const data = await api.runMinimax({
        attractions: resolveRoutingIds(routePath), depth_limit: depthLimit,
        budget_inr: budget, max_time_min: maxTime,
        preferred_categories: prefCats,
      })
      setMinimaxResult(data)
      setStatus(`✅ Minimax: value=${data.minimax_value}, pruned=${data.nodes_pruned}`)
    } catch { setStatus('⚠ Error') }
    setLoading(false)
  }

  async function runEU() {
    if (!routePath.length) { setStatus('⚠ Run a search first (CO2)'); return }
    setLoading(true); setStatus('Computing expected utility...')
    try {
      const data = await api.expectedUtility({
        attraction_ids: resolveRoutingIds(routePath), weather_prob_rain: rainProb,
        preferred_categories: prefCats, budget_inr: budget, max_time_min: maxTime,
      })
      setEuResult(data)
      setStatus('✅ Expected utility computed')
    } catch { setStatus('⚠ Error') }
    setLoading(false)
  }

  async function runNegotiation() {
    if (startId === null || startId === undefined || !goalIds.length) { setStatus('⚠ Select Start and Goals on the Home page first'); return }
    const resolvedGoalIds = resolveRoutingIds(goalIds)
    if (!resolvedGoalIds.length) { setStatus('⚠ Select at least 1 routable goal on the Home page'); return }
    if (resolvedGoalIds.length > 8) { setStatus('⚠ Negotiation is limited to 8 goals max (compare-all limit).'); return }
    setLoading(true); setStatus('Generating candidate routes from CO2 algorithms...')
    try {
      const compareData = await api.compareSearch({
        start_id: resolveRoutingId(startId), goal_ids: resolvedGoalIds,
        budget_inr: budget, max_time_min: maxTime,
        cost_mode: 'distance', avoid_crowds: false
      })
      const candidate_routes = Object.entries(compareData.comparison || {}).map(([alg, res]) => ({
        algorithm: alg,
        path: res.path,
        total_cost: res.total_cost,
        total_time_min: res.total_time_min,
      })).filter(r => r.path && r.path.length > 0)
      
      if (!candidate_routes.length) {
         setStatus('⚠ No valid routes found to negotiate over')
         setLoading(false); return
      }

      setStatus('Negotiating Nash Bargaining Solution...')
      const negData = await api.negotiate({ routes: candidate_routes })
      setNegResult(negData)
      setStatus(`✅ Negotiation complete! Winning route: ${negData.winning_route?.algorithm}`)
    } catch (e) {
      console.error(e)
      setStatus('⚠ Error during negotiation')
    }
    setLoading(false)
  }

  const radarData = utilResult?.components ? [
    { axis: 'Rating', val: +(utilResult.components.rating_score * 100).toFixed(1) },
    { axis: 'Cost Eff', val: +(utilResult.components.cost_efficiency * 100).toFixed(1) },
    { axis: 'Time Eff', val: +(utilResult.components.time_efficiency * 100).toFixed(1) },
    { axis: 'Preference', val: +(utilResult.components.preference_score * 100).toFixed(1) },
    { axis: 'Low Crowd', val: +((1 - utilResult.components.crowd_penalty) * 100).toFixed(1) },
  ] : []

  const hasRoute = routePath.length > 0

  return (
    <PageLayout
      title="CO4 — Decision Theory"
      subtitle="Multi-attribute Utility · Minimax · Alpha-Beta Pruning · Expected Utility · Bounded Rationality"
      accentClass="text-amber-700"
    >
      
      <div className="co-banner bg-amber-50 border-amber-200 text-amber-800">
        <strong>Decision Theory</strong> — Utility function U(route) combines rating,
        cost efficiency, time efficiency, category preference, and crowd penalty.
        Minimax models tourist (MAX) vs. nature (MIN). Alpha-Beta pruning cuts
        irrelevant branches. Expected utility handles weather uncertainty.
      </div>

      <div className="card p-4 space-y-3">
        <p className="text-xs font-bold uppercase tracking-wider text-gray-400">Common Configuration</p>
        <div>
          <p className="text-xs font-medium text-gray-500 mb-1">Preferred Categories</p>
          <div className="flex flex-wrap gap-1">
            {CATEGORIES.map(c => (
              <button key={c} onClick={() => toggleCat(c)}
                className={`text-xs px-2.5 py-1 rounded-lg font-medium transition-all
                  ${prefCats.includes(c)
                    ? 'bg-amber-500 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}>
                {c}
              </button>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="text-xs font-medium text-gray-500 mb-1 block">Budget (₹)</div>
            <input title="Input field" aria-label="Input field" id="inp-d647ac" type="number" value={budget} onChange={e => setBudget(+e.target.value)} className="inp text-sm" />
          </div>
          <div>
            <div className="text-xs font-medium text-gray-500 mb-1 block">Max Time (min)</div>
            <input title="Input field" aria-label="Input field" id="inp-5ccafc" type="number" value={maxTime} onChange={e => setMaxTime(+e.target.value)} className="inp text-sm" />
          </div>
        </div>
        {!hasRoute && (
          <div className="text-xs text-amber-600 bg-amber-50 rounded-lg px-3 py-2">
            ⚠ Run a search algorithm on the CO2 page first to get a route
          </div>
        )}
      </div>

      <div className="card p-4 space-y-3">
        <div className="flex items-center gap-2 text-amber-700">
          <Scale size={16} />
          <span className="text-sm font-bold">1. Utility Function U(route)</span>
        </div>
        <p className="text-xs text-gray-500">
          Route: {hasRoute ? routePath.map(id => attractions.find(a => a.id === id)?.name?.split(' ')[0]).join(' → ') : '—'}
        </p>
        <button onClick={runUtility} disabled={loading || !hasRoute}
          className="btn-primary w-full">
          Compute Utility
        </button>
        {utilResult && (
          <div className="space-y-2">
            <div className="text-center">
              <span className="text-3xl font-bold text-amber-600">{utilResult.utility?.toFixed(4)}</span>
              <span className="text-xs text-gray-400 ml-2">/ ~1.0</span>
            </div>
            {radarData.length > 0 && (
              <ResponsiveContainer width="100%" height={180}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#e2e8f0" />
                  <PolarAngleAxis dataKey="axis" tick={{ fontSize: 10, fill: '#64748b' }} />
                  <Radar dataKey="val" fill="#f59e0b" fillOpacity={0.3} stroke="#f59e0b" strokeWidth={2} />
                </RadarChart>
              </ResponsiveContainer>
            )}
            <div className="grid grid-cols-2 gap-1 text-xs text-gray-500">
              {Object.entries(utilResult.components || {}).map(([k, v]) => (
                <div key={k} className="flex justify-between px-2 py-1 bg-gray-50 rounded-lg">
                  <span>{k.replace(/_/g, ' ')}</span>
                  <span className="text-gray-800 font-semibold">{(+v).toFixed(4)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="card p-4 space-y-3">
        <div className="flex items-center gap-2 text-amber-700">
          <Swords size={16} />
          <span className="text-sm font-bold">2. Minimax + Alpha-Beta Pruning</span>
        </div>
        <p className="text-xs text-gray-500">
          Tourist (MAX) selects best attraction vs. Nature (MIN) that disrupts with crowds/weather.
        </p>
        <div>
          <div className="text-xs font-medium text-gray-500 mb-1 block">Depth Limit: {depthLimit}</div>
          <input title="Input field" aria-label="Input field" id="inp-160b08" type="range" min={2} max={6} value={depthLimit}
            onChange={e => setDepthLimit(+e.target.value)}
            className="w-full accent-amber-500" />
        </div>
        <button onClick={runMinimax} disabled={loading || !hasRoute}
          className="btn-primary w-full">
          Run Minimax
        </button>
        {minimaxResult && (
          <div className="space-y-2 text-xs">
            <div className="bg-amber-50 rounded-lg px-3 py-2 space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-500">Minimax Value</span>
                <span className="font-bold text-amber-700">{minimaxResult.minimax_value}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Best First Choice</span>
                <span className="font-semibold text-gray-800">{minimaxResult.optimal_first_choice}</span>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-1 text-gray-500">
              {[
                { label: 'Evaluated', value: minimaxResult.nodes_evaluated },
                { label: 'Pruned', value: minimaxResult.nodes_pruned },
                { label: 'Prune Ratio', value: `${(minimaxResult.pruning_ratio * 100).toFixed(1)}%` },
                { label: 'Runtime', value: `${minimaxResult.runtime_ms} ms` },
              ].map(s => (
                <div key={s.label} className="flex justify-between px-2 py-1 bg-gray-50 rounded-lg">
                  <span>{s.label}</span>
                  <span className="font-semibold text-gray-700">{s.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="card p-4 space-y-3">
        <div className="flex items-center gap-2 text-amber-700">
          <CloudRain size={16} />
          <span className="text-sm font-bold">3. Expected Utility (Weather Uncertainty)</span>
        </div>
        <p className="text-xs text-gray-500">
          EU = P(sunny) · U(sunny) + P(rain) · U(rain). Uses Bayesian probability from CO5.
        </p>
        <div>
          <div className="text-xs font-medium text-gray-500 mb-1 block">
            Probability of Rain: {(rainProb * 100).toFixed(0)}% | Probability of Sunny: {((1 - rainProb) * 100).toFixed(0)}%
          </div>
          <input title="Input field" aria-label="Input field" id="inp-42348b" type="range" min={0} max={1} step={0.05} value={rainProb}
            onChange={e => setRainProb(+e.target.value)}
            className="w-full accent-amber-500" />
          <div className="flex justify-between text-[10px] text-gray-400">
            <span>Sunny</span><span>Rainy</span>
          </div>
        </div>
        <button onClick={runEU} disabled={loading || !hasRoute}
          className="btn-primary w-full">
          Compute Expected Utility
        </button>
        {euResult && (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-gray-500">
              <thead>
                <tr className="border-b border-gray-100 text-gray-400">
                  <th className="text-left py-1 font-semibold">Attraction</th>
                  <th className="text-right py-1 font-semibold">U(sunny)</th>
                  <th className="text-right py-1 font-semibold">U(rain)</th>
                  <th className="text-right py-1 font-semibold">EU</th>
                  <th className="text-right py-1 font-semibold">OK?</th>
                </tr>
              </thead>
              <tbody>
                {(euResult.results || []).map((r, i) => (
                  <tr key={i} className="border-b border-gray-50">
                    <td className="py-1 truncate max-w-[100px]">{r.name}</td>
                    <td className="text-right py-1">{r.utility_sunny?.toFixed(3)}</td>
                    <td className="text-right py-1">{r.utility_rain?.toFixed(3)}</td>
                    <td className="text-right py-1 font-semibold text-amber-600">{r.expected_utility?.toFixed(3)}</td>
                    <td className="text-right py-1">{r.recommended ? '✅' : '❌'}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="font-bold border-t border-gray-200 text-amber-700 bg-amber-50/50">
                  <td className="py-2 pl-2">Total Expected Utility</td>
                  <td className="text-right py-2"></td>
                  <td className="text-right py-2"></td>
                  <td className="text-right py-2 pr-1 font-semibold">{((euResult.results || []).reduce((acc, r) => acc + (r.expected_utility || 0), 0)).toFixed(3)}</td>
                  <td className="text-right py-2"></td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>

      <div className="card p-4 space-y-3">
        <div className="flex items-center gap-2 text-amber-700">
          <Users size={16} />
          <span className="text-sm font-bold">4. Multi-Agent Negotiation (Family Group)</span>
        </div>
        <p className="text-xs text-gray-500">
          Simulates a group of tourists with conflicting preferences. Calculates the <b>Nash Bargaining Solution</b> across all candidate routes from CO2 search algorithms.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
           <div className="bg-blue-50 border border-blue-100 p-2 rounded-lg text-[10px]">
              <p className="font-bold text-blue-800">🎒 Alice (Backpacker)</p>
              <p className="text-blue-600 mt-0.5">High weight on Cost. Prefers Nature.</p>
           </div>
           <div className="bg-purple-50 border border-purple-100 p-2 rounded-lg text-[10px]">
              <p className="font-bold text-purple-800">📸 Bob (Luxury/History)</p>
              <p className="text-purple-600 mt-0.5">High weight on Ratings & History.</p>
           </div>
           <div className="bg-green-50 border border-green-100 p-2 rounded-lg text-[10px]">
              <p className="font-bold text-green-800">⏱ Charlie (Impatient)</p>
              <p className="text-green-600 mt-0.5">High weight on Fast Travel & Entertainment.</p>
           </div>
        </div>

        <button onClick={runNegotiation} disabled={loading}
          className="btn-primary w-full">
          Generate Routes & Run Negotiation
        </button>

        {negResult && (
           <div className="mt-3 border rounded-xl overflow-hidden overflow-x-auto">
             <table className="w-full text-xs text-gray-600">
               <thead className="bg-gray-50 border-b border-gray-200 text-gray-500">
                 <tr>
                   <th className="py-2 px-3 text-left font-semibold whitespace-nowrap">Candidate Route</th>
                   {negResult.agents.map(a => <th key={a} className="py-2 px-2 text-center font-semibold whitespace-nowrap">{a.split(' ')[0]}</th>)}
                   <th className="py-2 px-3 text-right font-semibold text-indigo-700 whitespace-nowrap">Nash Product</th>
                 </tr>
               </thead>
               <tbody className="divide-y divide-gray-100">
                 {negResult.negotiated_routes.map((r, i) => (
                   <tr key={i} className={i === 0 ? 'bg-indigo-50/50' : ''}>
                     <td className="py-2 px-3 font-medium whitespace-nowrap">
                       {r.algorithm}
                       {i === 0 && <span className="ml-2 text-[10px] bg-indigo-500 text-white px-1.5 py-0.5 rounded">WINNER</span>}
                     </td>
                     {negResult.agents.map(a => (
                       <td key={a} className="py-2 px-2 text-center">
                         {r.scores[a]?.toFixed(2)}
                       </td>
                     ))}
                     <td className="py-2 px-3 text-right font-bold text-indigo-700">
                       {r.nash_product?.toFixed(4)}
                     </td>
                   </tr>
                 ))}
               </tbody>
             </table>
           </div>
        )}
      </div>
    </PageLayout>
  )
}
