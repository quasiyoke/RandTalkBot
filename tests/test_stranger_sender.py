# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import asynctest
from randtalkbot.stranger_sender import StrangerSender, StrangerSenderError
from asynctest.mock import patch, Mock, CoroutineMock

class TestStrangerSender(asynctest.TestCase):
    def setUp(self):
        self.bot = CoroutineMock()
        self.sender = StrangerSender(self.bot, 31416)
        self.sender.sendMessage = CoroutineMock()

    def test_send_notification(self):
        yield from self.sender.send_notification('foo')
        self.sender.sendMessage.assert_called_once_with(
            '*Rand Talk:* foo',
            parse_mode='Markdown',
            )

    def test_send__text(self):
        content_kwargs = {'foo': 'bar'}
        yield from self.sender.send('text', content_kwargs)
        self.sender.sendMessage.assert_called_once_with(**content_kwargs)

    def test_send__video(self):
        content_kwargs = {'foo': 'bar'}
        with self.assertRaises(StrangerSenderError):
            yield from self.sender.send('video', content_kwargs)
        self.sender.sendMessage.assert_not_called()
