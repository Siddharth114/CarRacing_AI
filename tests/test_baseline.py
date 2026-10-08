import json
from baseline_2024 import OLD_TO_NEW, old_state, run
from car_env import CarEnv, Track


def test_old_state_is_heading_bin_plus_eight_coarse_distances():
    s = old_state(CarEnv(Track.load()))
    assert len(s) == 9 and s[0] == 6 and all(0 <= b <= 4 for b in s[1:])


def test_old_actions_map_onto_new_controls():
    assert OLD_TO_NEW == {0: 6, 1: 0, 2: 4, 3: 5, 4: 3}


def test_baseline_smoke(tmp_path):
    run(episodes=3, out=tmp_path)
    m = json.loads((tmp_path / "metrics.json").read_text())
    assert len(m["games"]) == 3 and {"test", "start", "states_seen"} <= m.keys()
