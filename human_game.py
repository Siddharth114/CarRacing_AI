import pygame
import time
import math
from game_utils import resize_images_to_largest, scale_image

GRASS, TRACK, TRACK_BORDER = resize_images_to_largest(
    ["assets/grass.jpg", "assets/track.png", "assets/track-border.png"]
)

FINISH = pygame.image.load("assets/finish.png")
CAR = scale_image(pygame.image.load("assets/red-car.png"), 0.5)

WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Human Playable Game")

running = True
FPS = 60
clock = pygame.time.Clock()
images = [(GRASS, (0,0)), (TRACK, (0,0))]

def draw(win, images):
    for image, position in images:
        win.blit(image, position)

while running:
    clock.tick(FPS)

    draw(WIN, images)

    pygame.display.update()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break

pygame.quit()