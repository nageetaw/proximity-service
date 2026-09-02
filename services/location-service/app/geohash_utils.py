"""Pure-Python geohash encode/decode/neighbor helpers.

No third-party geohash package required (avoids C-extension build issues).
Port of the well-known public-domain algorithm (as popularized by Chris
Veness's geohash.js), used identically by shop-service and location-service.
"""
from __future__ import annotations

BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"

# direction -> (odd-length table, even-length table)
_NEIGHBOR = {
    "n": ("p0r21436x8zb9dcf5h7kjnmqesgutwvy", "bc01fg45238967deuvhjyznpkmstqrwx"),
    "s": ("14365h7k9dcfesgujnmqp0r2twvyx8zb", "238967debc01fg45kmstqrwxuvhjyznp"),
    "e": ("bc01fg45238967deuvhjyznpkmstqrwx", "p0r21436x8zb9dcf5h7kjnmqesgutwvy"),
    "w": ("238967debc01fg45kmstqrwxuvhjyznp", "14365h7k9dcfesgujnmqp0r2twvyx8zb"),
}
_BORDER = {
    "n": ("prxz", "bcfguvyz"),
    "s": ("028b", "0145hjnp"),
    "e": ("bcfguvyz", "prxz"),
    "w": ("0145hjnp", "028b"),
}

# Approx cell size in meters at the equator, per geohash string length.
# (width, height) — see https://en.wikipedia.org/wiki/Geohash#Digits_and_precision
PRECISION_METERS = {
    1: (5_009_400, 4_992_600),
    2: (1_252_300, 624_100),
    3: (156_500, 156_000),
    4: (39_100, 19_500),
    5: (4_900, 4_900),
    6: (1_200, 610),
    7: (152.9, 152.4),
    8: (38.2, 19.0),
    9: (4.8, 4.8),
}

MAX_PRECISION = 9


def encode(lat: float, lon: float, precision: int = MAX_PRECISION) -> str:
    """Encode a lat/lon pair into a geohash string of the given length."""
    lat_min, lat_max = -90.0, 90.0
    lon_min, lon_max = -180.0, 180.0
    even_bit = True
    idx = 0
    bit = 0
    geohash = []

    while len(geohash) < precision:
        if even_bit:
            mid = (lon_min + lon_max) / 2
            if lon >= mid:
                idx = idx * 2 + 1
                lon_min = mid
            else:
                idx = idx * 2
                lon_max = mid
        else:
            mid = (lat_min + lat_max) / 2
            if lat >= mid:
                idx = idx * 2 + 1
                lat_min = mid
            else:
                idx = idx * 2
                lat_max = mid
        even_bit = not even_bit
        bit += 1
        if bit == 5:
            geohash.append(BASE32[idx])
            bit = 0
            idx = 0

    return "".join(geohash)


def adjacent(geohash: str, direction: str) -> str:
    """Return the geohash of the cell adjacent to `geohash` in `direction`
    ('n', 's', 'e', or 'w')."""
    geohash = geohash.lower()
    last_ch = geohash[-1]
    parent = geohash[:-1]
    table_idx = len(geohash) % 2  # 0 for even length, 1 for odd length

    if last_ch in _BORDER[direction][table_idx] and parent:
        parent = adjacent(parent, direction)

    return parent + BASE32[_NEIGHBOR[direction][table_idx].index(last_ch)]


def neighbors(geohash: str) -> dict[str, str]:
    """Return the 8 geohashes surrounding `geohash` (n/s/e/w + diagonals)."""
    n = adjacent(geohash, "n")
    s = adjacent(geohash, "s")
    e = adjacent(geohash, "e")
    w = adjacent(geohash, "w")
    return {
        "n": n,
        "s": s,
        "e": e,
        "w": w,
        "ne": adjacent(n, "e"),
        "nw": adjacent(n, "w"),
        "se": adjacent(s, "e"),
        "sw": adjacent(s, "w"),
    }


def choose_precision(radius_m: float) -> int:
    """Pick the largest geohash precision whose cell size (both width and
    height) is still >= radius_m, so a 3x3 block of cells at that precision
    is guaranteed to cover the full search circle. Falls back to precision 1
    for very large radii and MAX_PRECISION for very small ones.
    """
    best = 1
    for precision in sorted(PRECISION_METERS):
        width, height = PRECISION_METERS[precision]
        if min(width, height) >= radius_m:
            best = precision
        else:
            break
    return best


def cover(lat: float, lon: float, radius_m: float) -> tuple[int, list[str]]:
    """Return (precision, [9 geohash prefixes]) covering a circle of
    `radius_m` centered at (lat, lon): the center cell plus its 8 neighbors.
    """
    precision = choose_precision(radius_m)
    center = encode(lat, lon, precision)
    nb = neighbors(center)
    prefixes = [center, *nb.values()]
    return precision, prefixes
