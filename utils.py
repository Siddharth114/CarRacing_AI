import pygame

def discretize_state(value, min_value, max_value, num_bins):
    bin_size = (max_value - min_value) / num_bins
    return min(num_bins - 1, max(0, int((value - min_value) / bin_size)))

def draw_actions(surface, action):
    key_surface = pygame.Surface((160, 160))
    key_surface.set_alpha(128)
    key_surface.fill((50, 50, 50))
    
    keys = [
        ((0, 40, 40, 80), [(10, 80), (30, 70), (30, 90)]),   # Left
        ((120, 40, 40, 80), [(150, 80), (130, 70), (130, 90)]), # Right
        ((40, 0, 80, 40), [(80, 10), (70, 30), (90, 30)]),   # Up
        ((40, 120, 80, 40), [(80, 150), (70, 130), (90, 130)])  # Down
    ]
    
    for i, (rect, arrow) in enumerate(keys):
        color = (255, 255, 255) if action == i else (100, 100, 100)
        pygame.draw.rect(key_surface, color, rect, border_radius=5)  # Rounded rectangles for key shape
        pygame.draw.polygon(key_surface, (0, 0, 0), arrow)
    
    if action == 4:
        pygame.draw.circle(key_surface, (255, 255, 255), (80, 80), 20)
    else:
        pygame.draw.circle(key_surface, (100, 100, 100), (80, 80), 20)
    return key_surface