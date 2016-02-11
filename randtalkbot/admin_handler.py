# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
import re
from .stranger import MissingPartnerError, SEX_NAMES, StrangerError
from .stranger_handler import StrangerHandler
from .stranger_service import StrangerServiceError
from telepot import TelegramError

LOGGER = logging.getLogger('randtalkbot')

class AdminHandler(StrangerHandler):
    @asyncio.coroutine
    def _handle_command_clear(self, message):
        try:
            telegram_id = int(message.command_args)
        except (ValueError, TypeError):
            yield from self._sender.send_notification('Please specify Telegram ID like this: /clear 31416')
            return
        try:
            stranger = self._stranger_service.get_stranger(telegram_id)
        except StrangerServiceError as e:
            yield from self._sender.send_notification('Stranger wasn\'t found: {0}', e)
            return
        yield from stranger.end_chatting()
        yield from self._sender.send_notification('Stranger was cleared.')
        LOGGER.debug('Clear: %d -> %d', self._stranger.id, telegram_id)

    @asyncio.coroutine
    def _handle_command_pay(self, message):
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
            yield from self._sender.send_notification(
                'Please specify Telegram ID and bonus amount like this: `/pay 31416 10 Thanks!`',
                )
            return
        try:
            stranger = self._stranger_service.get_stranger(telegram_id)
        except StrangerServiceError as e:
            yield from self._sender.send_notification('Stranger wasn\'t found: {0}', e)
            return
        yield from stranger.pay(delta, match.group('gratitude'))
        yield from self._sender.send_notification('Success.')
        LOGGER.debug('Clear: %d -> %d', self._stranger.id, telegram_id)
