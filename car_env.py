"""Headless top-down racing env on the 2024 Bahrain circuit — no pygame.

Single source of truth for the rules. The portfolio's lib/car/env.ts mirrors this
file line for line; export_web.py writes golden fixtures that pin the two together.
Heading is whole degrees and trig comes from the tables in track.json, so Python
and JS agree bit for bit. Physics constants match the 2024 game (legacy/ai_game.py);
the car now moves once per step and a crash ends the episode.
"""
import json
import math
from collections import deque
from pathlib import Path
from typing import Callable

MAX_V, ACC, REV_V = 6.0, 0.1, -3.0
STEER_DEG, MIN_STEER_V = 4, 0.1
HALF_LEN, HALF_WID = 15, 6  # car body ~30x12 px (red-car.png at 0.5 scale)
RAYS = (-90, -45, -20, 0, 20, 45, 90)  # degrees relative to heading; positive = left
RAY_STEP, RAY_N = 2, 150
RAY_MAX = RAY_STEP * RAY_N
PROGRESS_SCALE, CRASH_R, LAP_R = 0.01, -1.0, 1.0
STALL_STEPS, MAX_STEPS = 100, 3000
N_ACTIONS = 9  # (steer + 1) * 3 + throttle; steer +1 left / -1 right; throttle 0 coast, 1 gas, 2 brake

TRACK_FILE = Path(__file__).with_name("track.json")


def progress_field(mask: bytearray, w: int, h: int, finish: tuple) -> tuple[list[int], int]:
    """Distance along the road from the finish line, the long way round (4-connected BFS).

    The finish band is blocked during the search so distance can't leak backwards across
    it; afterwards band pixels continue the count from the pixel just left of the band.
    """
    x0, x1, y0, y1 = finish
    prog = [-1] * (w * h)
    q = deque()
    for y in range(y0, y1):
        if mask[y * w + x1]:
            prog[y * w + x1] = 0
            q.append((x1, y))
    while q:
        x, y = q.popleft()
        d = prog[y * w + x] + 1
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not (x0 <= nx < x1 and y0 <= ny < y1):
                j = ny * w + nx
                if mask[j] and prog[j] < 0:
                    prog[j] = d
                    q.append((nx, ny))
    for y in range(y0, y1):
        left = prog[y * w + x0 - 1]
        for x in range(x0, x1):
            if mask[y * w + x]:
                prog[y * w + x] = left + (x - x0 + 1) if left >= 0 else 0
    return prog, max(prog) + 1


class Track:
    def __init__(self, data: dict):
        self.w, self.h = data["w"], data["h"]
        self.start = tuple(data["start"])
        self.sin, self.cos = data["sin"], data["cos"]
        self.spawns = [tuple(s) for s in data.get("spawns", [])]
        f = data["finish"]
        self.finish = (f["x0"], f["x1"], f["y0"], f["y1"])
        self.mask = bytearray(self.w * self.h)
        for y, runs in enumerate(data["rows"]):
            for i in range(0, len(runs), 2):
                start = y * self.w + runs[i]
                self.mask[start:start + runs[i + 1]] = b"\x01" * runs[i + 1]
        self.progress, self.length = progress_field(self.mask, self.w, self.h, self.finish)

    @classmethod
    def load(cls, path: Path = TRACK_FILE) -> "Track":
        return cls(json.loads(path.read_text()))

    def drivable(self, px: float, py: float) -> bool:
        ix, iy = math.floor(px), math.floor(py)
        return 0 <= ix < self.w and 0 <= iy < self.h and self.mask[iy * self.w + ix] == 1

    def progress_at(self, px: float, py: float) -> int:
        return self.progress[math.floor(py) * self.w + math.floor(px)]


