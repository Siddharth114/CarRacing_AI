import pygame
from ai_game import (
    Car,
    TRACK_BORDER_MASK,
    FINISH_MASK,
    FINISH_POSITION,
    WIN,
    WIDTH,
    HEIGHT,
)
from utils import discretize_state


class CarEnvironment:
    def __init__(self):
        self.player_car = Car(8, 4)
        self.reset()

    def reset(self):
        self.player_car.reset()
        return self.get_state()

    def step(self, action):
        self.take_action(action)
        new_state = self.get_state()
        reward = self.calculate_reward()
        done = self.is_done()
        return new_state, reward, done

    def take_action(self, action):
        if action == 0:  # Left
            self.player_car.rotate(left=True)
        elif action == 1:  # Right
            self.player_car.rotate(right=True)
        elif action == 2:  # Accelerate
            self.player_car.move_forward()
        elif action == 3:  # Brake
            self.player_car.move_backward()
        else:  # Do nothing
            self.player_car.reduce_speed()

    def get_state(self):
        return discretize_state(
            self.player_car.x, self.player_car.y, self.player_car.angle
        )

    def calculate_reward(self):
        reward = 0
        if self.player_car.collide(TRACK_BORDER_MASK) is not None:
            reward -= 10

        finish_collision = self.player_car.collide(FINISH_MASK, *FINISH_POSITION)
        if finish_collision is not None:
            if finish_collision[1] == 0:
                reward -= 5
            else:
                reward += 100

        # Add a small reward for moving forward
        reward += self.player_car.velocity * 0.1

        return reward

    def is_done(self):
        if self.player_car.collide(FINISH_MASK, *FINISH_POSITION) is not None:
            return True
        return False

    def render(self):
        pass