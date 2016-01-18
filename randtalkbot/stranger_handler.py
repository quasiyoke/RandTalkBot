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
from .utils import __version__

def _(s): return s

class MissingCommandError(Exception):
    pass

class StrangerHandlerError(Exception):
    pass

class StrangerHandler(telepot.helper.ChatHandler):
    COMMAND_RE_PATTERN = re.compile('^/(begin|end|help|setup|start)\\b')

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
            logging.error('Problems with StrangerHandler construction: %s', e)
            sys.exit('Problems with StrangerHandler construction: %s' % e)
        self._sender = StrangerSenderService.get_instance(bot) \
            .get_or_create_stranger_sender(self._stranger)
        self._stranger_setup_wizard = StrangerSetupWizard(self._stranger)

    @classmethod
    def _get_command(cls, message):
        command_match = cls.COMMAND_RE_PATTERN.match(message)
        if command_match:
            return command_match.group(1)
        else:
            raise MissingCommandError()

    @asyncio.coroutine
    def _handle_command(self, command):
        if command == 'start':
            yield from self._sender.send_notification(
                _('*Manual*\n\nUse /begin to start looking for a conversational partner, once '
                    'you\'re matched you can use /end to end the conversation.')
                )
            logging.debug('Start: %d', self._stranger.id)
        if command == 'begin':
            try:
                partner = self._stranger_service.get_partner(self._stranger)
            except PartnerObtainingError:
                yield from self._stranger.set_looking_for_partner()
                logging.debug('Looking for partner: %d', self._stranger.id)
            except StrangerServiceError as e:
                logging.error('Problems with handling /begin command: %s', e)
                sys.exit('Problems with handling /begin command: %s' % e)
            else:
                yield from self._stranger.set_partner(partner)
                yield from partner.set_partner(self._stranger)
                logging.debug('Found partner: %d -> %s.', self._stranger.id, partner.id)
        elif command == 'end':
            yield from self._stranger.end_chatting()
            logging.debug(
                'Finished chatting: %d -x-> %d',
                self._stranger.id,
                self._stranger.partner.id if self._stranger.partner else 0,
                )
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
            yield from self._stranger.end_chatting()
            yield from self._stranger_setup_wizard.activate()
            logging.debug('Setup: %d', self._stranger.id)

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
                    command = StrangerHandler._get_command(message_json['text'])
                except MissingCommandError:
                    try:
                        yield from self._stranger.send_to_partner(message)
                    except MissingPartnerError:
                        pass
                    except StrangerError:
                        yield from self._sender.send_notification(
                            _('Messages of this type aren\'t supported.'),
                            )
                else:
                    yield from self._handle_command(command)
        else:
            try:
                yield from self._stranger.send_to_partner(message)
            except MissingPartnerError:
                pass
            except StrangerError:
                yield from self._sender.send_notification(
                    _('Messages of this type aren\'t supported.'),
                    )
