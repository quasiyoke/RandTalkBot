# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
import telepot
from .stranger_handler import StrangerHandler
from telepot.delegate import per_chat_id
from telepot.async.delegate import create_open

class Bot:
    def __init__(self, configuration, stranger_service):
        self._delegator_bot = telepot.async.DelegatorBot(
            configuration.token,
            [
                (per_chat_id(), create_open(StrangerHandler, stranger_service)),
                ]
            )
        self._stranger_service = stranger_service

    def start_listening(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self._delegator_bot.messageLoop())
        logging.info('Listening...')
        loop.run_forever()
