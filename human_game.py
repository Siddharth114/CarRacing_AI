import pygame
import random
import math
from game_utils import resize_images_to_largest, scale_image, blit_rotate_center

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
pygame.display.set_caption("Human Playable Game")

class Car:
    def __init__(self, max_velocity, rotation_velocity):
        self.image = CAR
        self.max_velocity = max_velocity
        self.velocity = 0
        self.rotation_velocity = rotation_velocity
        self.angle = 270
        self.START_POSITION = (506, 720)
        self.x, self.y = self.START_POSITION
        self.acceleration = 0.1
        self.previous_position = self.START_POSITION


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

        new_y = self.y - vertical_velocity
        new_x = self.x - horizontal_velocity

        self.previous_position = (self.x, self.y)

        self.y = new_y
        self.x = new_x

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
    
    def handle_collision(self):
        self.x, self.y = self.previous_position
        self.velocity *= 0.5
        self.angle += 5 if random.random() > 0.5 else -5

    def bounce(self):
        self.velocity *= -1
        self.move()

    def reset(self):
        self.x, self.y = self.START_POSITION
        self.angle = 270
        self.velocity = 0


running = True
FPS = 60
clock = pygame.time.Clock()
images = [
    (GRASS, (0, 0)),
    (TRACK, (0, 0)),
    (FINISH, FINISH_POSITION),
    (TRACK_BORDER, (0, 0)),
]
player_car = Car(6, 4)


def draw(win, images, player_car):
    for image, position in images:
        win.blit(image, position)
    player_car.draw(WIN)
    pygame.display.update()


def move_player(player_car):
    keys = pygame.key.get_pressed()
    moved = False

    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        player_car.rotate(left=True)
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        player_car.rotate(right=True)
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        moved = True
        player_car.move_forward()
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        moved = True
        player_car.move_backward()

    if not moved:
        player_car.reduce_speed()

    if player_car.collide(TRACK_BORDER_MASK) is not None:
        player_car.handle_collision()


while running:
    clock.tick(FPS)

    draw(WIN, images, player_car)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break

    move_player(player_car)

    finish_collision_point_of_intersection = player_car.collide(
        FINISH_MASK, *FINISH_POSITION
    )
    if finish_collision_point_of_intersection is not None:
        if finish_collision_point_of_intersection[1] == 0:
            player_car.handle_collision()
        else:
            player_car.reset()


pygame.quit()
