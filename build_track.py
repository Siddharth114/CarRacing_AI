"""Build track.json from the 2024 Bahrain assets. Run once; track.json is committed.

Drivable = opaque pixels of bahrain_track.png. Start pose and finish band come from
the 2024 game (car at 520,740 heading 270; finish sprite at 480,720, 20x44, padded
vertically to span the road). Spawns: the most central road pixel every 40 units of
progress, heading toward the spawn 3 ahead, kept only if the car fits there.
"""
import json
import math
from collections import deque
from pathlib import Path

from PIL import Image

from car_env import TRACK_FILE, CarEnv, Track

ASSETS = Path(__file__).with_name("assets")
START = [520, 740, 270]
FINISH = {"x0": 480, "x1": 500, "y0": 700, "y1": 780}
SPAWN_EVERY = 40


def row_runs(alpha, w: int, y: int) -> list[int]:
    runs, x = [], 0
    while x < w:
        if alpha[x, y] > 127:
            x0 = x
            while x < w and alpha[x, y] > 127:
                x += 1
            runs += [x0, x - x0]
        else:
            x += 1
    return runs


def wall_distance(t: Track) -> list[int]:
    dist = [-1] * (t.w * t.h)
    q = deque()
    for i, m in enumerate(t.mask):
        if not m:
            dist[i] = 0
            q.append(i)
    while q:
        i = q.popleft()
        x, y = i % t.w, i // t.w
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < t.w and 0 <= ny < t.h and dist[ny * t.w + nx] < 0:
                dist[ny * t.w + nx] = dist[i] + 1
                q.append(ny * t.w + nx)
    return dist


def spawns(t: Track) -> list[list[int]]:
    dist = wall_distance(t)
    best: dict[int, tuple[int, int, int]] = {}
    for y in range(t.h):
        for x in range(t.w):
            i = y * t.w + x
            p = t.progress[i]
            if t.mask[i] and p >= 0:
                b = p // SPAWN_EVERY
                if b not in best or dist[i] > best[b][0]:
                    best[b] = (dist[i], x, y)
    pts = [(x, y) for _, (_, x, y) in sorted(best.items())]
    out = []
    for i, (x, y) in enumerate(pts):
        nx, ny = pts[(i + 3) % len(pts)]
        a = round(math.degrees(math.atan2(-(nx - x), -(ny - y)))) % 360
        if all(t.drivable(px, py) for px, py in CarEnv(t, (x, y, a)).corners()):
            out.append([x, y, a])
    return out


def build() -> dict:
    alpha = Image.open(ASSETS / "bahrain_track.png").convert("RGBA").getchannel("A").load()
    w, h = 1200, 800
    data = {"w": w, "h": h, "start": START, "finish": FINISH,
            "sin": [math.sin(math.radians(d)) for d in range(360)],
            "cos": [math.cos(math.radians(d)) for d in range(360)],
            "rows": [row_runs(alpha, w, y) for y in range(h)]}
    data["spawns"] = spawns(Track(data))
    return data


if __name__ == "__main__":
    data = build()
    TRACK_FILE.write_text(json.dumps(data, separators=(",", ":")))
    t = Track(data)
    print(f"track.json: lap length {t.length}, {len(data['spawns'])} spawns, {TRACK_FILE.stat().st_size // 1024} KB")
