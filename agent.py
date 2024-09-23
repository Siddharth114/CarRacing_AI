import numpy as np
import random

class QLearningAgent:
    def __init__(self, action_space, learning_rate=0.1, discount_factor=0.95, epsilon=0.1):
        self.action_space = action_space
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.q_table = {}
        
    def get_q_value(self, state, action):
        # Return the Q-value for the given state-action pair, or 0.0 if not found.
        return self.q_table.get((state, action), 0.0)

    def choose_action(self, state):
        # Choose an action using epsilon-greedy policy.
        if random.uniform(0, 1) < self.epsilon:
            # Exploration
            return random.choice(self.action_space)
        else:
            # Exploitation
            q_values = [self.get_q_value(state, action) for action in self.action_space]
            return self.action_space[np.argmax(q_values)]
        
    def update_q_value(self, state, action, reward, next_state):
        # Update the Q-value for a state-action pair using the Q-learning update rule.
        current_q = self.get_q_value(state, action)
        # Calculate the maximum Q-value for the next state
        next_max_q = max([self.get_q_value(next_state, a) for a in self.action_space])
        # Q-learning update rule
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * next_max_q - current_q)
        self.q_table[(state, action)] = new_q