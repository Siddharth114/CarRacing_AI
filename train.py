import pygame
from environment import CarEnvironment
from agent import QLearningAgent
import config
import pickle
from utils import draw_action
from ai_game import GRASS, TRACK, TRACK_BORDER, FINISH, FINISH_POSITION

def train():
    pygame.init()
    env = CarEnvironment()
    agent = QLearningAgent(
        action_space=[0, 1, 2, 3, 4],
        learning_rate=config.LEARNING_RATE,
        discount_factor=config.DISCOUNT_FACTOR,
        epsilon=config.EPSILON
    )

    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)

    for episode in range(config.NUM_EPISODES):
        state = env.reset()
        total_reward = 0
        done = False
        step = 0

        while not done:
            action = agent.choose_action(state)
            next_state, reward, done = env.step(action)
            agent.update_q_value(state, action, reward, next_state)
            state = next_state
            total_reward += reward

            # Render the game state
            env.render()
            
            # Draw the background
            env.WIN.blit(GRASS, (0, 0))
            env.WIN.blit(TRACK, (0, 0))
            env.WIN.blit(FINISH, FINISH_POSITION)
            env.WIN.blit(TRACK_BORDER, (0, 0))
            
            # Draw the car
            env.player_car.draw(env.WIN)
            
            # Draw the action visualization
            draw_action(env.WIN, action)
            
            # Draw episode and step information
            episode_text = font.render(f"Episode: {episode + 1}", True, (255, 255, 255))
            step_text = font.render(f"Step: {step}", True, (255, 255, 255))
            reward_text = font.render(f"Total Reward: {total_reward:.2f}", True, (255, 255, 255))
            env.WIN.blit(episode_text, (10, 10))
            env.WIN.blit(step_text, (10, 50))
            env.WIN.blit(reward_text, (10, 90))
            
            pygame.display.update()
            clock.tick(config.FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            step += 1

        print(f"Episode {episode + 1}, Total Reward: {total_reward}")

    # Save the trained Q-table
    with open('models/q_table.pkl', 'wb') as f:
        pickle.dump(agent.q_table, f)

    pygame.quit()

if __name__ == "__main__":
    train()