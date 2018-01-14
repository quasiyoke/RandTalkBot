# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2018 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
from asyncio import Queue
import logging
from unittest.mock import Mock
from asynctest.mock import CoroutineMock
from telepot_testing.helpers import get_update, send_update, UPDATES_TIMEOUT
from telepot.helper import Microphone

LOGGER = logging.getLogger('telepot_testing.aio')

def create_open(cls, *args, **kwargs):
    def get_future(seed_tuple):
        """Args:
            seed_tuple (tuple): bot, update, seed

        Returns:
            Future: Future awaiting for received updates.
        """
        async def wait_loop():
            LOGGER.debug('Handler\'s first call: %s', update)
            await handler.on_message(update)

            while True:
                next_update = await handler.listener.wait()

                if next_update is None:
                    LOGGER.debug('No update was received')
                    break

                LOGGER.debug('Update %s was awaited', next_update)
                await handler.on_message(next_update)

        handler = cls(seed_tuple, *args, **kwargs)
        unused_bot, update, unused_seed = seed_tuple
        return wait_loop()

    return get_future

class Listener:
    def __init__(self, microphone, queue):
        self.capture = Mock()
        self._microphone = microphone
        self._queue = queue

    async def wait(self):
        LOGGER.debug('Waiting for received update')

        try:
            update = await asyncio.wait_for(self._queue.get(), timeout=UPDATES_TIMEOUT)
        except asyncio.TimeoutError:
            LOGGER.debug('No received update was awaited in listener')
            return None

        LOGGER.debug('Received update was awaited in the listener %s', update)
        return update

class DelegatorBot:
    coroutines = [
        'forwardMessage',
        'sendPhoto',
        'sendAudio',
        'sendDocument',
        'sendSticker',
        'sendVideo',
        'sendVoice',
        'sendVideoNote',
        'sendLocation',
        'sendVenue',
        'sendContact',
        'sendGame',
        'sendChatAction',
        'sendMediaGroup',
        ]

    def __init__(self, unused_token, delegate_records):
        self._delegate_records = [record + ({},) for record in delegate_records]
        self._microphone = Microphone()
        self.scheduler = Mock()
        self._loop = asyncio.get_event_loop()

        for method in self.coroutines:
            setattr(self, method, CoroutineMock())

    def create_listener(self):
        queue = Queue()
        self._microphone.add(queue)
        listener = Listener(self._microphone, queue)
        return listener

    async def handle(self, update):
        LOGGER.debug('Sending to the microphone %s', update)
        self._microphone.send(update)

        for calculate_seed, get_future, cache in self._delegate_records:
            seed = calculate_seed(update)

            if seed is None:
                continue

            if seed not in cache or cache[seed].done():
                future = get_future((self, update, seed))
                cache[seed] = future
                self._loop.create_task(future)

    async def message_loop(self):
        while True:
            update = await get_update()
            await self.handle(update)

    # pylint: disable=invalid-name,too-many-arguments,unused-argument
    async def sendMessage(
            self,
            chat_id,
            text,
            disable_notification=None,
            disable_web_page_preview=None,
            parse_mode=None,
            reply_markup=None,
        ):
        update = {
            'chat': {
                'id': chat_id,
                },
            'text': text,
            }

        if disable_notification is not None:
            update['disable_notification'] = disable_notification

        if reply_markup is not None:
            update['reply_markup'] = reply_markup

        send_update(update)
