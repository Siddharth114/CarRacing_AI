import pygame

def discretize_state(x, y, angle):
    return (int(x // 10), int(y // 10), int(angle // 10))

def draw_action(surface, action):
    key_surface = pygame.Surface((80, 80))
    key_surface.set_alpha(128)
    key_surface.fill((50, 50, 50))
    
    if action == 0:  # Left
        pygame.draw.polygon(key_surface, (255, 255, 255), [(60, 40), (20, 40), (40, 20)])
    elif action == 1:  # Right
        pygame.draw.polygon(key_surface, (255, 255, 255), [(20, 40), (60, 40), (40, 60)])
    elif action == 2:  # Accelerate
        pygame.draw.polygon(key_surface, (255, 255, 255), [(40, 20), (20, 60), (60, 60)])
    elif action == 3:  # Brake
        pygame.draw.polygon(key_surface, (255, 255, 255), [(20, 20), (60, 20), (40, 60)])
    # Action 4 (Do nothing) doesn't need visualization
    
    surface.blit(key_surface, (surface.get_width() - 100, surface.get_height() - 100))