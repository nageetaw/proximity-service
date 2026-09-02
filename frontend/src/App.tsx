import { useEffect, useState } from 'react'
import { useGeolocation } from './hooks/useGeolocation'
import { fetchNearby, type Shop } from './api/nearby'
import { RadiusSelector } from './components/RadiusSelector'
import { ShopList } from './components/ShopList'
import { MapView } from './components/MapView'
import { DEMO_LOCATION, DEMO_LOCATION_LABEL } from './constants'
import './App.css'

function formatRadius(m: number): string {
  return m >= 1000 ? `${m / 1000}km` : `${m}m`
}

type LocationSource = 'gps' | 'demo' | null

export default function App() {
  const { coords, status, error, locate, setCoords } = useGeolocation()
  const [radiusM, setRadiusM] = useState(500)
  const [shops, setShops] = useState<Shop[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const [source, setSource] = useState<LocationSource>(null)

  useEffect(() => {
    if (status === 'success') setSource('gps')
  }, [status])

  function useDemoLocation() {
    setCoords(DEMO_LOCATION)
    setSource('demo')
  }

  function useRealLocation() {
    locate()
  }

  useEffect(() => {
    if (!coords) return
    let cancelled = false
    setLoading(true)
    setFetchError(null)
    fetchNearby(coords.lat, coords.lng, radiusM)
      .then((res) => {
        if (!cancelled) setShops(res.shops)
      })
      .catch((err: Error) => {
        if (!cancelled) setFetchError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [coords, radiusM])

  return (
    <div className="app">
      <header>
        <h1>Shops near you</h1>
        <div className="header-right">
          <RadiusSelector value={radiusM} onChange={setRadiusM} />
          <button type="button" className="link-button" onClick={useDemoLocation}>
            Use demo location
          </button>
        </div>
      </header>

      {status === 'locating' && <p className="status">Getting your location…</p>}

      {(status === 'error' || status === 'unsupported') && !coords && (
        <div className="status error">
          <p>{error}</p>
          <div className="status-actions">
            {status === 'error' && (
              <button type="button" onClick={locate}>
                Try again
              </button>
            )}
            <button type="button" onClick={useDemoLocation}>
              Use demo location instead
            </button>
          </div>
        </div>
      )}

      {source === 'demo' && (
        <div className="status demo-banner">
          <p>Showing demo location — {DEMO_LOCATION_LABEL}</p>
          <button type="button" onClick={useRealLocation}>
            Use my real location
          </button>
        </div>
      )}

      {coords && (
        <main>
          <div className="map-pane">
            <MapView
              center={coords}
              radiusM={radiusM}
              shops={shops}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          </div>
          <div className="list-pane">
            {loading && <p className="status">Loading shops…</p>}
            {fetchError && <p className="status error">{fetchError}</p>}
            {!loading && !fetchError && (
              <>
                <p className="count">
                  {shops.length} shop{shops.length === 1 ? '' : 's'} within {formatRadius(radiusM)}
                </p>
                <ShopList shops={shops} selectedId={selectedId} onSelect={setSelectedId} />
              </>
            )}
          </div>
        </main>
      )}
    </div>
  )
}
