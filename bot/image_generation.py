'''Generate partially-blocked images based on the original one.

generate_images splits the starting image in ROWS x COLS regions and
creates images where one by one each of the regions is covered.

Returns the list of generated images in reversed order to simulate that it is
revealing the image.
'''

import logging
import os
import uuid
import random

from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

OUTPUT_PATH = './output/'
ROWS = 3
COLS = 4
COLOR = (0, 0, 0, 128)


def generate_images(key, output_path=OUTPUT_PATH):
    '''Generates n images based on the starting. Returns the list of images.'''

    base_image_path = key
    base_image = Image.open(base_image_path)
    width, height = base_image.size

    chunks = compute_chunks(height, width, ROWS, COLS)
    logger.debug(chunks)
    random.shuffle(chunks)
    chunks.pop()

    key = uuid.uuid4()
    image_paths = generate_step_images(key, base_image, chunks, output_path)

    return image_paths


def compute_chunks(height, width, rows, cols):
    '''Returns retangle positions to cover the image.'''

    chunk_height = height // rows
    chunk_width = width // cols

    horizontal_steps = [i * chunk_width for i in range(cols)]
    vertical_steps = [i * chunk_height for i in range(rows)]

    chunks = []
    for v in vertical_steps:
        for h in horizontal_steps:
            chunks.append((h, v, h + chunk_width - 1, v + chunk_height - 1))
    return chunks


def generate_step_images(key, base_image, chunks, output_path):
    '''Writes the images to files.'''

    paths = []
    draw_context = ImageDraw.Draw(base_image)
    for i, chunk in reversed(list(enumerate(chunks))):
        logger.debug('%d %s', i, chunk)
        draw_context.rectangle(chunk, fill=COLOR)
        filename = f'{key}.{i+1}.png'
        filepath = os.path.join(output_path, filename)
        base_image.save(filepath, 'PNG')
        paths.append(filepath)
    return list(reversed(paths))
