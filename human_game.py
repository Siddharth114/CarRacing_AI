import pygame
import math
from game_utils import resize_images_to_largest, scale_image, has_completed_track

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
pygame.display.set_caption("Human Playable Game")

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
        self.rotated_image = pygame.transform.rotate(self.image, self.angle)
        self.rect = self.rotated_image.get_rect(center=(self.x, self.y))
        self.distance_traveled = 0

    def rotate(self, left=False, right=False):
        """Rotate the car image and update the mask."""
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

        self.previous_position = (self.x, self.y)
        
        distance_this_frame = math.sqrt((new_x - self.x)**2 + (new_y - self.y)**2)
        self.distance_traveled += distance_this_frame if self.velocity > 0 else -distance_this_frame

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
        self.distance_traveled = 0
        self.rotated_image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.rotated_image.get_rect(center=(self.x, self.y))
        self.mask = pygame.mask.from_surface(self.rotated_image)

def draw_info_panel(win, player_car):
    """Draw information pane with distance traveled."""
    font = pygame.font.Font(None, 36)
    distance_text = font.render(f"Distance Traveled: {int(player_car.distance_traveled)}", True, (255, 255, 255))
    text_rect = distance_text.get_rect()
    text_rect.topleft = (10, 10)
    
    background_rect = text_rect.copy()
    background_rect.inflate_ip(20, 20)
    background_surface = pygame.Surface(background_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(background_surface, (0, 0, 0, 128), background_surface.get_rect())
    win.blit(background_surface, background_rect)
    
    win.blit(distance_text, text_rect)

def draw(win, images, player_car):
    """Draw all game elements onto the window."""
    for image, position in images:
        win.blit(image, position)
    player_car.draw(win)
    draw_info_panel(win, player_car)
    pygame.display.update()

def move_player(player_car):
    """Handle player input and move the car accordingly."""
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

    if (player_car.collide(TRACK_BORDER_MASK) is not None) or (player_car.collide(GRASS_MASK) is not None):
        player_car.handle_collision()

def main():
    """Main game loop."""
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

    while running:
        clock.tick(FPS)

        draw(WIN, images, player_car)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    break
                elif event.key == pygame.K_r:
                    player_car.reset()
            

        move_player(player_car)

        finish_collision_point_of_intersection = player_car.collide(
            FINISH_MASK, *FINISH_POSITION
        )
        if finish_collision_point_of_intersection is not None:
            if has_completed_track(player_car.initial_angle, FINISH_POSITION, (player_car.x, player_car.y)):
                print('Completed circuit!')
                player_car.reset()
            else:
                print('Go around the whole track!')
                player_car.reset()

    pygame.quit()

if __name__ == "__main__":
    main()