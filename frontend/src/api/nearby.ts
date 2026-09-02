export interface Shop {
  id: number
  google_place_id: string | null
  name: string
  category: string | null
  address: string | null
  lat: number
  lng: number
  rating: number | null
  distance_m: number
}

export interface NearbyResponse {
  center: { lat: number; lng: number }
  radius_m: number
  count: number
  shops: Shop[]
}

const LOCATION_SERVICE_URL: string =
  import.meta.env.VITE_LOCATION_SERVICE_URL || 'http://localhost:8000'

export async function fetchNearby(
  lat: number,
  lng: number,
  radiusM: number,
): Promise<NearbyResponse> {
  const url = new URL('/nearby', LOCATION_SERVICE_URL)
  url.searchParams.set('lat', String(lat))
  url.searchParams.set('lng', String(lng))
  url.searchParams.set('radius_m', String(radiusM))

  const res = await fetch(url.toString())
  if (!res.ok) {
    throw new Error(`Nearby search failed (${res.status})`)
  }
  return res.json()
}
