'''Manager encapsulates the main functionality of the bot.

Usage:

1) Create the bot with the constructor.

2) Load one or more folders with images. See Readme.md.

3) Start the bot with the run() method. 
'''

import glob
import logging
import os
import random
import sys
import time

from datetime import datetime

from . import strings
from .image_quiz import ImageGame, load_definition_from_file
from .state import State


logger = logging.getLogger(__name__)

DEFAULT_CLUE_DELAY_SECONDS = 60*60*2
DEFAULT_CHECK_DELAY_SECONDS = 60*5

# Number of games before the same image is used again
HISTORY_SIZE = 50

class BotManager:
    '''Bot for image-based quizes on Mastodon.'''

    def __init__(self, mastodon_client, owner):
        if mastodon_client is None:
            raise ValueError('Mastodon client required')

        self.questions = []
        self.mastodon_client = mastodon_client
        self.owner = owner

        self.state = State(HISTORY_SIZE)
        self.state.loadFromDisk()


    def load_dataset(self, path):
        '''Loads quiz questions from a directory.'''

        logger.info('Loading dataset...')

        definitions = glob.glob(os.path.join(path, '*.json'))
        logger.debug(
                'Found %d definition files: %s', len(definitions), definitions)

        questions = []
        for d in definitions:
            try:
                logger.debug('Parsing %s...', d)
                q = load_definition_from_file(d)
                logger.debug(q)
                questions.append(q)
            except Exception as e:
                logger.error('Unable to parse %s', d)
                logger.error(e, exc_info=True)
                sys.exit(-1)

        logger.info('%d questions loaded successfully', len(questions))
        self.questions.extend(questions)


    def _new_game(self):
        if not self.questions:
            msg = 'Unable to find any question'
            logger.error(msg)
            raise ValueError(msg)

        question = random.choice(self.questions)
        if len(self.questions) > HISTORY_SIZE:
            while question.filepath in self.state.getQuestions():
                logger.debug('Repeated question: %s', question.filepath)
                question = random.choice(self.questions)

        logger.debug('Selected question: %s', question)

        return ImageGame(question)


    def _publish_new_clue(self, current_game):
        clue = current_game.next_clue()
        if clue is None:
            return None
        num_clues = len(current_game.clues) + 1

        msg = strings.NEW_CLUE.format(current_game.clue_idx, num_clues)
        if current_game.clue_idx == num_clues:
            msg = strings.LAST_CLUE.format(
                    current_game.clue_idx, num_clues)

        return self.mastodon_client.post_with_media(msg, clue)


    def _publish_solution_found(self, current_game, response):
        self.state.addQuestion(current_game.definition.filepath)
        solution = current_game.get_solution()
        msg = strings.SOLUTION_FOUND.format(solution)
        # TODO use response
        return self.mastodon_client.post_with_media(
                msg, current_game.get_image())



    def _publish_finished(self, current_game):
        self.state.addQuestion(current_game.definition.filepath)
        solution = current_game.get_solution()
        msg = strings.SOLUTION_NOT_FOUND.format(solution)
        return self.mastodon_client.post_with_media(
                msg, current_game.get_image())


    def _check_for_owner_commands(self, response):
        if response.creator != self.owner:
            return

        logger.info('Received message from the owner: %s', response.content)

        if 'DIE' in response.content:
            logger.info('I have received the command to shut down myself')
            sys.exit(-1)


    def run(self, clue_delay_seconds=DEFAULT_CLUE_DELAY_SECONDS,
            check_delay_seconds=DEFAULT_CHECK_DELAY_SECONDS):
        '''Executes the bot main loop.

        Arguments:
            clue_delay_seconds: delay before publishing a new clue
            check_delay_seconds: delay before checking for new responses
        '''

        logger.info(
            'Running with clue_delay_seconds=%d check_delay_seconds=%d',
            clue_delay_seconds, check_delay_seconds)

        last_clue = datetime.min
        current_game = None
        clue_post_ids = set()
        while True:

            if current_game is None:
                # No game is currently on. Create a new one
                logger.info('Creating new game...')
                last_clue = datetime.min
                current_game = self._new_game()
                logger.info(current_game)
                clue_post_ids = set()

            # Check for responses and validate them
            logger.info('Checking for responses...')
            responses = self.mastodon_client.get_responses()
            logger.debug('Received %d responses', len(responses))
            for r in responses:
                self._check_for_owner_commands(r)

                if current_game is None:
                    logging.info('No current game')
                elif r.in_reply_to_id not in clue_post_ids:
                    logging.debug(
                        'post_id = %s, clue_post_ids = %s',
                            r.post_id, clue_post_ids)
                    logging.info('Response not in current game posts')
                elif current_game.is_valid(r.content):
                    logging.info('Correct response!')
                    # Correct response!
                    self._publish_solution_found(current_game, r)
                    current_game.clean()
                    current_game = None
                else:
                    logging.info('Invalid response')

            # Publish a new clue?
            if (current_game is not None and
                _enough_delay(clue_delay_seconds, last_clue)):
                logger.info('Publishing new clue...')
                post_id = self._publish_new_clue(current_game)
                if post_id is not None:
                    clue_post_ids.add(post_id)
                else:
                    logger.info('No more clues. Finishing current game...')
                    self._publish_finished(current_game)
                    current_game.clean()
                    current_game = None

                last_clue = datetime.now()

            # Wait a bit before checking again
            logger.info('Waiting...')
            time.sleep(check_delay_seconds)


def _enough_delay(delay_seconds, start, end=None):
    '''Checks if enough time has passed since start.

    Arguments:
        delay_seconds:
        start:
        end:

    Returns:
        True or False
    '''

    if end is None:
        end = datetime.now()
    return (end - start).total_seconds() > delay_seconds