class CarEnv:
    def __init__(self, track: Track, spawn: tuple | None = None):
        self.t = track
        self.reset(spawn or track.start)

    def reset(self, spawn: tuple) -> list[float]:
        x, y, a = spawn
        self.x, self.y, self.a, self.v = float(x), float(y), a, 0.0
        self.steps = 0
        self.done = self.lap = self.crashed = False
        self.p = self.t.progress_at(self.x, self.y)
        self.gained = self.best = self.since_best = 0
        return self.observe()

    def step(self, action: int) -> float:
        assert not self.done, "step() after done; call reset()"
        steer, throttle = action // 3 - 1, action % 3
        v = self.v
        if throttle == 1:
            v = min(v + ACC, MAX_V) if v >= 0 else min(v + 2 * ACC, 0.0)
        elif throttle == 2:
            v = max(v - 2 * ACC, 0.0) if v > 0 else max(v - ACC, REV_V)
        else:
            v = max(v - ACC / 2, 0.0) if v > 0 else min(v + ACC / 2, 0.0)
        self.v = v
        if steer and abs(v) >= MIN_STEER_V:
            self.a = (self.a + steer * STEER_DEG * (1 if v > 0 else -1)) % 360
        self.x -= self.t.sin[self.a] * v
        self.y -= self.t.cos[self.a] * v
        self.steps += 1
        if not all(self.t.drivable(px, py) for px, py in self.corners()):
            self.done = self.crashed = True
            return CRASH_R
        p = self.t.progress_at(self.x, self.y)
        d, half = p - self.p, self.t.length // 2
        if d < -half:
            d += self.t.length
        elif d > half:
            d -= self.t.length
        self.p = p
        self.gained += d
        if self.gained > self.best:
            self.best, self.since_best = self.gained, 0
        else:
            self.since_best += 1
        reward = d * PROGRESS_SCALE
        if self.gained >= self.t.length:
            self.done = self.lap = True
            return reward + LAP_R
        if self.since_best >= STALL_STEPS or self.steps >= MAX_STEPS:
            self.done = True
        return reward

    def corners(self) -> list[tuple[float, float]]:
        s, c = self.t.sin[self.a], self.t.cos[self.a]
        fx, fy, rx, ry = -s, -c, c, -s  # forward and right unit vectors
        return [(self.x + fx * HALF_LEN * i + rx * HALF_WID * j, self.y + fy * HALF_LEN * i + ry * HALF_WID * j)
                for i in (1, -1) for j in (1, -1)]

    def rays(self) -> list[int]:
        out = []
        for rel in RAYS:
            a = (self.a + rel) % 360
            dx, dy = -self.t.sin[a], -self.t.cos[a]
            dist = RAY_MAX
            for k in range(1, RAY_N + 1):
                if not self.t.drivable(self.x + dx * RAY_STEP * k, self.y + dy * RAY_STEP * k):
                    dist = RAY_STEP * k
                    break
            out.append(dist)
        return out

    def observe(self) -> list[float]:
        """8 features in [-0.5, 1]: 7 sensor distances / RAY_MAX, then speed / MAX_V."""
        return [d / RAY_MAX for d in self.rays()] + [self.v / MAX_V]

    def fraction(self) -> float:
        return max(0.0, min(self.gained / self.t.length, 1.0))  # backwards counts as 0


def heuristic(env: CarEnv) -> int:
    """Hand-written baseline: steer toward the more open 45-degree sensor; target speed = gap ahead / 20."""
    r = env.rays()
    right45, front, left45 = r[1], r[3], r[5]
    steer = 1 if left45 > right45 + 4 else -1 if right45 > left45 + 4 else 0
    target = min(MAX_V, front / 20)
    throttle = 1 if env.v < target else 2 if env.v > target + 0.5 else 0
    return (steer + 1) * 3 + throttle


def splits(track: Track) -> tuple[list, list, list]:
    """Disjoint start poses: train on odd spawns, validate on 0::4, report on 2::4."""
    s = track.spawns
    return s[1::2], s[0::4], s[2::4]


def run(track: Track, policy: Callable[[CarEnv], int], spawn: tuple) -> CarEnv:
    env = CarEnv(track, spawn)
    while not env.done:
        env.step(policy(env))
    return env


def evaluate(track: Track, policy: Callable[[CarEnv], int], spawns: list) -> list[CarEnv]:
    return [run(track, policy, s) for s in spawns]
