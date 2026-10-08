from car_env import CarEnv, Track

T = Track.load()


def test_track_shape_and_lap_length():
    assert (T.w, T.h, T.length) == (1200, 800, 5095)
    assert T.start == (520, 740, 270) and T.progress_at(520, 740) == 20


def test_trig_tables_are_whole_degrees():
    assert len(T.sin) == len(T.cos) == 360 and T.sin[90] == 1.0 and T.cos[0] == 1.0


def test_every_drivable_pixel_has_progress():
    assert all(p >= 0 for p, m in zip(T.progress, T.mask) if m)


def test_spawns_are_ordered_along_the_lap_and_fit_the_car():
    assert len(T.spawns) == 128 and T.spawns[0] == (500, 739, 270)
    ps = [T.progress_at(x, y) for x, y, _ in T.spawns]
    assert ps == sorted(ps)
    for s in T.spawns:
        assert all(T.drivable(px, py) for px, py in CarEnv(T, s).corners())
