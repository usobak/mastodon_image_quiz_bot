'''Tests for image_generation module.'''

import unittest

from unittest.mock import patch, Mock

from . import image_generation


class ImageGenerationTest(unittest.TestCase):

    def test_generate_images(self):
        '''With mock Image returns 11 clues.'''

        with patch.object(image_generation.Image, 'open') as mock_open:
            mock_image = Mock()
            mock_image.size = (10, 10)
            mock_open.return_value = mock_image

            images = image_generation.generate_images('t')

            self.assertEqual(len(images), 11)


    def test_compute_chunks_1_chunk(self):
        '''Segments the image correctly in 1 chunk.'''

        chunks = image_generation.compute_chunks(10, 10, 1, 1)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks, [(0, 0, 9, 9)])


    def test_compute_chunks_2_chunks(self):
        '''Segments the image correctly in 2 chunks.'''

        chunks = image_generation.compute_chunks(10, 10, 2, 1)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks, [(0, 0, 9, 4), (0, 5, 9, 9)])
