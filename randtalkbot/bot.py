# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
import telepot
from .admin_handler import AdminHandler
from .stranger_handler import StrangerHandler
from telepot.delegate import per_chat_id
from telepot.async.delegate import create_open

LOGGER = logging.getLogger('randtalkbot.bot')

class Bot:
    def __init__(self, configuration, stranger_service):
        self._admins_telegram_ids = configuration.admins_telegram_ids
        self._delegator_bot = telepot.async.DelegatorBot(
            configuration.token,
            [
                (self._calculate_admin_seed, create_open(AdminHandler, stranger_service)),
                (self._calculate_stranger_seed, create_open(StrangerHandler, stranger_service)),
                ]
            )
        self._stranger_service = stranger_service

    def _calculate_admin_seed(self, message_json):
        telegram_id = message_json['chat']['id']
        # If the bot isn't chatting with an admin, skip, so for this chat will be used another handler,
        # not AdminHandler.
        return telegram_id if telegram_id in self._admins_telegram_ids else None

    def _calculate_stranger_seed(self, message_json):
        telegram_id = message_json['chat']['id']
        # If the bot is chatting with an admin, skip, so for this chat will be used another handler,
        # not StrangerHandler.
        return None if telegram_id in self._admins_telegram_ids else telegram_id

    @asyncio.coroutine
    def run(self):
        LOGGER.info('Listening')
        yield from self._delegator_bot.messageLoop()
