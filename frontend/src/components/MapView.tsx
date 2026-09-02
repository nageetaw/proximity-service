import { useEffect } from 'react'
import { Circle, MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'
import L from 'leaflet'
import type { Shop } from '../api/nearby'
import type { Coordinates } from '../hooks/useGeolocation'

// Plain CSS dot markers instead of Leaflet's default image-based icon —
// avoids the classic "marker images don't resolve under a bundler" issue
// and lets us style the selected shop differently.
function dotIcon(className: string) {
  return L.divIcon({
    className: `marker-dot ${className}`,
    iconSize: [16, 16],
  })
}

const userIcon = dotIcon('user')
const shopIcon = dotIcon('shop')
const shopIconSelected = dotIcon('shop selected')

interface Props {
  center: Coordinates
  radiusM: number
  shops: Shop[]
  selectedId: number | null
  onSelect: (id: number) => void
}

function Recenter({ center }: { center: Coordinates }) {
  const map = useMap()
  useEffect(() => {
    map.setView([center.lat, center.lng])
  }, [center.lat, center.lng, map])
  return null
}

export function MapView({ center, radiusM, shops, selectedId, onSelect }: Props) {
  return (
    <MapContainer
      center={[center.lat, center.lng]}
      zoom={15}
      style={{ height: '100%', width: '100%' }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Recenter center={center} />

      <Circle
        center={[center.lat, center.lng]}
        radius={radiusM}
        pathOptions={{ color: '#2563eb', fillOpacity: 0.05 }}
      />

      <Marker position={[center.lat, center.lng]} icon={userIcon}>
        <Popup>You are here</Popup>
      </Marker>

      {shops.map((shop) => (
        <Marker
          key={shop.id}
          position={[shop.lat, shop.lng]}
          icon={shop.id === selectedId ? shopIconSelected : shopIcon}
          eventHandlers={{ click: () => onSelect(shop.id) }}
        >
          <Popup>
            <strong>{shop.name}</strong>
            {shop.category && (
              <>
                <br />
                {shop.category}
              </>
            )}
            <br />
            {Math.round(shop.distance_m)}m away
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}
