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
from .stranger import MissingPartnerError, SEX_NAMES
from .stranger_sender import StrangerSender
from .stranger_sender_service import StrangerSenderService
from .stranger_service import PartnerObtainingError, StrangerServiceError
from .stranger_setup_wizard import StrangerSetupWizard
from .utils import __version__

MANUAL = '''Use /begin to start looking for a conversational partner, once you're matched you \
can use /end to end the conversation.'''

HELP_PATTERN = MANUAL + '''

If you have any suggestions or require help, please contact @quasiyoke. When asking questions, please \
provide this number: {0}

You're welcome to inspect and improve [Rand Talk's source code.](https://github.com/quasiyoke/RandTalkBot)

version {1}
'''

class MissingCommandError(Exception):
    pass

class StrangerHandlerError(Exception):
    pass

class UnsupportedContentError(Exception):
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
        self._sender = StrangerSenderService.get_instance(bot).get_or_create_stranger_sender(chat_id)
        self.listener.set_options()
        self.listener.capture(chat__id=chat_id)
        self._stranger_service = stranger_service
        try:
            self._stranger = self._stranger_service.get_or_create_stranger(self.chat_id)
        except StrangerServiceError as e:
            logging.error('Problems with StrangerHandler construction: %s', e)
            sys.exit('Problems with StrangerHandler construction: %s' % e)
        self._stranger_setup_wizard = StrangerSetupWizard(self._stranger)

    @classmethod
    def _get_command(cls, message):
        command_match = cls.COMMAND_RE_PATTERN.match(message)
        if command_match:
            return command_match.group(1)
        else:
            raise MissingCommandError()

    @classmethod
    def _get_content_kwargs(cls, message, content_type):
        if content_type == 'text':
            try:
                content_kwargs = {
                    'text': message['text'],
                    }
            except KeyError:
                raise UnsupportedContentError()
            if 'reply_to_message' in message:
                raise UnsupportedContentError()
            return content_kwargs
        elif content_type == 'photo':
            try:
                content_kwargs = {
                    'photo': message['photo'][-1]['file_id'],
                    }
            except KeyError:
                raise UnsupportedContentError()
            try:
                content_kwargs['caption'] = message['caption']
            except KeyError:
                pass
            if 'reply_to_message' in message:
                raise UnsupportedContentError()
            return content_kwargs
        else:
            raise UnsupportedContentError()

    @asyncio.coroutine
    def _handle_command(self, command):
        if command == 'start':
            yield from self._sender.send_notification('*Manual*\n\n' + MANUAL)
        if command == 'begin':
            try:
                partner = self._stranger_service.get_partner(self._stranger)
            except PartnerObtainingError:
                yield from self._stranger.set_looking_for_partner()
            except StrangerServiceError as e:
                logging.error('Problems with handling /begin command: %s', e)
                sys.exit('Problems with handling /begin command: %s' % e)
            else:
                yield from self._stranger.set_partner(partner)
                yield from partner.set_partner(self._stranger)
        elif command == 'end':
            yield from self._stranger.end_chatting()
        elif command == 'help':
            yield from self._sender.send_notification(
                '*Help*\n\n' + HELP_PATTERN.format(self.chat_id, __version__),
                )
        elif command == 'setup':
            yield from self._stranger_setup_wizard.activate()

    @asyncio.coroutine
    def on_message(self, message):
        content_type, chat_type, chat_id = telepot.glance2(message)

        if chat_type != 'private':
            return

        try:
            content_kwargs = StrangerHandler._get_content_kwargs(message, content_type)
        except UnsupportedContentError:
            yield from self._sender.send_notification('Messages of this type aren\'t supported.')
            return
        if content_type == 'text':
            if not (yield from self._stranger_setup_wizard.handle(message['text'])):
                try:
                    yield from self._handle_command(StrangerHandler._get_command(message['text']))
                except MissingCommandError:
                    try:
                        yield from self._stranger.send_to_partner(content_type, content_kwargs)
                    except MissingPartnerError:
                        pass
        else:
            try:
                yield from self._stranger.send_to_partner(content_type, content_kwargs)
            except MissingPartnerError:
                pass
            except UnsupportedContentError:
                yield from self._sender.send_notification('Messages of this type aren\'t supported.')
