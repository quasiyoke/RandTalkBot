# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
import telepot

class StrangerSenderError(Exception):
    pass

class StrangerSender(telepot.helper.Sender):
    CONTENT_TYPE_TO_METHOD_NAME = {
        'text': 'sendMessage',
        'photo': 'sendPhoto',
        }

    @asyncio.coroutine
    def send(self, content_type, content_kwargs):
        try:
            method_name = StrangerSender.CONTENT_TYPE_TO_METHOD_NAME[content_type]
        except KeyError:
            raise StrangerSenderError('Unsupported content_type: {0}'.format(content_type))
        else:
            yield from getattr(self, method_name)(**content_kwargs)

    @asyncio.coroutine
    def send_notification(self, message, reply_markup=None):
        yield from self.sendMessage(
            '*Rand Talk:* {0}'.format(message),
            parse_mode='Markdown',
            reply_markup=reply_markup,
            )
