import pygame
import math
import matplotlib.pyplot as plt
from environment import ParallelLearningCarEnvironment
from agent import ParallelQLearningAgent
import config
from ai_game import (
    GRASS,
    TRACK,
    TRACK_BORDER,
    TRACK_BORDER_MASK,
    FINISH,
    FINISH_POSITION,
    WIDTH,
    HEIGHT,
)


def train():
    pygame.init()
    NUM_CARS = 10
    env = ParallelLearningCarEnvironment(num_cars=NUM_CARS)
    agent = ParallelQLearningAgent(
        action_space=[0, 1, 2, 3, 4],
        num_agents=NUM_CARS,
        learning_rate=config.LEARNING_RATE,
        discount_factor=config.DISCOUNT_FACTOR,
        epsilon=config.EPSILON,
    )

    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    main_surface = pygame.display.set_mode((WIDTH + 200, HEIGHT))
    pygame.display.set_caption("Parallel RL Car Racing Game")

    car_colors = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (255, 0, 255),
        (0, 255, 255),
        (255, 128, 0),
        (128, 0, 255),
        (0, 255, 128),
        (255, 128, 128),
    ]

    episode_rewards = []
    best_reward_ever = float("-inf")
    best_distance_ever = float("-inf")
    for episode in range(config.NUM_EPISODES):
        states = env.reset()
        population_done = False
        step = 0
        current_episode_best = float("-inf")
        current_episode_best_distance = float("-inf")
        while not population_done:
            actions = agent.choose_actions(states)
            next_states, rewards, dones, population_done = env.step(actions)

            agent.update_q_values(states, actions, rewards, next_states)

            states = [s for s, d in zip(next_states, dones) if not d]

            if env.car_rewards:
                current_episode_best = max(max(env.car_rewards), current_episode_best)
                best_reward_ever = max(best_reward_ever, current_episode_best)

            current_episode_best_distance = max([car.distance_traveled for car in env.cars])
            best_distance_ever = max(best_distance_ever, current_episode_best_distance)

            main_surface.fill((50, 50, 50))
            game_surface = pygame.Surface((WIDTH, HEIGHT))

            game_surface.blit(GRASS, (0, 0))
            game_surface.blit(TRACK, (0, 0))
            game_surface.blit(FINISH, FINISH_POSITION)

            for i, car in enumerate(env.cars):
                if i in env.active_cars:
                    for angle in range(0, 360, 45):
                        distance = car.ray_cast(TRACK_BORDER_MASK, angle)
                        start_pos = (int(car.x), int(car.y))
                        end_x = car.x + distance * math.cos(math.radians(angle))
                        end_y = car.y + distance * math.sin(math.radians(angle))
                        end_pos = (int(end_x), int(end_y))
                        pygame.draw.line(
                            game_surface,
                            car_colors[i % len(car_colors)],
                            start_pos,
                            end_pos,
                            1,
                        )
                    car.draw(game_surface)

            game_surface.blit(TRACK_BORDER, (0, 0))
            main_surface.blit(game_surface, (0, 0))

            info_surface = pygame.Surface((200, HEIGHT))
            info_surface.fill((30, 30, 30))

            texts = [
                f"Episode: {episode + 1}/{config.NUM_EPISODES}",
                f"Step: {step}",
                f"Active Cars: {len(env.active_cars)}",
                f"Epsilon: {agent.epsilon:.2f}",
                "",
                f"Current Episode:",
                f"Best Reward: {current_episode_best:.2f}",
                f"Best Distance: {current_episode_best_distance:.2f}",
                "",
                f"All Episodes:",
                f"Best Reward: {best_reward_ever:.2f}",
                f"Best Distance: {best_distance_ever:.2f}",
            ]

            for i, text in enumerate(texts):
                color = (255, 255, 255)
                if "Best" in text:
                    color = (0, 255, 0)
                text_surface = font.render(text, True, color)
                info_surface.blit(text_surface, (10, 10 + i * 25))

            main_surface.blit(info_surface, (WIDTH, 0))

            pygame.display.update()
            clock.tick(config.FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    pygame.quit()
                    return

            step += 1

        best_car_index = env.get_best_car_index()
        agent.clone_best_q_table(best_car_index)

        episode_rewards.append(current_episode_best)
        print(
            f"Episode {episode + 1}, Best Reward: {current_episode_best:.2f}, All-Time Best: {best_reward_ever:.2f}"
        )

        agent.epsilon = max(0.01, agent.epsilon * 0.995)

    pygame.quit()


if __name__ == "__main__":
    train()
