import pygame
from ai_game import (
    Car,
    TRACK,
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
        self.player_car.move()

    def get_state(self):
        # Get distances to track borders
        distances = self.player_car.get_distances_to_border(TRACK_BORDER_MASK)
        
        # Discretize the car's position, angle, and distances
        x_discrete = discretize_state(self.player_car.x, 0, TRACK.get_width(), 10)
        y_discrete = discretize_state(self.player_car.y, 0, TRACK.get_height(), 10)
        angle_discrete = discretize_state(self.player_car.angle, 0, 360, 8)
        distances_discrete = [discretize_state(d, 0, max(TRACK.get_width(), TRACK.get_height()), 5) for d in distances]
        
        # Combine all state information
        state = (x_discrete, y_discrete, angle_discrete, *distances_discrete)
        return state

    def calculate_reward(self):
        # Calculate the reward for the current state.
        reward = 0
        # Penalize collision with track border
        if self.player_car.collide(TRACK_BORDER_MASK) is not None:
            reward = -5
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
    

class ParallelLearningCarEnvironment:
    def __init__(self, num_cars=10):
        self.num_cars = num_cars
        self.cars = [Car(6,4) for _ in range(self.num_cars)]
        self.active_cars = list(range(self.num_cars))
        self.car_rewards = [0 for _ in range(self.num_cars)]
        self.reset()

    def reset(self):
        self.active_cars = list(range(self.num_cars))
        self.car_rewards = [0 for _ in range(self.num_cars)]
        for car in self.cars:
            car.reset()
        return [self.get_state(car) for car in self.cars]
    
    def step(self, actions):
        states, rewards, done_states = [], [], []

        for idx, action in zip(self.active_cars, actions):
            car = self.cars[idx]
            self.take_action(car, action)

            if car.collide(TRACK_BORDER_MASK) is not None:
                car.handle_collision()

            new_state = self.get_state(car)
            reward = self.get_reward(car)
            done = self.is_done(car)

            self.car_rewards[idx] += reward

            states.append(new_state)
            rewards.append(reward)
            done_states.append(done)

        self.active_cars = [idx for idx, is_done in zip(self.active_cars, done_states) if not is_done]

        population_done = (len(self.active_cars) == 0)

        return states, rewards, done_states, population_done
    
    def get_state(self, car):
        distances = car.get_distances_to_border(TRACK_BORDER_MASK)
        
        x_discrete = discretize_state(car.x, 0, TRACK.get_width(), 10)
        y_discrete = discretize_state(car.y, 0, TRACK.get_height(), 10)
        
        angle_discrete = discretize_state(car.angle, 0, 360, 8)
        distances_discrete = [discretize_state(d, 0, max(TRACK.get_width(), TRACK.get_height()), 5) for d in distances]

        return (x_discrete, y_discrete, angle_discrete, *distances_discrete)
    
    def take_action(self, car, action):
        if action == 0:  # Left
            car.rotate(left=True)
        elif action == 1:  # Right
            car.rotate(right=True)
        elif action == 2:  # Accelerate
            car.move_forward()
        elif action == 3:  # Brake
            car.move_backward()
        else:  # Do nothing
            car.reduce_speed()
        car.move()

    def calculate_reward(self, car):
        reward = 0
        if car.collide(TRACK_BORDER_MASK) is not None:
            reward = -5
            return reward
        finish_collision = car.collide(FINISH_MASK, *FINISH_POSITION)
        if finish_collision is not None:
            if finish_collision[1] == 0:
                car.handle_collision()
                reward -= 5
            else:
                reward += 100
        if car.velocity > 0:
            reward += car.velocity * 0.5
        else:
            reward -= 1 
        return reward
    
    def is_done(self, car):
        if car.collide(FINISH_MASK, *FINISH_POSITION) is not None:
            return True
        return False

    def get_best_car_index(self):
        return max(range(self.num_cars), key=lambda i: self.car_rewards[i])