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
        self.player_car = Car(6, 4)
        self.reset()

    def reset(self):
        self.player_car.reset()
        return self.get_state()

    def step(self, action):
        # Perform a step in the environment based on the given action.
        self.take_action(action)
        # Check for collision after movement
        if self.player_car.collide(TRACK_BORDER_MASK) is not None:
            self.player_car.handle_collision()

        new_state = self.get_state()
        reward = self.calculate_reward()
        done = self.is_done()
        return new_state, reward, done


    def take_action(self, action):
        # Apply the given action to the car.
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
        # Get the current state of the environment.
        return discretize_state(
            self.player_car.x, self.player_car.y, self.player_car.angle
        )

    def calculate_reward(self):
        # Calculate the reward for the current state.
        reward = 0
        # Penalize collision with track border
        if self.player_car.collide(TRACK_BORDER_MASK) is not None:
            print('collision')
            reward = -100
            return reward

        # Check finish line collision
        finish_collision = self.player_car.collide(FINISH_MASK, *FINISH_POSITION)
        if finish_collision is not None:
            if finish_collision[1] == 0:
                self.player_car.handle_collision()
                reward -= 5
            else:
                reward += 100

        # Reward for moving forward along the track
        if self.player_car.velocity > 0:
            reward += self.player_car.velocity * 0.5
        else:
            reward -= 1 

        return reward

    def is_done(self):
        # Check if the episode is finished.
        # Episode is done if the car crosses the finish line
        if self.player_car.collide(FINISH_MASK, *FINISH_POSITION) is not None:
            return True
        return False

    def render(self):
        pass