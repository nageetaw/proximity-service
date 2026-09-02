import { useCallback, useEffect, useState } from 'react'

export interface Coordinates {
  lat: number
  lng: number
}

export type GeolocationStatus = 'idle' | 'locating' | 'success' | 'error' | 'unsupported'

export function useGeolocation() {
  const [coords, setCoords] = useState<Coordinates | null>(null)
  const [status, setStatus] = useState<GeolocationStatus>('idle')
  const [error, setError] = useState<string | null>(null)

  const locate = useCallback(() => {
    if (!('geolocation' in navigator)) {
      setStatus('unsupported')
      setError('Geolocation is not supported by this browser.')
      return
    }
    setStatus('locating')
    setError(null)
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCoords({ lat: position.coords.latitude, lng: position.coords.longitude })
        setStatus('success')
      },
      (err) => {
        setStatus('error')
        setError(err.message || 'Unable to retrieve your location.')
      },
      { enableHighAccuracy: true, timeout: 10_000, maximumAge: 60_000 },
    )
  }, [])

  useEffect(() => {
    locate()
  }, [locate])

  return { coords, status, error, locate, setCoords }
}
