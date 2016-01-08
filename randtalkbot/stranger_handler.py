# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
import re
import telepot
from .stranger import MissingPartnerError
from .stranger_service import PartnerObtainingError

MANUAL = '''Use /begin to start looking for a conversational partner, once you're matched you \
can use /end to end the conversation.'''

HELP_PATTERN = MANUAL + '''

If you have any suggestions or require help, please contact @quasiyoke. When asking questions, please \
provide this number: {0}

You're welcome to inspect and improve [Rand Talk's source code.](https://github.com/quasiyoke/RandTalkBot)
'''

class MissingCommandError(Exception):
    pass

class UnsupportedContentError(Exception):
    pass

class StrangerHandler(telepot.helper.ChatHandler):
    COMMAND_RE_PATTERN = re.compile('^/(begin|end|help|start)\\b')

    CONTENT_TYPE_TO_METHOD_NAME = {
        'text': 'sendMessage',
        'photo': 'sendPhoto',
        }

    def __init__(self, seed_tuple, stranger_service):
        super(StrangerHandler, self).__init__(seed_tuple, None)
        self._stranger_service = stranger_service
        self._stranger = self._stranger_service.get_or_create_stranger(self.chat_id, self)

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
        if command == 'begin':
            try:
                yield from self._stranger_service.set_partner(self._stranger)
            except PartnerObtainingError:
                pass
        elif command == 'end':
            yield from self._stranger.end_chatting()
        elif command == 'help':
            yield from self.send_notification('*Help*\n\n' + HELP_PATTERN.format(self.chat_id))
        elif command == 'start':
            yield from self.send_notification('*Manual*\n\n' + MANUAL)

    @asyncio.coroutine
    def send_notification(self, message):
        yield from self.sender.sendMessage('*Rand Talk:* {0}'.format(message), parse_mode='Markdown')

    @asyncio.coroutine
    def on_message(self, message):
        content_type, chat_type, chat_id = telepot.glance2(message)

        if chat_type != 'private':
            return

        try:
            content_kwargs = StrangerHandler._get_content_kwargs(message, content_type)
        except UnsupportedContentError:
            yield from self.send_notification('Messages of this type weren\'t supported.')
            return
        if content_type == 'text':
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
                yield from self.send_notification('Messages of this type weren\'t supported.')

    @asyncio.coroutine
    def send(self, content_type, content_kwargs):
        try:
            method_name = StrangerHandler.CONTENT_TYPE_TO_METHOD_NAME[content_type]
        except KeyError:
            raise UnsupportedContentError()
        else:
            yield from getattr(self.sender, method_name)(**content_kwargs)
