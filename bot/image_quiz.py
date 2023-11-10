'''Image quiz classes'''

import json
import logging
import os
import random

from .image_generation import generate_images

logger = logging.getLogger(__name__)


class ImageData:
    '''Information about an image for the game.'''

    def __init__(self, title=None, filepaths=None, valid_responses=None):
        '''Stores information about an image for the game.

        Arguments:
            - title: Full title of the game
            - filepaths: paths to the screenshot file
            - valid_resposes: iterable of valid responses for the quiz

        Example:
            ImageData(
                'Metroid Prime',
                ['metroid_prime.png'],
                {'metroid prime', 'mp'})
        '''

        self.title = title
        self.filepaths = filepaths

        # Picks one image at random
        self.filepath = random.choice(filepaths)

        if valid_responses is None:
            self.valid_responses = set()
        else:
            self.valid_responses = set(map(self._normalize, valid_responses))

    def check(self, response):
        '''Checks if response contains any of the valid responses.'''

        response = self._normalize(response)
        for vr in self.valid_responses:
            if vr in response:
                return True
        return False

    def _normalize(self, value):
        '''Cleans a bit the string.'''

        return value.lower().strip()

    def __repr__(self):
        return 'ImageData({}, {}, {})'.format(
            repr(self.title), repr(self.filepath), repr(self.valid_responses)
        )


def _validate_fields_exist(fields, dictionary):
    '''Checks that the needed fields are present in the dictionary.'''

    for f in fields:
        if f not in dictionary:
            raise ValueError(f'Missing "{f}" field in "{dictionary}"')


def load_definition_from_file(filepath):
    '''Reads filepath and creates a ImageData object.'''

    with open(filepath) as fin:
        json_content = json.load(fin)

    _validate_fields_exist(['title', 'filepaths', 'valid_responses'], json_content)

    base_path = os.path.dirname(filepath)

    return ImageData(
        json_content['title'],
        [os.path.join(base_path, fp) for fp in json_content['filepaths']],
        json_content['valid_responses'],
    )


class ImageGame:
    '''Image-guesing game.'''

    def __init__(self, definition):
        self.definition = definition

        self.clue_idx = 0

        logger.info('Generating clues...')
        self.clues = generate_images(definition.filepath)

    def is_valid(self, response):
        '''Returns True if the response is correct.'''

        return self.definition.check(response)

    def next_clue(self):
        '''Returns the next image clue for the game or None.'''

        if self.clue_idx == len(self.clues):
            self.clue_idx += 1
            return self.get_image()

        if self.clue_idx > len(self.clues):
            logger.debug('No more clues for %s', self.definition)
            return None

        clue = self.clues[self.clue_idx]
        self.clue_idx += 1
        return clue

    def get_solution(self):
        '''Returns the correct solution title.'''
        return self.definition.title

    def get_image(self):
        '''Returns the image solution.'''
        return self.definition.filepath

    def clean(self):
        '''Deletes all clue images.'''

        logger.info('Deleting clue images...')
        for path in self.clues:
            logger.debug('Deleting %s', path)
            os.remove(path)

    def __str__(self):
        return f'ImageGame title: "{self.get_solution()}" clues: {self.clues}'
