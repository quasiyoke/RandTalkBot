# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import re
import telepot

HELP_PATTERN = '''*Manual*

Use /begin to start looking for a conversational partner, once you're matched you can use /end to end the conversation.

You're welcome to inspect and improve [Rand Talk's source code.](https://github.com/quasiyoke/RandTalkBot) If you have any suggestions or require help, please contact @quasiyoke

When asking questions, please provide this number: {0}'''

class StrangerHandler(telepot.helper.ChatHandler):
    COMMAND_RE_PATTERN = re.compile('^/(begin|end|help)\\b')

    def __init__(self, seed_tuple, stranger_service):
        super(StrangerHandler, self).__init__(seed_tuple, None)
        self._stranger_service = stranger_service
        self._stranger = self._stranger_service.get_or_create_stranger(self.chat_id)

    @asyncio.coroutine
    def _handle_command(self, command):
        if command == 'begin':
            yield from self._send_notification('Looking for a stranger for you.')
        elif command == 'end':
            yield from self._send_notification('Chat was finished. Feel free to /begin a new one.')
        elif command == 'help':
            yield from self._send_notification(HELP_PATTERN.format(self.chat_id))

    @asyncio.coroutine
    def _send_notification(self, message):
        yield from self.sender.sendMessage('*Rand Talk:* {0}'.format(message), parse_mode='Markdown')

    @asyncio.coroutine
    def on_message(self, message):
        content_type, chat_type, chat_id = telepot.glance2(message)

        if chat_type != 'private':
            return

        if content_type == 'text':
            command_match = StrangerHandler.COMMAND_RE_PATTERN.match(message['text'])
            if command_match:
                yield from self._handle_command(command_match.group(1))
            elif self._stranger.is_chatting:
                yield from self.sender.sendMessage(message['text'])
        else:
            yield from self._send_notification('Messages of this type aren\'t supported.')
