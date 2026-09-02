const RADII = [500, 1000, 2000, 5000] as const

function formatRadius(m: number): string {
  return m >= 1000 ? `${m / 1000}km` : `${m}m`
}

interface Props {
  value: number
  onChange: (radius: number) => void
}

export function RadiusSelector({ value, onChange }: Props) {
  return (
    <div className="radius-selector">
      {RADII.map((r) => (
        <button
          key={r}
          type="button"
          className={r === value ? 'active' : ''}
          onClick={() => onChange(r)}
        >
          {formatRadius(r)}
        </button>
      ))}
    </div>
  )
}
