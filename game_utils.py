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