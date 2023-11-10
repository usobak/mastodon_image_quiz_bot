'''Wrapper to encapsulate the Mastodon client  with a simpler interface.

FakeMastodonWrapper can be instantiated to have a simulated Mastodon client.
'''

import logging
import random

from mastodon import Mastodon
from mastodon.errors import MastodonServiceUnavailableError

from .util import retry

logger = logging.getLogger(__name__)


class FakeMastodonWrapper:
    '''Fake wrapper for testing. Simulates calling Mastodon.'''

    def __init__(self):
        self.lastId = 1

    def post_with_media(self, msg, filepath):
        '''Simulates the post of an image. Returns random post id'''

        #if random.random() < 0.1:  # Fail 10% of the time
        #    logger.info('Throwing fake error')
        #    raise MastodonServiceUnavailableError('Fake error!')
        logger.info('Posting message "%s" filepath "%s"', msg, filepath)
        logger.info('Returning random postId')
        self.lastId = int(1000000*random.random())
        return self.lastId


    def get_responses(self):
        '''Simulates that some responses have been received.'''

        logger.info('Returning fake response')
        return [
            Response(post_id=1,  in_reply_to_id=self.lastId, content='response 1'),
            Response(post_id=2,  in_reply_to_id=self.lastId, content='stray')
        ]


class MastodonWrapper:
    '''Wrapper for the Mastodon client.'''

    # TODO inject mastodon dependency
    def __init__(self, api_url, token, visibility):
        self.visibility = visibility

        self.mastodon = Mastodon(
            access_token=token,
            api_base_url=api_url)


    @retry(times=10)
    def post_with_media(self, msg, filepath):
        '''Creates a post with an image.'''

        upload_result = self.mastodon.media_post(media_file=filepath)
        media_id = upload_result['id']
        logger.info('Uploaded media with id %s', media_id)

        post_result = self.mastodon.status_post(
                msg, media_ids=[media_id], visibility=self.visibility)
        post_id = post_result['id']
        logger.info('Published post with id %s', post_id)
        return post_id


    @retry(times=10)
    def get_responses(self):
        '''Returns the list of all mentions to the bot as Response instances.'''

        request_result = self.mastodon.notifications(types=['mention'])
        statuses = [r['status'] for r in request_result]
        logger.info('Found %d new notifications', len(statuses))
        logger.debug(statuses)
        responses = [parse_response(r) for r in statuses]
        logger.info('Responses: %s', responses)

        logger.info('Clearing notifications...')
        self.mastodon.notifications_clear()

        return responses


class Response:
    '''Encapsulates a response to the quiz.'''

    def __init__(self, post_id=None, in_reply_to_id=None, content=None,
                 creator=None):
        self.post_id = post_id
        self.in_reply_to_id = in_reply_to_id
        self.content = content
        self.creator = creator
        self.bots_allowed = True

    def __str__(self):
        return f'Response({self.post_id}, {self.creator}, {self.in_reply_to_id}, {self.content})'


def parse_response(result):
    '''Converts a notification message from Mastodon into a Response object.'''

    r = Response()
    r.post_id = result['id']
    r.in_reply_to_id = result['in_reply_to_id']
    r.content = result['content']
    r.creator = result['account']['acct']

    note = result['account']['note']
    if '#nobot' in note:
        r.bots_allowed = False

    return r
