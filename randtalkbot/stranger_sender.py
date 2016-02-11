# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
import re
import telepot
from .i18n import get_translation

LOGGER = logging.getLogger('randtalkbot')

class StrangerSenderError(Exception):
    pass

class StrangerSender(telepot.helper.Sender):
    MESSAGE_TYPE_TO_METHOD_NAME = {
        'audio': 'sendAudio',
        'document': 'sendDocument',
        'location': 'sendLocation',
        'photo': 'sendPhoto',
        'sticker': 'sendSticker',
        'text': 'sendMessage',
        'video': 'sendVideo',
        'voice': 'sendVoice',
        }
    MARKDOWN_RE = re.compile(r'([\[\*_`])')

    def __init__(self, bot, stranger):
        super(StrangerSender, self).__init__(bot, stranger.telegram_id)
        self._stranger = stranger
        self.update_translation()

    @classmethod
    def _escape_markdown(cls, s):
        '''
        Escapes string to prevent injecting Markdown into notifications.
        @see https://core.telegram.org/bots/api#using-markdown
        '''
        if s is not str:
            s = str(s)
        s = cls.MARKDOWN_RE.sub(r'\\\1', s)
        return s

    @asyncio.coroutine
    def send(self, message):
        '''
        @raises StrangerSenderError if message's content type is not supported.
        @raises TelegramError if stranger has blocked the bot.
        '''
        try:
            method_name = StrangerSender.MESSAGE_TYPE_TO_METHOD_NAME[message.type]
        except KeyError:
            raise StrangerSenderError('Unsupported content_type: {0}'.format(message.type))
        else:
            yield from getattr(self, method_name)(**message.sending_kwargs)

    @asyncio.coroutine
    def send_notification(self, message, *args, reply_markup=None):
        '''
        @raise TelegramError if stranger has blocked the bot.
        '''
        args = [StrangerSender._escape_markdown(arg) for arg in args]
        message = self._(message).format(*args)
        if reply_markup and 'keyboard' in reply_markup:
            reply_markup = {
                'keyboard': [
                    [self._(key) for key in row]
                    for row in reply_markup['keyboard']
                    ],
                }
        yield from self.sendMessage(
            '*Rand Talk:* {0}'.format(message),
            parse_mode='Markdown',
            reply_markup=reply_markup,
            )

    def update_translation(self, partner=None):
        if partner:
            languages = self._stranger.get_common_languages(partner)
        else:
            languages = self._stranger.get_languages()
        self._ = get_translation(languages)
