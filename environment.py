import pygame
from ai_game import (
    Car,
    TRACK_BORDER_MASK,
    FINISH_MASK,
    FINISH_POSITION,
    WIN,
    WIDTH,
    HEIGHT,
)
from utils import discretize_state


class CarRacingEnvironment:
    def __init__(self):
        self.player_car = Car(8, 4)
        self.reset()
