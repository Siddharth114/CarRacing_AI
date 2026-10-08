"""Export trained runs to the portfolio: track, weights, chart data, summary, golden fixtures."""
import argparse
import base64
import json
import shutil
import struct
from pathlib import Path

import torch

from car_env import TRACK_FILE, CarEnv, Track, evaluate, heuristic, splits
from train import greedy, make_net, pct

STEPS_PER_SECOND = 60  # browser sim speed = the 2024 human game's FPS


def b64f32(t: torch.Tensor) -> str:
    vals = t.detach().flatten().tolist()
    return base64.b64encode(struct.pack(f"<{len(vals)}f", *vals)).decode()


def layers_of(state_dict) -> list[dict]:
    out = []
    for i in (0, 2, 4):
        w, b = state_dict[f"{i}.weight"], state_dict[f"{i}.bias"]
        out.append({"in": w.shape[1], "out": w.shape[0], "w": b64f32(w), "b": b64f32(b)})
    return out


def rolling(games: list, window: int = 20, points: int = 200) -> list[list[float]]:
    scores = [s for _, s in games]
    means, acc = [], 0.0
    for i, s in enumerate(scores):
        acc += s
        if i >= window:
            acc -= scores[i - window]
        means.append(acc / min(i + 1, window))
    stride = max(1, -(-len(means) // points))  # ceil
    idx = list(range(len(means) - 1, -1, -stride))[::-1]  # always keep the last point
    return [[i, round(means[i], 3)] for i in idx]


def golden_env(track: Track) -> dict:
    env, frames = CarEnv(track), []
    while not env.done and env.steps < 600:
        action = heuristic(env)
        env.step(action)
        frames.append({"action": action, "x": env.x, "y": env.y, "v": env.v, "a": env.a, "p": env.p,
                       "gained": env.gained, "done": env.done, "crashed": env.crashed, "lap": env.lap,
                       "obs": env.observe()})
    return {"frames": frames}


def golden_track(track: Track) -> dict:
    idx = [i for i, m in enumerate(track.mask) if m][::4099]
    return {"length": track.length, "samples": [[i % track.w, i // track.w, track.progress[i]] for i in idx]}


def golden_policy(track: Track, net, file: str) -> dict:
    env, inputs = CarEnv(track), []
    while not env.done and env.steps < 160:
        if env.steps % 10 == 0:
            inputs.append(env.observe())
        env.step(heuristic(env))
    with torch.no_grad():
        outputs = net(torch.tensor(inputs)).tolist()
    start = evaluate(track, greedy(net), [track.start])[0]
    return {"file": file, "inputs": inputs, "outputs": outputs,
            "rollout": {"pct": 100 * start.fraction(), "lap": start.lap, "steps": start.steps}}


def start_result(env: CarEnv) -> dict:
    return {"pct": round(100 * env.fraction(), 2), "lap": env.lap,
            "seconds": round(env.steps / STEPS_PER_SECOND, 2) if env.lap else None}


def readme_chart(before, ckpts, heuristic_mean, path: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 3.6), dpi=150)
    ax.plot([c["games"] for c in ckpts], [c["evalMean"] for c in ckpts], color="#d97706", marker="o",
            label="2026 rework (greedy, validation starts)")
    ax.plot(*zip(*before), color="#64748b", label="2024 recipe (rolling mean of training episodes)")
    ax.axhline(heuristic_mean, color="#94a3b8", ls="--", lw=1, label="hand-written rule (held-out starts)")
    ax.set_xlabel("episodes")
    ax.set_ylabel("% of a lap")
    ax.set_ylim(0, 100)
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)


def main(portfolio: Path, runs: Path):
    track = Track.load()
    _, _, test_spawns = splits(track)
    dqn = json.loads((runs / "dqn/metrics.json").read_text())
    base = json.loads((runs / "baseline/metrics.json").read_text())
    pub, lib = portfolio / "public/lab/car", portfolio / "lib/car"
    for d in (pub, lib / "fixtures"):
        d.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TRACK_FILE, pub / "track.json")

    # Milestones up to (and including) the best checkpoint; the best one closes the scrubber.
    best = dqn["best"]
    ckpts = []
    for ev in dqn["evals"]:
        if ev["steps"] > best["steps"]:
            break
        ck = torch.load(runs / f"dqn/ckpt-{ev['steps']:07d}.pt")
        name = f"ckpt-{ev['steps']:07d}.json"
        (pub / name).write_text(json.dumps({"steps": ck["steps"], "games": ck["games"], "evalMean": ck["eval_mean"],
                                            "layers": layers_of(ck["state_dict"])}))
        ckpts.append({"file": name, "steps": ck["steps"], "games": ck["games"], "evalMean": ck["eval_mean"]})

    net = make_net()
    net.load_state_dict(torch.load(runs / f"dqn/ckpt-{best['steps']:07d}.pt")["state_dict"])
    after_test, heur_test = evaluate(track, greedy(net), test_spawns), evaluate(track, heuristic, test_spawns)
    heuristic_mean = pct(heur_test)
    before = rolling(base["games"])
    (lib / "lab.json").write_text(json.dumps({"cap": 100, "heuristicMean": heuristic_mean,
                                              "series": {"before": before, "after": rolling(
                                                  [g for g in dqn["games"] if g[0] <= best["steps"]])},
                                              "checkpoints": ckpts}))
    summary = {"cap": 100, "testStarts": len(test_spawns),
               "before": {"mean": base["test"]["mean"], "laps": base["test"]["laps"],
                          "start": {"pct": round(base["start"]["pct"], 2), "lap": base["start"]["lap"], "seconds": None},
                          "statesSeen": base["states_seen"], "games": base["best"]["games"]},
               "after": {"mean": pct(after_test), "laps": sum(e.lap for e in after_test), "games": best["games"],
                         "steps": best["steps"], "start": start_result(evaluate(track, greedy(net), [track.start])[0])},
               "heuristic": {"mean": heuristic_mean, "laps": sum(e.lap for e in heur_test),
                             "start": start_result(evaluate(track, heuristic, [track.start])[0])}}
    (lib / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (lib / "fixtures/golden-env.json").write_text(json.dumps(golden_env(track)))
    (lib / "fixtures/golden-track.json").write_text(json.dumps(golden_track(track)))
    (lib / "fixtures/golden-policy.json").write_text(json.dumps(golden_policy(track, net, ckpts[-1]["file"])))
    readme_chart(before, ckpts, heuristic_mean, Path("training_results/2026-rework.png"))

    f = lambda n: f"{n:.2f}" if n < 1 else f"{n:.1f}"
    lap = lambda s: f"{s['seconds']} s" if s["lap"] else f"no ({f(s['pct'])}%)"
    b, a, h = summary["before"], summary["after"], summary["heuristic"]
    print(f"| | % of a lap (held-out starts) | Laps finished | Laps from the start line |\n|---|---|---|---|")
    print(f"| 2024 recipe (re-run) | {f(b['mean'])} | {b['laps']}/{len(test_spawns)} | {lap(b['start'])} |")
    print(f"| Hand-written rule | {f(h['mean'])} | {h['laps']}/{len(test_spawns)} | {lap(h['start'])} |")
    print(f"| 2026 rework | {f(a['mean'])} | {a['laps']}/{len(test_spawns)} | {lap(a['start'])} |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--portfolio", type=Path, default=Path.home() / "code/portfolio")
    ap.add_argument("--runs", type=Path, default=Path("runs"))
    args = ap.parse_args()
    main(args.portfolio, args.runs)
