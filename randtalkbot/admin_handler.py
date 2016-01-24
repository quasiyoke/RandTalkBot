# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
from .stranger import MissingPartnerError, SEX_NAMES, StrangerError
from .stranger_handler import StrangerHandler
from .stranger_service import StrangerServiceError

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
