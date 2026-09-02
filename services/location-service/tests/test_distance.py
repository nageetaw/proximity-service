from app.distance import haversine_m


def test_zero_distance_for_identical_points():
    assert haversine_m(12.9352, 77.6146, 12.9352, 77.6146) == 0


def test_known_short_distance_is_roughly_correct():
    # ~0.0036 degrees latitude ~= 400m north
    d = haversine_m(12.9352, 77.6146, 12.9352 + 0.0036, 77.6146)
    assert 350 <= d <= 450


def test_symmetry():
    d1 = haversine_m(12.9352, 77.6146, 13.0000, 77.7000)
    d2 = haversine_m(13.0000, 77.7000, 12.9352, 77.6146)
    assert abs(d1 - d2) < 1e-6
