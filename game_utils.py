import pygame

def resize_images_to_largest(image_paths):
    images = [pygame.image.load(path) for path in image_paths]

    sizes = [image.get_size() for image in images]


    max_width = max(size[0] for size in sizes)
    max_height = max(size[1] for size in sizes)

    max_size = (max_width, max_height)

    resized_images = [pygame.transform.scale(image, max_size) for image in images]

    return resized_images

def scale_image(image, scale_factor):
    current_size = image.get_size()

    new_size = tuple(map(lambda x: int(x * scale_factor), current_size))

    return pygame.transform.scale(image, new_size)

def blit_rotate_center(win, image, top_left, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    # Rotating the image around the centre of the image, instead of around the top left of the image
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft = top_left).center)
    win.blit(rotated_image, new_rect.topleft)
    
def has_completed_track(starting_angle, finish_position, current_car_position):
    if starting_angle==0:
        return finish_position[1] <= current_car_position[1]
    elif starting_angle==90:
        return finish_position[0] <= current_car_position[0]
    elif starting_angle==180:
        return finish_position[1] >= current_car_position[1]
    elif starting_angle==270:
        return finish_position[0] >= current_car_position[0]