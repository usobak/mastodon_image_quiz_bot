'''Tests for manager module.'''

import unittest

from unittest.mock import patch, Mock

from . import manager
from . import state

class BotManagerTest(unittest.TestCase):

    def test_constructor(self):
        '''The constructor works.'''

        manager.BotManager(Mock(), 'test_owner', '/tmp')


    def test_constructor(self):
        '''Constructor argument validation.'''

        with self.assertRaises(ValueError):
            manager.BotManager(None, 'test_owner', '/tmp')

        with self.assertRaises(ValueError):
            manager.BotManager(Mock(), 'test_owner', None)


    def test_changeState(self):
        '''The method changeState works.'''

        expected_state = manager.BotStates.FINISH_EXECUTION
        m = manager.BotManager(Mock(), 'test_owner', '/tmp')
        m._changeState(expected_state)

        self.assertEqual(expected_state, m.currentState)

   
    def test_onStateStart(self):
        '''State start handler works.'''

        mock_state = Mock()
        manager.State = mock_state
        m = manager.BotManager(Mock(), 'test_owner', '/tmp')
        expected_state = manager.BotStates.NEW_ROUND

        m._onStateStart()
        self.assertEqual(expected_state, m.currentState)
        self.assertTrue(mock_state.called)


    def test_onStateNewRound_JSON(self):
        '''Loads all JSON files.'''
        self.assertTrue(False)


    def test_onStateNewRound_NoQuestions(self):
        '''Can't load any questions.'''

        m = manager.BotManager(Mock(), 'test_owner', '/tmp')
        m._load_dataset = lambda s: []

        with self.assertRaises(ValueError):
            m._onStateNewRound()
        

    def test_onStateNewRound(self):
        '''State new round works fine.'''

        m = manager.BotManager(Mock(), 'test_owner', '/tmp')

        # Mock question loading
        q1 = Mock()
        q1.filepath = 'path1'
        questions = [q1]
        m._load_dataset = lambda s: questions

        # Mock image generation
        mock_image = Mock()
        manager.ImageGame = mock_image

        m._onStateNewRound()

        # Check mock calls
        mock_image.assert_called_with(q1) 


    def test_onStateNewRound_NoRepeat(self):
        '''Does not repeat a question if it is in the history.'''

        m = manager.BotManager(Mock(), 'test_owner', '/tmp', 1)
        m._onStateStart()

        # Mock question loading
        q1 = Mock()
        q1.filepath = 'path1'
        q2 = Mock()
        q2.filepath = 'path2'
        questions = [q1, q2]
        m._load_dataset = lambda s: questions

        # State history already contains q1
        m.gameState.history = [q1.filepath]

        # Mock image generation
        mock_image = Mock()
        manager.ImageGame = mock_image

        m._onStateNewRound()

        # Check mock calls
        mock_image.assert_called_with(q2)

