# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
import re
import sys
import telepot
from .i18n import get_languages_codes, LanguageNotFoundError, SUPPORTED_LANGUAGES_NAMES
from .message import Message, UnsupportedContentError
from .stranger import MissingPartnerError, SEX_NAMES, StrangerError
from .stranger_sender import StrangerSender
from .stranger_sender_service import StrangerSenderService
from .stranger_service import PartnerObtainingError, StrangerServiceError
from .stranger_setup_wizard import StrangerSetupWizard
from telepot import TelegramError
from .utils import __version__

LOGGER = logging.getLogger('randtalkbot')

def _(s): return s

class MissingCommandError(Exception):
    pass

class StrangerHandlerError(Exception):
    pass

class UnknownCommandError(Exception):
    def __init__(self, command):
        super(UnknownCommandError, self).__init__()
        self.command = command

class StrangerHandler(telepot.helper.ChatHandler):
    COMMAND_RE_PATTERN = re.compile('^/(\w+)\\b\s*(.*)$')
    COMMANDS = ['begin', 'end', 'help', 'setup', 'start', ]

    def __init__(self, seed_tuple, stranger_service):
        '''
        Most of this constructor's code were copied from telepot.helper.ChatHandler and
        its superclasses to inject stranger_sender_service.
        '''
        bot, initial_msg, seed = seed_tuple
        telepot.helper.ListenerContext.__init__(self, bot, seed)
        chat_id = initial_msg['chat']['id']
        self._chat_id = chat_id
        self.listener.set_options()
        self.listener.capture(chat__id=chat_id)
        self._stranger_service = stranger_service
        try:
            self._stranger = self._stranger_service.get_or_create_stranger(self.chat_id)
        except StrangerServiceError as e:
            LOGGER.error('Problems with StrangerHandler construction: %s', e)
            sys.exit('Problems with StrangerHandler construction: %s' % e)
        self._sender = StrangerSenderService.get_instance(bot) \
            .get_or_create_stranger_sender(self._stranger)
        self._stranger_setup_wizard = StrangerSetupWizard(self._stranger)

    @classmethod
    def _get_command(cls, message):
        command_match = cls.COMMAND_RE_PATTERN.match(message)
        if not command_match:
            raise MissingCommandError()
        command = command_match.group(1)
        args = command_match.group(2)
        if command not in cls.COMMANDS:
            raise UnknownCommandError(command)
        return command, args

    @asyncio.coroutine
    def handle_command(self, command, args=None):
        if command == 'start':
            LOGGER.debug('Start: %d', self._stranger.id)
            yield from self._sender.send_notification(
                _('*Manual*\n\nUse /begin to start looking for a conversational partner, once '
                    'you\'re matched you can use /end to end the conversation.')
                )
        elif command == 'begin':
            try:
                partner = None
                while not partner:
                    partner = self._stranger_service.get_partner(self._stranger)
                    try:
                        yield from partner.set_partner(self._stranger)
                    except StrangerError:
                        # Potential partner has blocked the bot. Let's look for next potential partner.
                        partner = None
                    else:
                        try:
                            yield from self._stranger.set_partner(partner)
                        except StrangerError:
                            # Stranger has blocked the bot. Forgive him, clear his potential partner and exit
                            # the cycle.
                            yield from partner.set_looking_for_partner()
                        else:
                            LOGGER.debug('Found partner: %d -> %d.', self._stranger.id, partner.id)
            except PartnerObtainingError:
                LOGGER.debug('Looking for partner: %d', self._stranger.id)
                yield from self._stranger.set_looking_for_partner()
            except StrangerServiceError as e:
                LOGGER.error('Problems with handling /begin command for %d: %s', self._stranger.id, str(e))
                yield from self._sender.send_notification(
                    _('Internal error. Admins are already notified about that'),
                    )
        elif command == 'end':
            LOGGER.debug(
                'Finished chatting: %d -x-> %d',
                self._stranger.id,
                self._stranger.partner.id if self._stranger.partner else 0,
                )
            yield from self._stranger.end_chatting()
        elif command == 'help':
            yield from self._sender.send_notification(
                _('*Help*\n\nUse /begin to start looking for a conversational partner, once '
                    'you\'re matched you can use /end to end the conversation.\n\nIf you have any '
                    'suggestions or require help, please contact @quasiyoke. When asking questions, '
                    'please provide this number: {0}\n\nYou\'re welcome to inspect and improve '
                    '[Rand Talk\'s source code.](https://github.com/quasiyoke/RandTalkBot)\n\n'
                    'version {1}'),
                    self.chat_id,
                    __version__,
                )
        elif command == 'setup':
            LOGGER.debug('Setup: %d', self._stranger.id)
            yield from self._stranger.end_chatting()
            yield from self._stranger_setup_wizard.activate()

    @asyncio.coroutine
    def on_message(self, message_json):
        content_type, chat_type, chat_id = telepot.glance2(message_json)

        if chat_type != 'private':
            return

        try:
            message = Message(message_json)
        except UnsupportedContentError:
            yield from self._sender.send_notification(_('Messages of this type aren\'t supported.'))
            return

        if content_type == 'text':
            if not (yield from self._stranger_setup_wizard.handle(message_json['text'])):
                try:
                    command, args = type(self)._get_command(message_json['text'])
                except MissingCommandError:
                    try:
                        yield from self._stranger.send_to_partner(message)
                    except MissingPartnerError:
                        pass
                    except StrangerError:
                        yield from self._sender.send_notification(
                            _('Messages of this type aren\'t supported.'),
                            )
                    except TelegramError:
                        LOGGER.warning(
                            'Send text. Can\'t send to partned: %d -> %d',
                            self._stranger.id,
                            self._stranger.partner.id,
                            )
                        yield from self._sender.send_notification(
                            _('Your partner has blocked me! How did you do that?!'),
                            )
                        self._stranger.end_chatting()
                except UnknownCommandError as e:
                    yield from self._sender.send_notification(
                        _('Unknown command. Look /help for the full list of commands.'),
                        )
                else:
                    yield from self.handle_command(command, args)
        else:
            try:
                yield from self._stranger.send_to_partner(message)
            except MissingPartnerError:
                pass
            except StrangerError:
                yield from self._sender.send_notification(_('Messages of this type aren\'t supported.'))
            except TelegramError:
                LOGGER.warning(
                    'Send media. Can\'t send to partned: %d -> %d',
                    self._stranger.id,
                    self._stranger.partner.id,
                    )
                yield from self._sender.send_notification(
                    _('Your partner has blocked me! How did you do that?!'),
                    )
                self._stranger.end_chatting()
