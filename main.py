#!/usr/bin/env python3

'''
Mastodon bot for image-based quizes.

See Readme.md for more info on how to setup and run it.
'''

import argparse
import logging
import os
import random
import sys

from bot.manager import BotManager
from bot.mastodon_wrapper import MastodonWrapper, FakeMastodonWrapper

logger = logging.getLogger(__name__)

# Default arguments
DEFAULT_DATASET_PATH = './dataset/'
DEFAULT_OUTPUT_PATH = './output/'
DEFAULT_CLUE_DELAY_SECONDS = 60 * 60 * 2
DEFAULT_CHECK_DELAY_SECONDS = 60 * 5
DEFAULT_MASTODON_VISIBILITY = 'public'

TOKEN_ENVIRON_VAR = 'MASTODON_TOKEN'


def get_auth_token():
    '''Fetches the auth token from the env var.'''
    try:
        token = os.environ[TOKEN_ENVIRON_VAR].strip()
        if not token:
            raise ValueError()
        return token
    except Exception as e:
        logging.error('Unable to get the auth token for Mastodon')
        logging.error(e, exc_info=True)
        sys.exit(-1)


def main():
    '''Setup and run the bot.'''

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
        handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()],
    )

    parser = argparse.ArgumentParser(
        prog="Quiz Bot", description="Mastodon bot for image-based quizs"
    )
    parser.add_argument('-d', '--dataset', default=DEFAULT_DATASET_PATH)
    parser.add_argument('-o', '--output', default=DEFAULT_OUTPUT_PATH)
    parser.add_argument('--no_dry_run', action='store_false')
    parser.add_argument(
        '--clue_delay_seconds', default=DEFAULT_CLUE_DELAY_SECONDS, type=int
    )
    parser.add_argument(
        '--check_delay_seconds', default=DEFAULT_CHECK_DELAY_SECONDS, type=int
    )
    parser.add_argument('--mastodon_endpoint')
    parser.add_argument('--mastodon_owner')
    parser.add_argument('--mastodon_visibility', default=DEFAULT_MASTODON_VISIBILITY)
    args = parser.parse_args()

    logger.info('Starting the bot...')
    logger.info('dataset = %s', args.dataset)
    logger.info('output = %s', args.output)
    logger.info('no dry run? = %s', args.no_dry_run)
    logger.info('clue delay in seconds = %d', args.clue_delay_seconds)
    logger.info('check delay in seconds = %d', args.check_delay_seconds)
    logger.info('mastodon endpoint = %s', args.mastodon_endpoint)
    logger.info('mastodon owner = %s', args.mastodon_owner)
    logger.info('mastodon visibility = %s', args.mastodon_visibility)

    logger.info('Setting up dependencies and data...')
    random.seed()

    if args.no_dry_run:
        logger.info("Dry run mode. Won't publish anything!")
        mastodon_client = FakeMastodonWrapper()
    else:
        token = get_auth_token()
        mastodon_client = MastodonWrapper(
            api_url=args.mastodon_endpoint,
            token=token,
            visibility=args.mastodon_visibility,
        )
        del os.environ[TOKEN_ENVIRON_VAR]
        del token

    bot = BotManager(
        mastodon_client,
        args.mastodon_owner,
        args.dataset,
        clueDelaySeconds=args.clue_delay_seconds,
        checkDelaySeconds=args.check_delay_seconds,
    )

    logger.info('Running game...')
    try:
        bot.run()
    except Exception as e:
        logging.error('UNHANDLED EXCEPTION')
        logging.error(e, exc_info=True)
        logging.info('Shutting down...')
        sys.exit(-1)


if __name__ == '__main__':
    main()
