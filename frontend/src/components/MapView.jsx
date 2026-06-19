import React, { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap, useMapEvents } from 'react-leaflet'
import L from 'leaflet'

function displayAttraction(id, attractions, startId, goalIds) {
  const direct = attractions.find(a => a.id === id)
  if (direct && !direct.isCustom) {
    const start = attractions.find(a => a.id === startId)
    if (start?.isCustom && start.snapToId === id) return start
    for (const gid of goalIds) {
      const g = attractions.find(a => a.id === gid)
      if (g?.isCustom && g.snapToId === id) return g
    }
  }
  return direct
}

function MapClickPicker({ active, onPick }) {
  useMapEvents({
    click(e) {
      if (active && onPick) onPick(e.latlng.lat, e.latlng.lng)
    },
  })
  return null
}

import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png'
import iconUrl from 'leaflet/dist/images/marker-icon.png'
import shadowUrl from 'leaflet/dist/images/marker-shadow.png'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl,
  iconUrl,
  shadowUrl,
})

function makeNumberIcon(n, color = '#4f46e5', isStart = false, isGoal = false) {
  const bg = isStart ? '#f97316' : isGoal ? '#4f46e5' : color
  return L.divIcon({
    html: `
      <div style="
        background:${bg};
        color:white;
        border-radius:50%;
        width:32px;height:32px;
        display:flex;align-items:center;justify-content:center;
        font-size:13px;font-weight:700;font-family:Inter,sans-serif;
        border:3px solid white;
        box-shadow:0 2px 8px rgba(0,0,0,0.25);
      ">${n}</div>`,
    className: '',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -18],
  })
}

function makeLabelIcon(text, color = '#4f46e5') {
  return L.divIcon({
    html: `
      <div style="
        background:white;
        color:${color};
        border:2px solid ${color};
        border-radius:8px;
        padding:3px 8px;
        font-size:11px;font-weight:600;font-family:Inter,sans-serif;
        white-space:nowrap;
        box-shadow:0 1px 6px rgba(0,0,0,0.15);
      ">${text}</div>`,
    className: '',
    iconAnchor: [0, -6],
    popupAnchor: [0, -10],
  })
}

function FitBounds({ positions }) {
  const map = useMap()
  useEffect(() => {
    if (positions.length >= 2) {
      try {
        map.fitBounds(L.latLngBounds(positions), { padding: [60, 60], maxZoom: 14 })
      } catch (_) {}
    } else if (positions.length === 1) {
      map.setView(positions[0], 14)
    }
  }, [JSON.stringify(positions)])
  return null
}

export default function MapView({
  attractions,
  routePath = [],
  startId,
  goalIds = [],
  mapPickActive = false,
  onMapPick,
}) {
  const HYD_CENTRE = [17.385, 78.4867]

  const routeAttrs = routePath.length > 0
    ? routePath.map(id => displayAttraction(id, attractions, startId, goalIds)).filter(Boolean)
    : attractions.filter(a => a.id === startId || goalIds.includes(a.id))

  const routeCoords = routeAttrs.map(a => [a.lat, a.lng])
  const hasFullRoute = routePath.length >= 2

  const boundsPositions = routeCoords.length >= 1 ? routeCoords : []
  
  const [roadCoords, setRoadCoords] = useState([])

  useEffect(() => {
    let isMounted = true
    const controller = new AbortController()

    if (hasFullRoute && routeCoords.length >= 2) {
      // OSRM fails if consecutive coordinates are exactly the same
      const dedupedCoords = routeCoords.filter((c, i, arr) => {
        if (i === 0) return true
        return c[0] !== arr[i - 1][0] || c[1] !== arr[i - 1][1]
      })

      if (dedupedCoords.length < 2) {
        setRoadCoords(routeCoords)
        return
      }

      const coordString = dedupedCoords.map(c => `${c[1]},${c[0]}`).join(';')
      const osrmBase = import.meta.env.VITE_OSRM_BASE_URL || 'https://router.project-osrm.org'
      fetch(`${osrmBase}/route/v1/driving/${coordString}?overview=full&geometries=geojson`, {
        signal: controller.signal
      })
        .then(res => {
          if (!res.ok) throw new Error(`OSRM HTTP error: ${res.status}`)
          return res.json()
        })
        .then(data => {
          if (!isMounted) return
          if (data.code === 'Ok' && data.routes && data.routes.length > 0) {
            const roadLine = data.routes[0].geometry.coordinates.map(c => [c[1], c[0]])
            setRoadCoords(roadLine)
          } else {
            console.warn('OSRM returned non-Ok code:', data)
            setRoadCoords(routeCoords)
          }
        })
        .catch(err => {
          if (err.name === 'AbortError') return
          console.error("OSRM Routing Error", err)
          if (isMounted) setRoadCoords(routeCoords)
        })
    } else {
      setRoadCoords([])
    }

    return () => {
      isMounted = false
      controller.abort()
    }
  }, [JSON.stringify(routeCoords), hasFullRoute])

  return (
    <MapContainer
      center={HYD_CENTRE}
      zoom={12}
      style={{ width: '100%', height: '100%', borderRadius: '12px' }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />

      <MapClickPicker active={mapPickActive} onPick={onMapPick} />

      {mapPickActive && (
        <div className="leaflet-top leaflet-center" style={{ width: '100%', pointerEvents: 'none' }}>
          <div
            className="leaflet-control"
            style={{
              margin: '12px auto',
              width: 'fit-content',
              background: '#4f46e5',
              color: 'white',
              padding: '8px 16px',
              borderRadius: 10,
              fontSize: 12,
              fontWeight: 600,
              boxShadow: '0 4px 12px rgba(79,70,229,0.35)',
            }}
          >
            Click the map to set your custom place
          </div>
        </div>
      )}

      {boundsPositions.length >= 1 && <FitBounds positions={boundsPositions} />}

      {hasFullRoute && roadCoords.length >= 2 && (
        <Polyline
          positions={roadCoords}
          color="#4f46e5"
          weight={5}
          opacity={0.9}
          className="animated-path"
        />
      )}

      {routeAttrs.map((a, idx) => {
        const isStart  = a.id === startId
        const isGoal   = goalIds.includes(a.id) && !isStart
        const label    = hasFullRoute ? idx + 1 : (isStart ? 'S' : 'G')
        const icon     = makeNumberIcon(label, '#4f46e5', isStart, isGoal)

        return (
          <Marker key={a.id} position={[a.lat, a.lng]} icon={icon}>
            <Popup>
              <div style={{ fontFamily: 'Inter, sans-serif', minWidth: 160 }}>
                <div style={{ fontWeight: 700, fontSize: 13, color: '#0f172a' }}>
                  {hasFullRoute ? `${idx + 1}. ` : ''}{a.name}
                </div>
                {!a.isCustom && (
                  <div style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>
                    {a.category} · ⭐ {a.rating}
                  </div>
                )}
                {a.isCustom && a.snapName && (
                  <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 4 }}>
                    Routes via {a.snapName}
                  </div>
                )}
                <div style={{ fontSize: 11, color: '#64748b' }}>
                  ₹{a.entry_cost || 'Free'} · {a.duration_min} min
                </div>
                {isStart && <div style={{ fontSize: 11, color: '#f97316', marginTop: 4, fontWeight: 600 }}>📍 Start</div>}
                {isGoal  && <div style={{ fontSize: 11, color: '#4f46e5', marginTop: 4, fontWeight: 600 }}>🎯 Goal</div>}
              </div>
            </Popup>
          </Marker>
        )
      })}

    </MapContainer>
  )
}
