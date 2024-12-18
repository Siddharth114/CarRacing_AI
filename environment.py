from ai_game import (
    Car,
    TRACK,
    TRACK_BORDER_MASK,
    FINISH_MASK,
    FINISH_POSITION,
    WIN,
    WIDTH,
    HEIGHT,
    GRASS_MASK
)
from utils import discretize_state
import config
from game_utils import has_completed_track


class CarEnvironment:
    def __init__(self):
        self.player_car = Car(6, 4)
        self.total_reward = 0
        self.reset()

    def reset(self):
        self.total_reward = 0
        self.player_car.reset()
        return self.get_state()

    def step(self, action):
        self.take_action(action)
        if (self.player_car.collide(TRACK_BORDER_MASK) is not None) or (self.player_car.collide(GRASS_MASK) is not None):
            self.player_car.handle_collision()

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
        self.player_car.move()

    def get_state(self):
        distances = self.player_car.get_distances_to_border(TRACK_BORDER_MASK)
        
        angle_discrete = discretize_state(self.player_car.angle, 0, 360, 8)
        distances_discrete = [discretize_state(d, 0, max(TRACK.get_width(), TRACK.get_height()), 5) for d in distances]
        
        state = (angle_discrete, *distances_discrete)
        return state

    def calculate_reward(self):
        reward = 0

        if (self.player_car.collide(TRACK_BORDER_MASK) is not None) or (self.player_car.collide(GRASS_MASK) is not None):
            reward = -10
            self.total_reward += reward
            return reward

        finish_collision = self.player_car.collide(FINISH_MASK, *FINISH_POSITION)
        if finish_collision is not None:
            if has_completed_track(self.player_car.initial_angle, FINISH_POSITION, (self.player_car.x, self.player_car.y)):
                reward += 100
                self.total_reward += reward
                return reward
            else:
                reward = -10
                self.total_reward += reward
                return reward

        distance_reward = self.player_car.distance_this_frame if self.player_car.velocity > 0 else -10*self.player_car.distance_this_frame
        reward += distance_reward

        self.total_reward += reward
        return reward

    def is_done(self):
        if self.player_car.stuck_steps >= config.STUCK_TIMEOUT_STEPS or self.total_reward <= -config.MAX_NEGATIVE_REWARD:
            return True
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

            if (car.collide(TRACK_BORDER_MASK) is not None) or (car.collide(GRASS_MASK) is not None):
                car.handle_collision()

            new_state = self.get_state(car)
            reward = self.calculate_reward(car)
            done = self.is_done(idx)

            self.car_rewards[idx] += reward

            states.append(new_state)
            rewards.append(reward)
            done_states.append(done)

        self.active_cars = [idx for idx, is_done in zip(self.active_cars, done_states) if not is_done]

        population_done = (len(self.active_cars) == 0)

        return states, rewards, done_states, population_done
    
    def get_state(self, car):
        distances = car.get_distances_to_border(TRACK_BORDER_MASK)
        
        angle_discrete = discretize_state(car.angle, 0, 360, 8)
        distances_discrete = [discretize_state(d, 0, max(TRACK.get_width(), TRACK.get_height()), 5) for d in distances]

        return (angle_discrete, *distances_discrete)
    
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
        if (car.collide(TRACK_BORDER_MASK) is not None) or (car.collide(GRASS_MASK) is not None):
            reward = -10
            return reward
        
        finish_collision = car.collide(FINISH_MASK, *FINISH_POSITION)
        if finish_collision is not None:
            if has_completed_track(car.initial_angle, FINISH_POSITION, (car.x, car.y)):
                reward += 100
                return reward
            else:
                reward = -10
                return reward

        distance_reward = car.distance_this_frame if car.velocity > 0 else -10*car.distance_this_frame
        reward += distance_reward

        return reward
    
    def is_done(self, idx):
        if self.cars[idx].stuck_steps >= config.STUCK_TIMEOUT_STEPS or self.car_rewards[idx]<=-config.MAX_NEGATIVE_REWARD:
            return True
        if self.cars[idx].collide(FINISH_MASK, *FINISH_POSITION) is not None:
            return True
        return False

    def get_best_car_index(self):
        return max(range(self.num_cars), key=lambda i: self.car_rewards[i])