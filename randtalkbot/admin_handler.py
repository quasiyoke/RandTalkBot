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

class AdminHandler(StrangerHandler):
    COMMANDS = StrangerHandler.COMMANDS + ['clear']

    @asyncio.coroutine
    def handle_command(self, command, args=None):
        if command == 'clear':
            try:
                telegram_id = int(args)
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
            logging.debug('Clear: %d -> %d', self._stranger.id, telegram_id)
        else:
            yield from super(AdminHandler, self).handle_command(command, args)
