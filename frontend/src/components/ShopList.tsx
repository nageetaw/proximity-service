import type { Shop } from '../api/nearby'

interface Props {
  shops: Shop[]
  selectedId: number | null
  onSelect: (id: number) => void
}

export function ShopList({ shops, selectedId, onSelect }: Props) {
  if (shops.length === 0) {
    return <p className="empty">No shops found in this radius.</p>
  }

  return (
    <ul className="shop-list">
      {shops.map((shop) => (
        <li
          key={shop.id}
          className={shop.id === selectedId ? 'selected' : ''}
          onClick={() => onSelect(shop.id)}
        >
          <div className="shop-name">{shop.name}</div>
          <div className="shop-meta">
            {shop.category && <span className="category">{shop.category}</span>}
            {shop.rating != null && <span className="rating">★ {shop.rating.toFixed(1)}</span>}
            <span className="distance">{Math.round(shop.distance_m)}m away</span>
          </div>
          {shop.address && <div className="shop-address">{shop.address}</div>}
        </li>
      ))}
    </ul>
  )
}
