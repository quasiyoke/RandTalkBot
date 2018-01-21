# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2018 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
from pprint import pformat
from telepot.exception import TelegramError

LOGGER = logging.getLogger('telepot_testing')
# pylint: disable=invalid-name
message_id_counter = 0
BOT_BLOCKERS_IDS = set()
SENT_FUTURES = []
UPDATES_FUTURES = []
UPDATES_TIMEOUT = 1

def add_bot_blockers_ids(*blockers_ids):
    BOT_BLOCKERS_IDS.update(blockers_ids)

async def assert_sent_message(chat_id, text, disable_notification=None, reply_markup=None):
    expected_update = {
        'chat': {
            'id': chat_id,
            },
        'text': text,
        }

    if disable_notification is not None:
        expected_update['disable_notification'] = disable_notification

    if reply_markup is not None:
        expected_update['reply_markup'] = reply_markup

    await assert_sent_update(expected_update)

async def assert_sent_inline_query_response(
        query_id,
        response,
        is_personal=None,
    ):
    expected_update = {
        'query_id': query_id,
        'is_personal': is_personal,
        'response': response,
        }

    await assert_sent_update(expected_update)

async def assert_sent_update(expected_update):
    async def get_sent_update():
        try:
            future = SENT_FUTURES[0]
        except IndexError:
            pass
        else:
            if future.done():
                SENT_FUTURES.pop(0)
                return future.result()

        future = asyncio.Future()
        SENT_FUTURES.append(future)
        LOGGER.debug('Waiting for sent update')

        try:
            await asyncio.wait_for(future, timeout=UPDATES_TIMEOUT)
        except asyncio.TimeoutError:
            SENT_FUTURES.remove(future)
            raise AssertionError(
                f'No updates were sent while we did expect `{expected_update_repr}`',
                )
        # pylint: disable=bare-except
        except:
            SENT_FUTURES.remove(future)
            LOGGER.exception('Exception during waiting for sent updates')
            raise
        else:
            SENT_FUTURES.remove(future)
            return future.result()

    def equals(actual, expected):
        if hasattr(expected, 'match'):
            return bool(expected.match(actual))
        elif isinstance(expected, dict):
            if not isinstance(actual, dict) or list(actual.keys()) != list(expected.keys()):
                return False

            for key, value in expected.items():
                if not equals(actual[key], value):
                    return False

            return True
        else:
            return actual == expected

    expected_update_repr = pformat(expected_update)
    actual_update = await get_sent_update()
    actual_update_repr = pformat(actual_update)

    if not equals(actual_update, expected_update):
        reason = f'Expected sent update `{actual_update_repr}`' \
            f'\nto be equal `{expected_update_repr}`'
        LOGGER.error(reason)
        raise AssertionError(reason)

async def finalize():
    LOGGER.debug('Finalizing')
    BOT_BLOCKERS_IDS.clear()

    try:
        if UPDATES_FUTURES:
            raise AssertionError('Updates\' futures weren\'t awaited')

        for future in SENT_FUTURES:
            if future.done():
                result = future.result()
                raise AssertionError(f'Sent future wasn\'t awaited: {result}')
    finally:
        SENT_FUTURES.clear()
        UPDATES_FUTURES.clear()

def get_first_not_done_future(futures):
    for future in futures:
        if not future.done():
            return future

    future = asyncio.Future()
    futures.append(future)
    return future

async def get_update():
    LOGGER.debug('Waiting for received updates')

    try:
        future = UPDATES_FUTURES[0]
    except IndexError:
        future = asyncio.Future()
        UPDATES_FUTURES.append(future)

    try:
        await asyncio.wait_for(future, timeout=UPDATES_TIMEOUT)
    except asyncio.TimeoutError:
        return None
    except asyncio.CancelledError:
        LOGGER.debug('Cancelled')
        raise
    # pylint: disable=bare-except
    except:
        LOGGER.exception('Exception during waiting for updates')
        raise
    else:
        return future.result()
    finally:
        UPDATES_FUTURES.remove(future)

def receive_update(update):
    get_first_not_done_future(UPDATES_FUTURES).set_result(update)

def receive_message(chat_id, text, is_edit=False, reply_to_message=None):
    # pylint: disable=global-statement
    global message_id_counter
    message_id_counter += 1
    update = {
        'message_id': message_id_counter,
        'chat': {
            'id': chat_id,
            'type': 'private',
            },
        'from': {
            'id': chat_id,
            },
        'text': text,
        }

    if is_edit:
        update['edit_date'] = 1517068580

    if reply_to_message is not None:
        update['reply_to_message'] = reply_to_message

    receive_update(update)

def receive_inline_query(chat_id, query_id, text):
    receive_update({
        'id': query_id,
        'chat': {
            'id': chat_id,
            'type': 'private',
            },
        'from': {
            'id': chat_id,
            },
        'query': text,
        })

def send_update(update):
    """Raises:
        TelegramError: If user has blocked the bot.

    """
    telegram_id = update['chat']['id']

    if telegram_id in BOT_BLOCKERS_IDS:
        reason = f'User with Telegram ID {telegram_id} has blocked the bot'
        LOGGER.info(reason)
        bot_was_blocked_code = 403
        raise TelegramError(reason, bot_was_blocked_code, {'reason': reason})

    LOGGER.debug(
        'Futures count: %d. Sending update to some (probably new) future: %s',
        len(SENT_FUTURES),
        update,
        )
    get_first_not_done_future(SENT_FUTURES) \
        .set_result(update)
