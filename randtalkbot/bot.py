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
from telepot.delegate import per_from_id_in, per_from_id_except
from telepot.aio.delegate import create_open

LOGGER = logging.getLogger('randtalkbot.bot')


class Bot:
    def __init__(self, configuration):
        self._admins_telegram_ids = configuration.admins_telegram_ids
        self._delegator_bot = telepot.aio.DelegatorBot(
            configuration.token,
            [
                # If the bot isn't chatting with an admin, skip, so for this
                # chat will be used another handler, not AdminHandler.
                (per_from_id_in(self._admins_telegram_ids), create_open(
                    AdminHandler,
                    timeout=60,
                    )),
                # If the bot is chatting with an admin, skip, so for this chat
                # will be used another handler, not StrangerHandler.
                (per_from_id_except(self._admins_telegram_ids), create_open(
                    StrangerHandler,
                    timeout=60,
                    )),
                ],
            )

    async def run(self):
        LOGGER.info('Listening')
        await self._delegator_bot.message_loop()
