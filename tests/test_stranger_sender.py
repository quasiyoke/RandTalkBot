# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import asynctest
from randtalkbot.stranger_sender import StrangerSender, StrangerSenderError
from asynctest.mock import call, patch, Mock, CoroutineMock

class TestStrangerSender(asynctest.TestCase):
    @patch('randtalkbot.stranger_sender.get_translation', Mock())
    def setUp(self):
        from randtalkbot.stranger_sender import get_translation
        self.bot = CoroutineMock()
        self.stranger = Mock()
        self.stranger.telegram_id = 31416
        self.stranger.get_languages.return_value = 'foo_languages'
        self.sender = StrangerSender(self.bot, self.stranger)
        self.sender.sendMessage = CoroutineMock()
        self.get_translation = get_translation
        self.translation = self.get_translation.return_value
        self.translation.reset_mock()

    @asynctest.ignore_loop
    def test_init(self):
        self.stranger.get_languages.assert_called_once_with()
        self.get_translation.assert_called_once_with('foo_languages')

    def test_send_notification__no_reply_markup(self):
        self.translation.return_value = 'foo_translation'
        yield from self.sender.send_notification('foo')
        self.translation.assert_called_once_with('foo')
        self.sender.sendMessage.assert_called_once_with(
            '*Rand Talk:* foo_translation',
            parse_mode='Markdown',
            reply_markup=None,
            )

    def test_send_notification__format(self):
        self.translation.return_value = '{0} foo_translation {1}'
        yield from self.sender.send_notification(
            'foo',
            'zero',
            'one',
            )
        self.translation.assert_called_once_with('foo')
        self.sender.sendMessage.assert_called_once_with(
            '*Rand Talk:* zero foo_translation one',
            parse_mode='Markdown',
            reply_markup=None,
            )

    def test_send_notification__with_reply_markup_no_keyboard(self):
        self.translation.return_value = 'foo_translation'
        yield from self.sender.send_notification(
            'foo',
            reply_markup={
                'no_keyboard': True,
                },
            )
        self.translation.assert_called_once_with('foo')
        self.sender.sendMessage.assert_called_once_with(
            '*Rand Talk:* foo_translation',
            parse_mode='Markdown',
            reply_markup={
                'no_keyboard': True,
                },
            )

    def test_send_notification__with_reply_markup_with_keyboard(self):
        self.translation.return_value = 'foo_translation'
        yield from self.sender.send_notification(
            'foo',
            reply_markup={
                'keyboard': [['fff', 'bar'], ['baz', 'boo']],
                },
            )
        self.assertEqual(
            self.translation.call_args_list,
            [call('foo'), call('fff'), call('bar'), call('baz'), call('boo'), ],
            )
        self.sender.sendMessage.assert_called_once_with(
            '*Rand Talk:* foo_translation',
            parse_mode='Markdown',
            reply_markup={
                'keyboard': [
                    ['foo_translation', 'foo_translation'],
                    ['foo_translation', 'foo_translation'],
                    ],
                },
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
