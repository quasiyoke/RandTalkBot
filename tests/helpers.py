# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2018 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import datetime
from functools import wraps
import logging
from asynctest.mock import patch, Mock
from peewee import SqliteDatabase
from randtalkbot import stats, stranger, talk
from randtalkbot.bot import Bot
from randtalkbot.stats import Stats
from randtalkbot.stranger import Stranger
from randtalkbot.stranger_service import StrangerService
from randtalkbot.talk import Talk
from randtalkbot.stats_service import StatsService
import telepot_testing
from telepot_testing import finalize as finalize_telepot

LOGGER = logging.getLogger('tests.helpers')
TIME_TOLERANCE = datetime.timedelta(seconds=.1)

def assert_db(db_dict):
    def assert_model(model, model_dict):
        def raise_assertion_error(key, actual_value, expected_value):
            raise AssertionError(
                f'Value of `{key}` is `{actual_value}` but should be `{expected_value}`',
                )

        for key, expected_value in model_dict.items():
            actual_value = getattr(model, key)

            if isinstance(expected_value, datetime.datetime):
                if abs(actual_value - expected_value) > TIME_TOLERANCE:
                    raise_assertion_error(key, actual_value, expected_value)
            elif hasattr(expected_value, 'match'): # Regular expression pattern.
                if expected_value.match(actual_value) is None:
                    raise AssertionError(
                        f'Value of `{key}` is `{actual_value}` and doesn\'t match'
                        f' `{expected_value}`',
                        )
            elif actual_value != expected_value:
                raise_assertion_error(key, actual_value, expected_value)

    for model_name, models_dicts in db_dict.items():
        if model_name == 'strangers':
            for stranger_dict in models_dicts:
                stranger_instance = Stranger.get(id=stranger_dict['id'])
                assert_model(stranger_instance, stranger_dict)
        elif model_name == 'talks':
            for talk_dict in models_dicts:
                talk_instance = Talk.get(id=talk_dict['id'])
                assert_model(talk_instance, talk_dict)
        else:
            raise AssertionError(f'Unknown model name: `{model_name}`')

def get_configuration_mock():
    configuration = Mock()
    configuration.admins_telegram_ids = []
    return configuration

def run(ctx):
    debug = False

    if debug:
        logging.basicConfig(
            format='%(asctime)s %(name)s:%(funcName)s - %(message)s',
            level=logging.DEBUG,
            )

    bot = Bot(get_configuration_mock())
    loop = asyncio.get_event_loop()
    ctx.task = loop.create_task(bot.run())

    ctx.database = SqliteDatabase(':memory:')
    stats.DATABASE_PROXY.initialize(ctx.database)
    stranger.DATABASE_PROXY.initialize(ctx.database)
    talk.DATABASE_PROXY.initialize(ctx.database)
    ctx.database.create_tables([Stats, Stranger, Talk])

    StatsService()
    StrangerService.get_instance() \
        ._strangers_cache \
        .clear()

def finalize(ctx):
    ctx.database.drop_tables([Stranger, Talk])

    for task in asyncio.Task.all_tasks():
        task.cancel()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(finalize_telepot())
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()

def patch_telepot(function):
    @patch('randtalkbot.bot.create_open', telepot_testing.aio.create_open)
    @patch('randtalkbot.bot.telepot', telepot_testing)
    @patch('randtalkbot.bot.telepot.aio.DelegatorBot', telepot_testing.aio.DelegatorBot)
    @wraps(function)
    def result(*args, **kwargs):
        return function(*args, **kwargs)

    return result

def setup_db(db_dict):
    strangers_dicts = db_dict.get('strangers')

    if strangers_dicts:
        for stranger_dict in strangers_dicts:
            Stranger.create(**stranger_dict)

    talks_dicts = db_dict.get('talks')

    if talks_dicts:
        for talk_dict in talks_dicts:
            Talk.create(**talk_dict)
