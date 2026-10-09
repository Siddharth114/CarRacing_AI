# car racing AI: from a Q-table to deep Q-learning

a top-down racing game on a trace of the Bahrain circuit, and an agent that learns to drive it.

**watch it, or race its ghost, in your browser:** https://portfolio-ahl.pages.dev/college/game-ais (the car tab)

## the short version

i built this in 2024 with tabular Q-learning.

in 2026 i dusted it off to put it on my portfolio. i rebuilt the game headless, re-ran the 2024 state, reward, and hyperparameters on it, and from starting points it never trained from, it covered well under 1% of a lap. it never learned to drive. so before it could go on the portfolio, it had to actually work.

(for the re-run, rays march in 4px steps and a crash ends the run. one training run of each, table below.)

![training](training_results/2026-rework.png)

dots are validation scores, and the last one was picked on them. the dashed line is the hand-written rule on held-out starts. see results for the like-for-like comparison.

## results

| | % of a lap (held-out starts) | laps finished | lap from the start line |
|---|---|---|---|
| 2024 recipe (re-run) | 0.40 | 0/32 | no (7.6%) |
| hand-written rule | 93.8 | 30/32 | 17.55 s |
| 2026 rework | 90.6 | 29/32 | 18.05 s |

measured greedily from 32 held-out starting points round the lap, and from the start line. checkpoints were picked on a separate 32.

the hand-written rule steers toward the more open 45° sensor and sets its target speed to the gap ahead ÷ 20. and yes, it's slightly ahead of the agent on every column. turns out distance sensors make this track easy if you already know how to drive. the agent had to work that out from reward alone, so i'm calling it a moral victory.

## why the 2024 version never learned

these are the problems i found reading the code back. i didn't test them one at a time.

- **the state couldn't see the road.** heading plus 8 world-frame distances, each split into five 240px bins, so being a car's length from a wall looked the same as being in the middle of the road. the table had room for millions of states. in 1000 episodes it visited a handful of them (the `states_seen` that `baseline_2024.py` writes).
- **the reward paid for odometry,** not progress round the track, so driving in circles counted.
- **walls weren't walls.** a collision only halved the speed, and the car could scrape along the border.
- **the car moved twice per frame unless it was steering.** `take_action` called `move()` after `move_forward()`, `move_backward()`, or `reduce_speed()`.
- **the parallel trainer's 10 agents all shared one Q-table** (`[{}] * num_agents`), and `legacy/train.py` crashed at the end of a full run (`timestamp` undefined).

## what changed when i dusted it off

- a headless env (`car_env.py`) with the 2024 physics fixed
- a progress field, flood-filled once from the finish line over the track image, so every pixel of road knows how far round the lap it is. the reward is distance gained round the lap, so circles don't pay anymore.
- seven distance sensors that turn with the car, plus speed
- a crash ends the run
- double DQN with a target network, huber loss, gradient clipping, and a 200k replay buffer
- training from starting points all round the lap
- keep the best checkpoint by validation score, not the last one. the score swung hard between checkpoints and several later ones collapsed.

## run it

    uv run pytest                          # tests
    uv run python build_track.py           # rebuild track.json from assets/ (already committed)
    uv run python train.py                 # train (CPU, ~10 min)
    uv run python baseline_2024.py         # re-run the 2024 recipe
    uv run python export_web.py --portfolio ../portfolio   # export to the portfolio
    uv run python human_game.py            # drive it yourself (the 2024 game)

## repo layout

- `car_env.py`: the headless game. source of truth, the browser port mirrors it.
- `build_track.py`: builds `track.json` from the track image.
- `train.py`: the DQN.
- `baseline_2024.py`: the old recipe, re-run on the new game.
- `export_web.py`: exports the agent to the portfolio.
- `human_game.py`: the original 2024 playable game.
- `legacy/`: the original 2024 code, kept for the record.
