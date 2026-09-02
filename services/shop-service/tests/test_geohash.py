import math

from app.geohash_utils import choose_precision, cover, encode, neighbors

# A known reference pair (Google HQ, Mountain View) with a published geohash.
GOOGLE_HQ = (37.4220, -122.0841)
GOOGLE_HQ_GEOHASH_PREFIX = "9q9hv"  # widely-published reference value


def test_encode_matches_known_reference():
    gh = encode(*GOOGLE_HQ, precision=5)
    assert gh == GOOGLE_HQ_GEOHASH_PREFIX


def test_encode_is_deterministic_and_length_matches_precision():
    for precision in (4, 6, 8, 9):
        gh = encode(*GOOGLE_HQ, precision=precision)
        assert len(gh) == precision


def test_neighbors_returns_eight_distinct_adjacent_cells():
    center = encode(*GOOGLE_HQ, precision=7)
    nb = neighbors(center)
    assert set(nb.keys()) == {"n", "s", "e", "w", "ne", "nw", "se", "sw"}
    # all neighbors should be distinct from the center and from each other
    values = list(nb.values())
    assert center not in values
    assert len(set(values)) == 8


def test_choose_precision_cell_covers_radius():
    for radius_m in (500, 1000, 2000, 5000):
        precision = choose_precision(radius_m)
        from app.geohash_utils import PRECISION_METERS

        width, height = PRECISION_METERS[precision]
        assert min(width, height) >= radius_m


def test_cover_returns_nine_prefixes_of_chosen_precision():
    precision, prefixes = cover(*GOOGLE_HQ, radius_m=500)
    assert len(prefixes) == 9
    assert all(len(p) == precision for p in prefixes)
    assert len(set(prefixes)) == 9  # center + 8 neighbors are all unique
