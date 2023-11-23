'''Manager encapsulates the main functionality of the bot.

Usage:

1) Create the bot with the constructor.

2) Load one or more folders with images. See Readme.md.

3) Start the bot with the run() method.
'''

import enum
import glob
import logging
import os
import os.path
import random
import sys
import time

from datetime import datetime

from . import strings
from .util import enough_delay
from .state import State
from .image_quiz import ImageGame, load_definition_from_file


logger = logging.getLogger(__name__)


# Number of games before the same image is used again
HISTORY_SIZE = 50

DEFAULT_CLUE_DELAY_SECONDS = 60 * 60 * 2
DEFAULT_CHECK_DELAY_SECONDS = 60 * 5


class BotStates(enum.Enum):
    START = 'START'
    NEW_ROUND = 'NEW_ROUND'
    NEW_CLUE = 'NEW_CLUE'
    WAIT = 'WAIT'
    CHECK_RESPONSES = 'CHECK_RESPONSES'
    SOLUTION_FOUND = 'SOLUTION_FOUND'
    FINISH_ROUND = 'FINISH_ROUND'
    FINISH_EXECUTION = 'FINISH_EXECUTION'


class BotManager:
    '''Bot for image-based quizes on Mastodon.'''

    def __init__(
        self,
        mastodon_client,
        owner,
        datasetPath,
        history_size=HISTORY_SIZE,
        clueDelaySeconds=DEFAULT_CLUE_DELAY_SECONDS,
        checkDelaySeconds=DEFAULT_CHECK_DELAY_SECONDS,
    ):
        if mastodon_client is None:
            raise ValueError('Mastodon client required')

        if datasetPath is None:
            raise ValueError('dataset path required')

        if not os.path.isdir(datasetPath):
            raise ValueError('dataset path must be a directory')

        self.mastodon_client = mastodon_client
        self.owner = owner
        self.datasetPath = datasetPath
        self.history_size = history_size
        self.checkDelaySeconds = checkDelaySeconds
        self.clueDelaySeconds = clueDelaySeconds

        self.currentState = BotStates.START
        self.currentRound = None

    def _changeState(self, newState):
        if newState == self.currentState:
            return
        self.currentState = newState

    def _onStateStart(self):
        self.gameState = State(self.history_size)
        self.gameState.loadFromDisk()

        # Uncomment to check all images in the dataset before starting
        #self._load_dataset(self.datasetPath, check=True)

        self._changeState(BotStates.NEW_ROUND)

    def _load_dataset(self, path, check=False):
        '''Loads quiz questions from a directory.'''

        logger.info('Loading dataset...')
        definitions = glob.glob(os.path.join(path, '*.json'))
        logger.debug('Found %d definition files: %s', len(definitions), definitions)

        questions = []
        for d in definitions:
            try:
                logger.debug('Parsing %s...', d)
                q = load_definition_from_file(d)
                logger.debug(q)
                questions.append(q)

                if check:
                    logger.info('Checking %s', d)
                    img = ImageGame(q)
                    img.clean()
            except Exception as e:
                logger.error('Unable to parse %s', d)
                logger.error(e, exc_info=True)
                sys.exit(-1)

        logger.info('%d questions loaded successfully', len(questions))
        return questions

    def _pickQuestion(self, questions):
        return random.choice(questions)

    def _new_round(self):
        candidates = self._load_dataset(self.datasetPath)
        if not candidates:
            msg = 'Unable to find any question'
            logger.error(msg)
            raise ValueError(msg)

        question = self._pickQuestion(candidates)
        if len(candidates) > self.history_size:
            while question.filepath in self.gameState.getQuestions():
                logger.debug('Repeated question: %s', question.filepath)
                question = self._pickQuestion(candidates)

        logger.debug('Selected question: %s', question)
        return ImageGame(question)

    def _onStateNewRound(self):
        self.currentRound = self._new_round()
        self.postIds = set()
        self._changeState(BotStates.NEW_CLUE)

    def _publish_new_clue(self, current_game):
        clue = current_game.next_clue()
        if clue is None:
            return None
        num_clues = len(current_game.clues) + 1

        msg = strings.NEW_CLUE.format(current_game.clue_idx, num_clues)
        if current_game.clue_idx == num_clues:
            msg = strings.LAST_CLUE.format(current_game.clue_idx, num_clues)

        return self.mastodon_client.post_with_media(msg, clue)

    def _onStateNewClue(self):
        postId = self._publish_new_clue(self.currentRound)

        if postId is None:
            # No more clues for this round
            self._changeState(BotStates.FINISH_ROUND)
        else:
            self.postIds.add(postId)
            self.lastClueTime = datetime.now()
            self._changeState(BotStates.WAIT)

    def _checkOwnerCommands(self, response):
        text = response.content

        if '\\die' in text:
            logger.info('Found owner command: DIE')
            self._changeState(BotStates.FINISH_EXECUTION)
            return True

        if '\\solution_found' in text:
            logger.info('Found owner command: SOLUTION_FOUND')
            self._changeState(BotStates.SOLUTION_FOUND)
            return True

        if '\\finish' in text:
            logger.info('Found owner command: FINISH_ROUND')
            self._changeState(BotStates.FINISH_ROUND)
            return True

        if '\\next' in text:
            logger.info('Found owner command: NEW_CLUE')
            self._changeState(BotStates.NEW_CLUE)
            return True

        return False

    def _onStateCheckResponses(self):
        logger.info('Checking for responses...')
        responses = self.mastodon_client.get_responses()
        logger.debug('Received %d responses', len(responses))
        solutionFound = False
        commandFound = False

        for r in responses:
            if r.creator == self.owner:
                commandFound = self._checkOwnerCommands(r)
                if commandFound:
                    break

            if r.in_reply_to_id not in self.postIds:
                logging.debug('post_id = %s, postIds = %s', r.post_id, self.postIds)
                logging.info('Response not in current game posts')

            elif self.currentRound.is_valid(r.content):
                logging.info('Correct response!')
                # TODO like response
                solutionFound = True
            else:
                logging.info('Invalid response')

        if commandFound:
            return
        elif solutionFound:
            self._changeState(BotStates.SOLUTION_FOUND)
        elif enough_delay(self.clueDelaySeconds, self.lastClueTime):
            self._changeState(BotStates.NEW_CLUE)
        else:
            self._changeState(BotStates.WAIT)

    def _onStateFinishRound(self):
        solution = self.currentRound.get_solution()
        msg = strings.SOLUTION_NOT_FOUND.format(solution)
        self.mastodon_client.post_with_media(msg, self.currentRound.get_image())
        self.currentRound.clean()
        self._changeState(BotStates.NEW_ROUND)

    def _onStateSolutionFound(self):
        solution = self.currentRound.get_solution()
        msg = strings.SOLUTION_FOUND.format(solution)
        self.mastodon_client.post_with_media(msg, self.currentRound.get_image())
        self.currentRound.clean()
        self._changeState(BotStates.NEW_ROUND)

    def run(self):
        while True:
            self._runStep()

    def _runStep(self):
        logger.debug('Current state: %s', self.currentState)

        if self.currentState == BotStates.START:
            self._onStateStart()

        elif self.currentState == BotStates.WAIT:
            logger.info('Waiting...')
            time.sleep(self.checkDelaySeconds)
            self._changeState(BotStates.CHECK_RESPONSES)

        elif self.currentState == BotStates.NEW_ROUND:
            self._onStateNewRound()

        elif self.currentState == BotStates.NEW_CLUE:
            self._onStateNewClue()

        elif self.currentState == BotStates.CHECK_RESPONSES:
            self._onStateCheckResponses()

        elif self.currentState == BotStates.FINISH_ROUND:
            self._onStateFinishRound()

        elif self.currentState == BotStates.SOLUTION_FOUND:
            self._onStateSolutionFound()

        elif self.currentState == BotStates.FINISH_EXECUTION:
            logger.info('I have received the command to shut down myself')
            sys.exit(-1)
