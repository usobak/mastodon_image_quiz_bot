'''Tests for image_quiz.py.'''

import json
import unittest

from unittest.mock import patch, mock_open, call

from . import image_quiz
from .image_quiz import ImageData, load_definition_from_file, ImageGame


class ImageDataTest(unittest.TestCase):
    '''Tests for ImageData class.'''

    def test_constructor(self):
        '''Properly constructs the object.'''

        expected_title = 'Metroid Prime'
        expected_filepath = 'metroid_prime.png'
        expected_valid_responses = {'metroid prime', 'mp'}
        valid_responses = {'Metroid Prime', 'MP '}

        definition = ImageData(expected_title, expected_filepath, valid_responses)

        self.assertEqual(definition.title, expected_title)
        self.assertEqual(definition.filepath, expected_filepath)
        self.assertEqual(definition.valid_responses, expected_valid_responses)

    def test_repr(self):
        '''Repr works fine.'''

        expected_definition = ImageData('title', 'filepath', {'a', 'b', 'c'})
        definition = eval(repr(expected_definition))

        self.assertEqual(definition.title, expected_definition.title)
        self.assertEqual(definition.filepath, expected_definition.filepath)
        self.assertEqual(
            definition.valid_responses, expected_definition.valid_responses
        )


class LoadDefinitionFromFileTest(unittest.TestCase):
    '''Tests for test_load_definition_from_file.'''

    def test_load_definition_from_file(self):
        '''Loads a file correctly.'''

        expected_definition = {
            'title': 'Chrono Trigger',
            'filepath': 'chrono_trigger',
            'valid_responses': ['chrono trigger'],
        }
        expected_filepath = 'something.json'
        json_file = json.dumps(expected_definition)

        with patch('builtins.open', mock_open(read_data=json_file)) as mock_file:
            definition = load_definition_from_file(expected_filepath)
            mock_file.assert_called_with(expected_filepath)

        self.assertEqual(definition.title, expected_definition['title'])
        self.assertEqual(definition.filepath, expected_definition['filepath'])
        self.assertEqual(
            definition.valid_responses, set(expected_definition['valid_responses'])
        )


class ImageGameTest(unittest.TestCase):
    '''Tests for ImageGame class.'''

    @patch.object(image_quiz, 'generate_images')
    def test_constructor(self, mock):
        '''With mocked image generation, it constructs the object.'''

        mock.return_value = ['a', 'b', 'c']
        ImageGame(ImageData('title', 'path', ['r1', 'r2']))

        mock.assert_called_with('path')

    def test_is_valid(self):
        '''Checks responses correctly.'''

        game = create_game()

        self.assertTrue(game.is_valid('r1'))
        self.assertTrue(game.is_valid('r2'))
        self.assertFalse(game.is_valid('other'))

    def test_next_clue(self):
        '''Next clue works fine.'''

        game = create_game()

        self.assertEqual(game.next_clue(), 'a')
        self.assertEqual(game.next_clue(), 'b')
        self.assertEqual(game.next_clue(), 'c')
        self.assertEqual(game.next_clue(), 'path')

    def test_next_clue_no_more_clues(self):
        '''Next clue returns None if no more clues exist.'''

        game = create_game()

        game.clues = []
        game.next_clue()  # Get the original image
        self.assertIsNone(game.next_clue())

    def test_get_solution(self):
        '''Returns the game solution.'''

        game = create_game()

        self.assertEqual(game.get_solution(), 'title')

    def test_get_image(self):
        '''Returns the final image.'''

        game = create_game()

        self.assertEqual(game.get_image(), 'path')

    @patch('os.remove')
    def test_clean(self, mock_remove):
        '''Cleans the generated images.'''

        game = create_game()
        game.clean()

        mock_remove.assert_has_calls([call('a'), call('b'), call('c')])


def create_game():
    '''Creates an ImageGame instances.'''

    with patch.object(image_quiz, 'generate_images') as mock:
        mock.return_value = ['a', 'b', 'c']
        return ImageGame(ImageData('title', 'path', ['r1', 'r2']))


if __name__ == '__main__':
    unittest.main()
