# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
import re
from .errors import StrangerError, StrangerServiceError
from .stranger import MissingPartnerError, SEX_NAMES
from .stranger_handler import StrangerHandler
from .stranger_service import StrangerService
from telepot import TelegramError

LOGGER = logging.getLogger('randtalkbot.admin_handler')

class AdminHandler(StrangerHandler):
    async def _handle_command_clear(self, message):
        someone_was_cleared = False
        for telegram_id in re.split(r'\s+', message.command_args):
            try:
                telegram_id = int(telegram_id)
            except (ValueError, TypeError):
                await self._sender.send_notification('Is it really telegram_id: \"{0}\"?', telegram_id)
                continue
            try:
                stranger = StrangerService.get_instance().get_stranger(telegram_id)
            except StrangerServiceError as e:
                await self._sender.send_notification('Stranger {0} wasn\'t found: {1}', telegram_id, e)
                continue
            await stranger.end_talk()
            await self._sender.send_notification('Stranger {0} was cleared', telegram_id)
            LOGGER.debug('Clear: %d -> %d', self._stranger.id, telegram_id)
            someone_was_cleared = True
        if not someone_was_cleared:
            await self._sender.send_notification('Use it this way: `/clear 31416 27183`')

    async def _handle_command_pay(self, message):
        try:
            match = re.match(
                r'^(?P<telegram_id>\d+)\s+(?P<delta>\d+)\s*(?P<gratitude>.*)$',
                message.command_args,
                )
        except (ValueError, TypeError):
            match = None
        if match:
            telegram_id = int(match.group('telegram_id'))
            delta = int(match.group('delta'))
        else:
            await self._sender.send_notification(
                'Please specify Telegram ID and bonus amount like this: `/pay 31416 10 Thanks!`',
                )
            return
        try:
            stranger = StrangerService.get_instance().get_stranger(telegram_id)
        except StrangerServiceError as e:
            await self._sender.send_notification('Stranger wasn\'t found: {0}', e)
            return
        await stranger.pay(delta, match.group('gratitude'))
        await self._sender.send_notification('Success.')
        LOGGER.debug('Pay: {} -({})-> {}'.format(self._stranger.id, delta, telegram_id))
