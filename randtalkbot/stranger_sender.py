# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import re
import telepot
from .errors import StrangerSenderError
from .i18n import get_translation

LOGGER = logging.getLogger('randtalkbot.stranger_sender')

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
        self._bot = bot
        self._stranger = stranger
        self.update_translation()

    @classmethod
    def _escape_markdown(cls, string_instance):
        """Escapes string to prevent injecting Markdown into notifications.
        @see https://core.telegram.org/bots/api#using-markdown
        """
        if string_instance is not str:
            string_instance = str(string_instance)

        string_instance = cls.MARKDOWN_RE.sub(r'\\\1', string_instance)
        return string_instance

    async def answer_inline_query(self, query_id, answers):
        def translate(item):
            return self._(item) if isinstance(item, str) else self._(item[0]).format(*item[1:])

        for answer in answers:
            if answer['type'] == 'article':
                answer['title'] = translate(answer['title'])
                answer['description'] = translate(answer['description'])
                answer['message_text'] = translate(answer['message_text'])
        await self._bot.answerInlineQuery(query_id, answers, is_personal=True)

    async def send(self, message):
        """Raises:
            StrangerSenderError: If message's content type is not supported.
            TelegramError: If stranger has blocked the bot.
        """
        if message.is_reply:
            raise StrangerSenderError('Reply can\'t be sent.')
        try:
            method_name = StrangerSender.MESSAGE_TYPE_TO_METHOD_NAME[message.type]
        except KeyError:
            raise StrangerSenderError('Unsupported content_type: {}'.format(message.type))
        else:
            await getattr(self, method_name)(**message.sending_kwargs)

    async def send_notification(
            self,
            message,
            *args,
            disable_notification=None,
            disable_web_page_preview=None,
            reply_markup=None,
        ):
        """Raises:
            TelegramError: If stranger has blocked the bot.
        """
        args = [StrangerSender._escape_markdown(arg) for arg in args]
        message = self._(message).format(*args)

        if reply_markup and 'keyboard' in reply_markup:
            reply_markup = {
                'keyboard': [
                    [self._(key) for key in row]
                    for row in reply_markup['keyboard']
                    ],
                'one_time_keyboard': True,
                }

        # pylint: disable=no-member
        await self.sendMessage(
            '*Rand Talk:* {}'.format(message),
            disable_notification=disable_notification,
            disable_web_page_preview=disable_web_page_preview,
            parse_mode='Markdown',
            reply_markup=reply_markup,
            )

    def update_translation(self, partner=None):
        if partner:
            languages = self._stranger.get_common_languages(partner)
        else:
            languages = self._stranger.get_languages()
        self._ = get_translation(languages)
