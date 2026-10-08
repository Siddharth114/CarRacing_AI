"""The 2024 recipe — tabular Q-learning with its state and rewards — on the new env.

QLearningAgent and discretize_state come straight from legacy/. Kept on purpose:
heading plus 8 world-frame sensor distances binned into 5 bins across 1200px,
odometry reward (+distance forward, -10x distance in reverse, -10 crash, +100 lap),
lr 0.1, gamma 0.95, epsilon 0.1 decaying x0.995, 1000 episodes from the start line.
The 2024 actions map onto the new controls (steering keeps the throttle off).
"""
import argparse
import json
import math
import random
from pathlib import Path

from car_env import CarEnv, Track, evaluate, splits
from legacy.agent import QLearningAgent
from legacy.utils import discretize_state

OLD_TO_NEW = {0: 6, 1: 0, 2: 4, 3: 5, 4: 3}  # left, right, accelerate, brake, nothing
EPISODES = 1000
OLD_RAY_STEP = 4  # 2024 marched 1px; bins are 240px wide, 4px keeps a 1000-episode run to minutes


def old_state(env: CarEnv) -> tuple:
    dists = []
    for angle in range(0, 360, 45):  # world frame, as in 2024 (x + l*cos, y + l*sin)
        c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        length = 1200
        for l in range(OLD_RAY_STEP, 1200, OLD_RAY_STEP):
            if not env.t.drivable(env.x + l * c, env.y + l * s):
                length = l
                break
        dists.append(length)
    return (discretize_state(env.a, 0, 360, 8), *[discretize_state(d, 0, 1200, 5) for d in dists])


def old_reward(env: CarEnv) -> float:
    if env.crashed:
        return -10.0
    if env.lap:
        return 100.0
    return abs(env.v) if env.v > 0 else -10 * abs(env.v)


def run(episodes: int, out: Path, seed: int = 0) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    random.seed(seed)
    track = Track.load()
    _, val_spawns, test_spawns = splits(track)
    agent = QLearningAgent(action_space=[0, 1, 2, 3, 4], learning_rate=0.1, discount_factor=0.95, epsilon=0.1)
    games = []
    for n in range(episodes):
        env = CarEnv(track)
        s = old_state(env)
        while not env.done:
            a = agent.choose_action(s)
            env.step(OLD_TO_NEW[a])
            s2 = old_state(env)
            agent.update_q_value(s, a, old_reward(env), s2)
            s = s2
        agent.epsilon = max(0.01, agent.epsilon * 0.995)
        games.append([n, round(100 * env.fraction(), 2)])
    agent.epsilon = 0.0

    def policy(env: CarEnv) -> int:
        return OLD_TO_NEW[agent.choose_action(old_state(env))]

    val, test = evaluate(track, policy, val_spawns), evaluate(track, policy, test_spawns)
    start = evaluate(track, policy, [track.start])[0]
    pct = lambda envs: 100 * sum(e.fraction() for e in envs) / len(envs)
    best = {"steps": 0, "games": episodes, "mean": pct(val), "laps": sum(e.lap for e in val)}
    metrics = {"games": games, "evals": [best], "best": best,
               "test": {"mean": pct(test), "laps": sum(e.lap for e in test)},
               "start": {"pct": 100 * start.fraction(), "lap": start.lap, "steps": start.steps},
               "states_seen": len({k[0] for k in agent.q_table})}
    (out / "metrics.json").write_text(json.dumps(metrics))
    return metrics


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=EPISODES)
    ap.add_argument("--out", type=Path, default=Path("runs/baseline"))
    args = ap.parse_args()
    m = run(args.episodes, args.out)
    print(f"2024 recipe: val {m['best']['mean']:.1f}%  test {m['test']['mean']:.1f}%  start {m['start']['pct']:.1f}%")
