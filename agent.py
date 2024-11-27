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
        return self.q_table.get((state, action), 0.0)

    def choose_action(self, state):
        if random.uniform(0, 1) < self.epsilon:
            return random.choice(self.action_space)
        else:
            q_values = [self.get_q_value(state, action) for action in self.action_space]
            return self.action_space[np.argmax(q_values)]
        
    def update_q_value(self, state, action, reward, next_state):
        current_q = self.get_q_value(state, action)
        next_max_q = max([self.get_q_value(next_state, a) for a in self.action_space])
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * next_max_q - current_q)
        self.q_table[(state, action)] = new_q

class ParallelQLearningAgent:
    def __init__(self, action_space, num_agents, learning_rate=0.1, discount_factor=0.95, epsilon=1.0):
        self.action_space = action_space
        self.num_agents = num_agents
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.q_tables = [{}] * num_agents

    def choose_actions(self, states):
        actions = []
        for state, q_table in zip(states, self.q_tables):
            if random.random() < self.epsilon:
                actions.append(random.choice(self.action_space))
            else:
                if state in q_table:
                    actions.append(max(self.action_space, key=lambda a: q_table[state].get(a, 0)))
                else:
                    actions.append(random.choice(self.action_space))
        return actions
    
    def update_q_values(self, states, actions, rewards, next_states):
        for i, (state, action, reward, next_state) in enumerate(zip(states, actions, rewards, next_states)):
            if state not in self.q_tables[i]:
                self.q_tables[i][state] = {a: 0 for a in self.action_space}
            if next_state not in self.q_tables[i]:
                self.q_tables[i][next_state] = {a: 0 for a in self.action_space}
            
            next_max = max(self.q_tables[i][next_state].values())
            self.q_tables[i][state][action] += self.learning_rate * (
                reward + self.discount_factor * next_max - self.q_tables[i][state][action]
            )

    def clone_best_q_table(self, best_index):
        best_q_table = self.q_tables[best_index]
        self.q_tables = [best_q_table.copy() for _ in range(self.num_agents)]

class CooperativeQLearningAgent:
    def __init__(self, action_space, num_agents, learning_rate=0.1, discount_factor=0.95, epsilon=1.0):
        self.action_space = action_space
        self.num_agents = num_agents
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        # Single shared Q-table for all agents
        self.shared_q_table = {}

    def choose_actions(self, states):
        actions = []
        for state in states:
            if random.random() < self.epsilon:
                actions.append(random.choice(self.action_space))
            else:
                if state in self.shared_q_table:
                    actions.append(max(self.action_space, key=lambda a: self.shared_q_table[state].get(a, 4)))
                else:
                    actions.append(random.choice(self.action_space))
        return actions
    
    def update_q_values(self, states, actions, rewards, next_states):
        for state, action, reward, next_state in zip(states, actions, rewards, next_states):
            if state not in self.shared_q_table:
                self.shared_q_table[state] = {a: 0 for a in self.action_space}
            if next_state not in self.shared_q_table:
                self.shared_q_table[next_state] = {a: 0 for a in self.action_space}
            
            next_max = max(self.shared_q_table[next_state].values())
            self.shared_q_table[state][action] += self.learning_rate * (
                reward + self.discount_factor * next_max - self.shared_q_table[state][action]
            )

    def get_q_table(self):
        """Return the shared Q-table"""
        return self.shared_q_table