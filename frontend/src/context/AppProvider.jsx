import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { AppContext } from './AppContext'
import { api } from '../utils/api'
import { nearestAttractionId } from '../utils/geo'

const CUSTOM_STORAGE_KEY = 'hydai-custom-places'
const CUSTOM_ID_START = 1000

function loadCustomPlaces() {
  try {
    const raw = localStorage.getItem(CUSTOM_STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function saveCustomPlaces(places) {
  try {
    localStorage.setItem(CUSTOM_STORAGE_KEY, JSON.stringify(places))
  } catch {
    // Storage can fail in private mode or when the quota is exhausted.
  }
}

export function AppProvider({ children }) {
  const [builtinAttractions, setBuiltinAttractions] = useState([])
  const [customPlaces, setCustomPlaces]             = useState(loadCustomPlaces)
  const [graph, setGraph]                           = useState({})
  const [startId, setStartId]                       = useState(null)
  const [goalIds, setGoalIds]                       = useState([])
  const [routePath, setRoutePath]                   = useState([])
  const [traceSteps, setTraceSteps]                 = useState([])
  const [loading, setLoading]                       = useState(false)
  const [statusMsg, setStatusMsg]                   = useState('Ready')
  const [backendOk, setBackendOk]                   = useState(null)
  const [liveEnv, setLiveEnv]                       = useState(null)
  const [mapPickActive, setMapPickActive]           = useState(false)
  const mapPickHandler = useRef(null)

  useEffect(() => {
    let isMounted = true
    Promise.all([api.getAttractions(), api.getGraph()])
      .then(([atts, g]) => {
        if (!isMounted) return
        setBuiltinAttractions(atts)
        setGraph(g)
        setBackendOk(true)
        setStatusMsg('Ready')
      })
      .catch(() => {
        if (!isMounted) return
        setBackendOk(false)
        setStatusMsg('⚠ Backend offline — run: uvicorn main:app --reload --port 8000')
      })
    return () => { isMounted = false }
  }, [])

  const enrichCustom = useCallback(
    (place, builtins) => {
      const snapToId = nearestAttractionId(place.lat, place.lng, builtins)
      const snapName = snapToId != null ? builtins.find(a => a.id === snapToId)?.name : undefined
      return {
        ...place,
        snapToId,
        snapName,
        category: 'custom',
        entry_cost: 0,
        duration_min: 30,
        rating: 0,
        description: place.description || 'Custom destination',
        isCustom: true,
      }
    },
    []
  )

  const attractions = useMemo(() => {
    const enriched = customPlaces.map(p => enrichCustom(p, builtinAttractions))
    return [...builtinAttractions, ...enriched]
  }, [builtinAttractions, customPlaces, enrichCustom])

  // O(1) lookup map — rebuilt only when attractions list changes
  const attractionMap = useMemo(
    () => new Map(attractions.map(a => [a.id, a])),
    [attractions]
  )

  const toggleGoal = useCallback((id) => {
    setGoalIds(g => (g.includes(id) ? g.filter(x => x !== id) : [...g, id]))
  }, [])

  const getAttraction = useCallback(
    (id) => attractionMap.get(id),
    [attractionMap]
  )

  const resolveRoutingId = useCallback(
    (id) => {
      const a = getAttraction(id)
      if (a?.isCustom && a.snapToId != null) return a.snapToId
      return id
    },
    [getAttraction]
  )

  const resolveRoutingIds = useCallback(
    (ids) => [...new Set(ids.map(resolveRoutingId))],
    [resolveRoutingId]
  )

  const routingPayload = useCallback(
    (extra = {}) => ({
      start_id: resolveRoutingId(startId),
      goal_ids: resolveRoutingIds(goalIds),
      ...extra,
    }),
    [startId, goalIds, resolveRoutingId, resolveRoutingIds]
  )

  const addCustomPlace = useCallback(({ name, lat, lng }) => {
    const nextId =
      customPlaces.reduce((max, p) => Math.max(max, p.id), CUSTOM_ID_START - 1) + 1
    const place = { id: nextId, name, lat, lng }
    const next = [...customPlaces, place]
    setCustomPlaces(next)
    saveCustomPlaces(next)
    return nextId
  }, [customPlaces])

  const removeCustomPlace = useCallback((id) => {
    const next = customPlaces.filter(p => p.id !== id)
    setCustomPlaces(next)
    saveCustomPlaces(next)
    if (startId === id) setStartId(null)
    setGoalIds(g => g.filter(x => x !== id))
    setRoutePath(p => p.filter(x => x !== id))
  }, [customPlaces, startId])

  const startMapPick = useCallback((onPick) => {
    mapPickHandler.current = onPick
    setMapPickActive(true)
    setStatusMsg('Click the map to set location')
  }, [])

  const cancelMapPick = useCallback(() => {
    mapPickHandler.current = null
    setMapPickActive(false)
  }, [])

  const handleMapPick = useCallback((lat, lng) => {
    if (mapPickHandler.current) {
      mapPickHandler.current({ lat, lng })
      mapPickHandler.current = null
      setMapPickActive(false)
    }
  }, [])

  const setStartIdSafe = useCallback((id) => {
    setStartId(id);
    setGoalIds(g => g.filter(x => x !== id));
  }, []);

  const contextValue = useMemo(() => ({
    attractions,
    graph,
    startId,
    setStartId: setStartIdSafe,
    goalIds,
    setGoalIds,
    toggleGoal,
    routePath,
    setRoutePath,
    traceSteps,
    setTraceSteps,
    loading,
    setLoading,
    statusMsg,
    setStatusMsg,
    setStatus: setStatusMsg,
    backendOk,
    liveEnv,
    setLiveEnv,
    getAttraction,
    routingPayload,
    resolveRoutingId,
    resolveRoutingIds,
    addCustomPlace,
    removeCustomPlace,
    mapPickActive,
    startMapPick,
    cancelMapPick,
    handleMapPick,
  }), [
    attractions, graph, startId, goalIds, routePath, traceSteps, loading,
    statusMsg, backendOk, liveEnv, mapPickActive,
    getAttraction, routingPayload, resolveRoutingId, resolveRoutingIds,
    toggleGoal, addCustomPlace, removeCustomPlace, startMapPick, cancelMapPick, handleMapPick
  ])

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  )
}
