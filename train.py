"""Double DQN on the headless car env. Writes checkpoints + metrics.json to --out."""
import argparse
import copy
import json
import random
from collections import deque
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

from car_env import N_ACTIONS, CarEnv, Track, evaluate, splits

# Eval + checkpoint every 25k: DQN here peaks and collapses between evals, sparse marks miss the peak.
CHECKPOINT_STEPS = [0, 10_000] + list(range(25_000, 2_000_001, 25_000))
GAMMA, BATCH, BUFFER, WARMUP = 0.99, 64, 200_000, 2000
EPS_END, EPS_STEPS, TARGET_SYNC = 0.05, 150_000, 1000


def make_net() -> nn.Sequential:
    return nn.Sequential(nn.Linear(8, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU(), nn.Linear(64, N_ACTIONS))


def greedy(net):
    def policy(env: CarEnv) -> int:
        with torch.no_grad():
            return int(net(torch.tensor(env.observe())).argmax())  # ties -> lowest index, same as JS
    return policy


def pct(envs: list[CarEnv]) -> float:
    return 100 * sum(e.fraction() for e in envs) / len(envs)


def train(total_steps: int, out: Path, checkpoint_steps=CHECKPOINT_STEPS, seed: int = 0, lr: float = 2.5e-4) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    random.seed(seed)
    torch.manual_seed(seed)
    track = Track.load()
    train_spawns, val_spawns, _ = splits(track)
    net = make_net()
    target = copy.deepcopy(net)
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    buffer = deque(maxlen=BUFFER)
    metrics = {"config": {"gamma": GAMMA, "lr": lr, "target_sync": TARGET_SYNC, "batch": BATCH, "hidden": 64,
                          "eps_steps": EPS_STEPS, "seed": seed},
               "games": [], "evals": [], "best": None}
    games = 0
    env = CarEnv(track, random.choice(train_spawns))
    obs = env.observe()
    marks = {s for s in checkpoint_steps if s <= total_steps} | {total_steps}

    def checkpoint(step: int):
        envs = evaluate(track, greedy(net), val_spawns)
        ev = {"steps": step, "games": games, "mean": pct(envs), "laps": sum(e.lap for e in envs)}
        metrics["evals"].append(ev)
        payload = {"state_dict": copy.deepcopy(net.state_dict()), "steps": step, "games": games,
                   "eval_mean": ev["mean"], "eval_laps": ev["laps"]}
        torch.save(payload, out / f"ckpt-{step:07d}.pt")
        if metrics["best"] is None or ev["mean"] > metrics["best"]["mean"]:
            metrics["best"] = ev
            torch.save(payload, out / "ckpt-best.pt")
        print(f"step {step:>7}  games {games:>5}  val {ev['mean']:.1f}%  laps {ev['laps']}/{len(envs)}", flush=True)

    for step in range(total_steps + 1):
        if step in marks:
            checkpoint(step)
        if step == total_steps:
            break
        eps = max(EPS_END, 1 - step / EPS_STEPS)
        if random.random() < eps:
            action = random.randrange(N_ACTIONS)
        else:
            with torch.no_grad():
                action = int(net(torch.tensor(obs)).argmax())
        reward = env.step(action)
        next_obs = env.observe()
        # Stall/timeout truncation is not terminal; crashes and finished laps are.
        buffer.append((obs, action, reward, next_obs, float(env.crashed or env.lap)))
        obs = next_obs
        if env.done:
            metrics["games"].append([step, round(100 * env.fraction(), 2)])
            games += 1
            obs = env.reset(random.choice(train_spawns))

        if len(buffer) >= WARMUP:
            s, a, r, s2, d = zip(*random.sample(buffer, BATCH))
            s, s2 = torch.tensor(s), torch.tensor(s2)
            a, r, d = torch.tensor(a), torch.tensor(r), torch.tensor(d)
            q = net(s).gather(1, a[:, None]).squeeze(1)
            with torch.no_grad():  # Double DQN: online net picks, target net scores
                best = net(s2).argmax(1, keepdim=True)
                y = r + GAMMA * (1 - d) * target(s2).gather(1, best).squeeze(1)
            loss = F.smooth_l1_loss(q, y)
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(net.parameters(), 10)
            opt.step()
        if step % TARGET_SYNC == 0:
            target.load_state_dict(net.state_dict())

    (out / "metrics.json").write_text(json.dumps(metrics))
    return metrics


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=600_000)
    ap.add_argument("--out", type=Path, default=Path("runs/dqn"))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--lr", type=float, default=2.5e-4)  # planning sweep: 95.2% val vs 83% at 5e-4
    args = ap.parse_args()
    train(args.steps, args.out, seed=args.seed, lr=args.lr)
