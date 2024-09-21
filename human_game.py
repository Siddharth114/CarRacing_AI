import pygame
import time
import math
from game_utils import resize_images_to_largest, scale_image, blit_rotate_center

GRASS, TRACK, TRACK_BORDER = resize_images_to_largest(
    ["assets/grass.jpg", "assets/track.png", "assets/track-border.png"]
)

FINISH = pygame.image.load("assets/finish.png")
CAR = scale_image(pygame.image.load("assets/red-car.png"), 0.5)

WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Human Playable Game")


class AbstractCar:
    def __init__(self, max_velocity, rotation_velocity):
        self.image = self.IMAGE
        self.max_velocity = max_velocity
        self.velocity = 0
        self.rotation_velocity = rotation_velocity
        self.angle = 0
        self.x, self.y = self.START_POSITION

    def rotate(self, left=False, right=False):
        if left:
            self.angle += self.rotation_velocity
        elif right:
            self.angle -= self.rotation_velocity
    
    def draw(self, win):
        blit_rotate_center(win, self.image, (self.x, self.y), self.angle)


class HumanCar(AbstractCar):
    IMAGE = CAR
    START_POSITION = (180,200)

running = True
FPS = 60
clock = pygame.time.Clock()
images = [(GRASS, (0,0)), (TRACK, (0,0))]
human_car = HumanCar(4,4)


def draw(win, images, player_car):
    for image, position in images:
        win.blit(image, position)
    player_car.draw(WIN)
    pygame.display.update()

while running:
    clock.tick(FPS)

    draw(WIN, images, human_car)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break

pygame.quit()