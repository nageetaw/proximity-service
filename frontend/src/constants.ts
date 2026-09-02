import type { Coordinates } from './hooks/useGeolocation'

// Fallback location for when real browser geolocation is unavailable/denied,
// or you just want to preview the app against the seeded Karachi dataset
// without spoofing GPS. Prince Complex, Clifton — right by Teen Talwar,
// inside the area we seeded with real shops from Google Places.
export const DEMO_LOCATION: Coordinates = {
  lat: 24.8380962,
  lng: 67.0332933,
}

export const DEMO_LOCATION_LABEL = 'Prince Complex, Clifton, Karachi (demo)'
