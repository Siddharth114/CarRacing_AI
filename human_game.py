import pygame
import time
import math

GRASS = pygame.image.load('assets/grass.jpg')
TRACK = pygame.image.load('assets/track.png')
TRACK_BORDER = pygame.image.load('assets/track-border.png')
FINISH = pygame.image.load('assets/finish.png')
CAR = pygame.image.load('assets/red-car.png')

WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Human Playable Game')

