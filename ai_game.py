import pygame
import time
import math
from game_utils import resize_images_to_largest, scale_image, blit_rotate_center

GRASS, TRACK, TRACK_BORDER = resize_images_to_largest(
    ["assets/grass.jpg", "assets/track.png", "assets/track-border.png"]
)

TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)

FINISH = pygame.image.load("assets/finish.png")
FINISH_MASK = pygame.mask.from_surface(FINISH)
FINISH_POSITION = (135, 250)
CAR = scale_image(pygame.image.load("assets/red-car.png"), 0.5)

WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RL Car Racing Game")


class Car:
    def __init__(self, max_velocity, rotation_velocity):
        self.image = CAR
        self.max_velocity = max_velocity
        self.velocity = 0
        self.rotation_velocity = rotation_velocity
        self.angle = 0
        self.START_POSITION = (165, 200)
        self.x, self.y = self.START_POSITION
        self.acceleration = 0.1

    def rotate(self, left=False, right=False):
        if self.velocity != 0:
            if self.velocity < 0:
                if left:
                    self.angle -= self.rotation_velocity
                elif right:
                    self.angle += self.rotation_velocity
            else:
                if left:
                    self.angle += self.rotation_velocity
                elif right:
                    self.angle -= self.rotation_velocity

    def draw(self, win):
        blit_rotate_center(win, self.image, (self.x, self.y), self.angle)

    def move_forward(self):
        if self.velocity < 0:
            self.velocity = min(self.velocity + self.acceleration * 2, 0)
        else:
            self.velocity = min(self.velocity + self.acceleration, self.max_velocity)
        self.move()

    def move_backward(self):
        if self.velocity > 0:
            self.velocity = max(self.velocity - self.acceleration * 2, 0)
        else:
            self.velocity = max(
                self.velocity - self.acceleration, -self.max_velocity / 2
            )
        self.move()

    def move(self):
        radians = math.radians(self.angle)
        vertical_velocity = math.cos(radians) * self.velocity
        horizontal_velocity = math.sin(radians) * self.velocity

        self.y -= vertical_velocity
        self.x -= horizontal_velocity

    def reduce_speed(self):
        if self.velocity > 0:
            self.velocity = max(self.velocity - self.acceleration / 2, 0)
        elif self.velocity < 0:
            self.velocity = min(self.velocity + self.acceleration / 2, 0)
        self.move()

    def collide(self, mask, x=0, y=0):
        car_mask = pygame.mask.from_surface(self.image)
        offset = (int(self.x - x), int(self.y - y))
        point_of_intersection = mask.overlap(car_mask, offset)
        return point_of_intersection

    def bounce(self):
        self.velocity *= -1
        self.move()

    def reset(self):
        self.x, self.y = self.START_POSITION
        self.angle = 0
        self.velocity = 0