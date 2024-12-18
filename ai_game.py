import pygame
from pygame.math import Vector2
import random
import math
from game_utils import resize_images_to_largest, scale_image

pygame.init()

GRASS, TRACK, TRACK_BORDER = resize_images_to_largest(
    ["assets/grass.jpg", "assets/bahrain_track.png", "assets/bahrain_track_border.png"]
)

TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)

FINISH = pygame.image.load("assets/finish.png")
FINISH_MASK = pygame.mask.from_surface(FINISH)
FINISH_POSITION = (480, 720)

CAR = scale_image(pygame.image.load("assets/red-car.png"), 0.5)

WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI Playable Game")
TRACK_MASK = pygame.mask.from_surface(TRACK)
GRASS_MASK = pygame.mask.from_surface(GRASS)

for x in range(GRASS_MASK.get_size()[0]):
    for y in range(GRASS_MASK.get_size()[1]):
        if TRACK_MASK.get_at((x, y)):
            GRASS_MASK.set_at((x, y), 0)


class Car:
    def __init__(self, max_velocity, rotation_velocity):
        self.original_image = CAR  
        self.image = self.original_image
        self.mask = pygame.mask.from_surface(self.image)
        self.max_velocity = max_velocity
        self.velocity = 0
        self.rotation_velocity = rotation_velocity
        self.initial_angle = 270
        self.angle = self.initial_angle
        self.START_POSITION = (520, 740)
        self.x, self.y = self.START_POSITION
        self.acceleration = 0.1
        self.previous_position = self.START_POSITION
        self.stuck_steps = 0
        self.rotated_image = pygame.transform.rotate(self.image, self.angle)
        self.rect = self.rotated_image.get_rect(center=(self.x, self.y))
        self.min_velocity_for_rotation = 0.1
        self.distance_traveled = 0

    def rotate(self, left=False, right=False):
        """Rotate the car image and update the mask."""
        if abs(self.velocity) >= self.min_velocity_for_rotation:
            if self.velocity > 0:
                if left:
                    self.angle += self.rotation_velocity
                elif right:
                    self.angle -= self.rotation_velocity
            else:
                if left:
                    self.angle -= self.rotation_velocity
                elif right:
                    self.angle += self.rotation_velocity

            self.rotated_image = pygame.transform.rotate(self.original_image, self.angle)
            self.rect = self.rotated_image.get_rect(center=(self.x, self.y))
            self.mask = pygame.mask.from_surface(self.rotated_image)

    def draw(self, win):
        """Draw the rotated car image onto the window."""
        win.blit(self.rotated_image, self.rect.topleft)

    def move_forward(self):
        """Accelerate the car forward."""
        if self.velocity < 0:
            self.velocity = min(self.velocity + self.acceleration * 2, 0)
        else:
            self.velocity = min(self.velocity + self.acceleration, self.max_velocity)
        self.move()

    def move_backward(self):
        """Accelerate the car backward."""
        if self.velocity > 0:
            self.velocity = max(self.velocity - self.acceleration * 2, 0)
        else:
            self.velocity = max(self.velocity - self.acceleration, -self.max_velocity / 2)
        self.move()

    def move(self):
        """Update the car's position based on its velocity and angle."""
        radians = math.radians(self.angle)
        vertical_velocity = math.cos(radians) * self.velocity
        horizontal_velocity = math.sin(radians) * self.velocity

        new_y = self.y - vertical_velocity
        new_x = self.x - horizontal_velocity

        if self.previous_position == (self.x, self.y):
            self.stuck_steps += 1 
        else:
            self.stuck_steps = 0

        self.previous_position = (self.x, self.y)
        
        self.distance_this_frame = math.sqrt((new_x - self.x)**2 + (new_y - self.y)**2)
        self.distance_traveled += self.distance_this_frame if self.velocity > 0 else -self.distance_this_frame

        self.y = new_y
        self.x = new_x
        self.rect.center = (self.x, self.y)

    def reduce_speed(self):
        """Gradually reduce the car's speed when not accelerating."""
        if self.velocity > 0:
            self.velocity = max(self.velocity - self.acceleration / 2, 0)
        elif self.velocity < 0:
            self.velocity = min(self.velocity + self.acceleration / 2, 0)
        self.move()

    def collide(self, mask, x=0, y=0):
        """
        Check for collision with another mask.
        :param mask: The mask to check collision against.
        :param x: X position of the other mask.
        :param y: Y position of the other mask.
        :return: Point of intersection or None.
        """
        offset_x = int(self.rect.left - x)
        offset_y = int(self.rect.top - y)
        point_of_intersection = mask.overlap(self.mask, (offset_x, offset_y))
        return point_of_intersection

    def handle_collision(self):
        """Handle collision by reverting to previous position and adjusting velocity and angle."""
        self.velocity *= 0.5 

        self.rotated_image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.rotated_image.get_rect(center=(self.x, self.y))
        self.mask = pygame.mask.from_surface(self.rotated_image)

    def bounce(self):
        """Reverse the car's velocity."""
        self.velocity *= -1
        self.move()

    def reset(self):
        """Reset the car to the starting position and state."""
        self.x, self.y = self.START_POSITION
        self.angle = 270
        self.velocity = 0
        self.stuck_steps = 0
        self.distance_traveled = 0
        self.rotated_image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.rotated_image.get_rect(center=(self.x, self.y))
        self.mask = pygame.mask.from_surface(self.rotated_image)

    def get_distances_to_border(self, track_border_mask):
        distances = []
        for angle in range(0, 360, 45):
            distance = self.ray_cast(track_border_mask, angle)
            distances.append(distance)
        return distances

    def ray_cast(self, mask, angle):
        length = 0
        max_length = max(TRACK.get_width(), TRACK.get_height())
        x, y = self.rect.center

        while length < max_length:
            length += 1
            target_x = x + length * math.cos(math.radians(angle))
            target_y = y + length * math.sin(math.radians(angle))
            
            if mask.get_at((int(target_x), int(target_y))):
                return length
        
        return max_length