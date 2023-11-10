import json
import logging

logger = logging.getLogger(__name__)

DEFAULT_STATE_FILENAME = 'state.json'


class State:
    def __init__(self, history_size=50):
        self.history = []
        self.history_size = history_size

    def addQuestion(self, question):
        self.history.append(question)
        while len(self.history) > self.history_size:
            self.history_size.pop(0)
        self.saveToDisk()

    def getQuestions(self):
        return self.history

    def saveToDisk(self, filename=DEFAULT_STATE_FILENAME):
        state = {'history': self.history}
        with open(filename, 'w') as fout:
            json.dump(state, fout)
        logger.info('Stated saved')
        print('Saved state')

    def loadFromDisk(self, filename=DEFAULT_STATE_FILENAME):
        try:
            with open(filename) as fin:
                state = json.load(fin)
                self.history = state['history']
            logger.info('State loaded')
        except Exception as e:
            logger.error(f'Failed to load {filename}. Using clean state...')
            logging.error(e, exc_info=True)
