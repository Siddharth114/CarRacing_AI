import pygame

def discretize_state(x, y, angle):
    return (int(x // 10), int(y // 10), int(angle // 10))

def draw_actions(surface, action):
    key_surface = pygame.Surface((160, 160))
    key_surface.set_alpha(128)
    key_surface.fill((50, 50, 50))
    
    keys = [
        ((80, 0, 80, 80), [(80, 20), (60, 60), (100, 60)]),   # Up
        ((0, 80, 80, 80), [(20, 80), (60, 60), (60, 100)]),   # Left
        ((160, 80, 80, 80), [(140, 80), (100, 60), (100, 100)]), # Right
        ((80, 160, 80, 80), [(80, 140), (60, 100), (100, 100)])  # Down
    ]
    
    for i, (rect, arrow) in enumerate(keys):
        color = (255, 255, 255) if action == i else (100, 100, 100)
        pygame.draw.rect(key_surface, color, rect)
        pygame.draw.polygon(key_surface, (0, 0, 0), arrow)
    
    # Draw the "do nothing" action
    if action == 4:
        pygame.draw.circle(key_surface, (255, 255, 255), (80, 80), 20)
    else:
        pygame.draw.circle(key_surface, (100, 100, 100), (80, 80), 20)
    
    return key_surface