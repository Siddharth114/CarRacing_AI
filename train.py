import pygame
import math
import os
import matplotlib.pyplot as plt
from datetime import datetime
from environment import CarEnvironment
from agent import QLearningAgent
import config
import pickle
from utils import draw_actions
from ai_game import GRASS, TRACK, TRACK_BORDER, TRACK_BORDER_MASK, FINISH, FINISH_POSITION, WIDTH, HEIGHT

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
    font = pygame.font.Font(None, 24)
    # Create a larger surface to accommodate the game and info panel
    main_surface = pygame.display.set_mode((WIDTH + 200, HEIGHT))
    pygame.display.set_caption("RL Car Racing Game")
    if not os.path.exists('models'):
        os.makedirs('models')
    if not os.path.exists('training_runs'):
        os.makedirs('training_runs')

    rewards = []

    for episode in range(config.NUM_EPISODES):
        state = env.reset()
        total_reward = 0
        done = False
        step = 0
        last_position = None
        stuck_steps = 0

        while not done:
            action = agent.choose_action(state)
            next_state, reward, done = env.step(action)
            agent.update_q_value(state, action, reward, next_state)
            state = next_state
            total_reward += reward

            # Check if the car is stuck
            current_position = (env.player_car.x, env.player_car.y)
            if current_position == last_position:
                stuck_steps += 1
            else:
                stuck_steps = 0
            last_position = current_position
            if stuck_steps >= config.TIMEOUT_STEPS:
                print('Timeout steps reached')
                done = True
            if total_reward<=-10000:
                print('Max negative rewards')
                done=True

            # Render the game state
            main_surface.fill((50, 50, 50))  # Dark grey background
            # Draw the game surface
            game_surface = pygame.Surface((WIDTH, HEIGHT))
            game_surface.blit(GRASS, (0, 0))
            game_surface.blit(TRACK, (0, 0))
            game_surface.blit(FINISH, FINISH_POSITION)
            game_surface.blit(TRACK_BORDER, (0, 0))
            env.player_car.draw(game_surface)

            for angle in range(0, 360, 45):
                distance = env.player_car.ray_cast(TRACK_BORDER_MASK, angle)
                end_x = env.player_car.x + distance * math.cos(math.radians(angle))
                end_y = env.player_car.y + distance * math.sin(math.radians(angle))
                pygame.draw.line(game_surface, (192, 235, 166), (int(env.player_car.x), int(env.player_car.y)), (int(end_x), int(end_y)), 1)

            main_surface.blit(game_surface, (0, 0))
            
            # Draw the info panel
            info_surface = pygame.Surface((200, HEIGHT))
            info_surface.fill((30, 30, 30))  # Darker grey for info panel
            
            # Draw episode and step information
            texts = [
                f"Episode: {episode + 1}",
                f"Step: {step}",
                f"Total Reward: {total_reward:.2f}",
                f"Epsilon: {agent.epsilon:.2f}"
            ]

            for i, text in enumerate(texts):
                text_surface = font.render(text, True, (255, 255, 255))
                info_surface.blit(text_surface, (10, 10 + i * 30))
            
            # Draw the action visualization
            action_surface = draw_actions(info_surface, action)
            info_surface.blit(action_surface, (20, HEIGHT - 180))
            main_surface.blit(info_surface, (WIDTH, 0))
            
            pygame.display.update()
            clock.tick(config.FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    plt.figure()
                    plt.plot(range(len(rewards)), rewards)
                    plt.xlabel('Episode')
                    plt.ylabel('Total Reward')
                    plt.title('Episode vs Reward')
                    plt.grid(True)
                    plt.savefig(f'training_runs/training_run_{timestamp}.png')
                    pygame.quit()
                    return

            step += 1

        rewards.append(total_reward)
        print(f"Episode {episode + 1}, Total Reward: {total_reward}")
        # Decay epsilon
        agent.epsilon = max(0.01, agent.epsilon * 0.995)

    # Save the final trained Q-table
    with open(f'models/q_table_final_{timestamp}.pkl', 'wb') as f:
        pickle.dump(agent.q_table, f)

    pygame.quit()

if __name__ == "__main__":
    train()