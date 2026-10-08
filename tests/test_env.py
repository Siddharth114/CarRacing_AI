import pytest
from car_env import CarEnv, Track, evaluate, heuristic, run, splits

T = Track.load()
GAS, COAST, BRAKE, LEFT_COAST = 4, 3, 5, 6


def drive(env, action, n=None):
    rewards = []
    while not env.done and (n is None or len(rewards) < n):
        rewards.append(env.step(action))
    return rewards


def test_flat_out_from_the_start_hits_the_first_corner():
    env = CarEnv(T)
    drive(env, GAS)
    assert (env.steps, env.gained, env.x, env.v, env.crashed) == (125, 567, 1093.0, 6.0, True)


def test_crash_is_terminal_with_penalty():
    env = CarEnv(T, (520, 740, 0))  # facing the wall
    rewards = drive(env, GAS)
    assert env.steps == 12 and env.crashed and rewards[-1] == -1.0


def test_progress_wraps_across_the_finish_line():
    env = CarEnv(T, (440, 740, 270))
    drive(env, GAS, 100)
    assert env.gained == 444 and not env.done


def test_stall_ends_the_episode_without_a_crash():
    env = CarEnv(T)
    drive(env, COAST)
    assert env.steps == 100 and not env.crashed and not env.lap


def test_no_steering_at_rest_and_reverse_is_capped():
    env = CarEnv(T)
    env.step(LEFT_COAST)
    assert env.a == 270
    drive(env, BRAKE, 40)
    assert env.v == -3.0


def test_observation_is_seven_sensors_and_speed():
    obs = CarEnv(T).observe()
    assert len(obs) == 8 and obs[3] == 1.0 and obs[7] == 0.0


def test_step_after_done_raises():
    env = CarEnv(T)
    drive(env, COAST)
    with pytest.raises(AssertionError):
        env.step(COAST)


def test_splits_are_disjoint():
    train, val, test = splits(T)
    assert (len(train), len(val), len(test)) == (64, 32, 32)
    assert not (set(train) & set(val)) and not (set(val) & set(test)) and not (set(train) & set(test))


def test_heuristic_laps_from_the_start_line():
    env = run(T, heuristic, T.start)
    assert env.lap and env.steps == 1053
    assert sum(e.lap for e in evaluate(T, heuristic, splits(T)[2])) == 30
