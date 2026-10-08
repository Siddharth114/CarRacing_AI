import base64
import struct
from car_env import Track
from export_web import b64f32, golden_env, golden_track, layers_of, rolling
from train import make_net


def test_b64f32_roundtrips_float32_row_major():
    w = make_net()[0].weight
    vals = struct.unpack(f"<{w.numel()}f", base64.b64decode(b64f32(w)))
    assert list(vals) == w.detach().flatten().tolist()


def test_layers_of_shapes():
    assert [(l["in"], l["out"]) for l in layers_of(make_net().state_dict())] == [(8, 64), (64, 64), (64, 9)]


def test_rolling_mean_downsamples():
    pts = rolling([[i, i % 2] for i in range(1000)], window=20, points=100)
    assert len(pts) <= 100 and pts[-1][0] == 999 and abs(pts[-1][1] - 0.5) < 1e-9


def test_golden_fixtures():
    t = Track.load()
    g = golden_env(t)
    assert len(g["frames"]) == 600 and not g["frames"][-1]["done"]
    gt = golden_track(t)
    assert gt["length"] == 5095 and len(gt["samples"]) == 51
