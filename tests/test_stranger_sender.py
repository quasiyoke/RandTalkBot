# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import asynctest
from randtalkbot.errors import StrangerSenderError
from randtalkbot.stranger_sender import StrangerSender
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

    @patch('randtalkbot.stranger_sender.StrangerSender.update_translation', Mock())
    @asynctest.ignore_loop
    def test_init(self):
        self.get_translation.reset_mock()
        sender = StrangerSender(Mock(), Mock())
        StrangerSender.update_translation.assert_called_once_with()

    def test_answer_inline_query(self):
        self.translation.return_value = 'foo {} {}'
        yield from self.sender.answer_inline_query(
            31416,
            [{
                'type': 'article',
                'bar': 'baz',
                'title': 'bim',
                'description': 'zig',
                'message_text': ('zam', 1, 2),
                }],
            )
        self.bot.answerInlineQuery.assert_called_once_with(
            31416,
            [{
                'type': 'article',
                'bar': 'baz',
                'title': 'foo {} {}',
                'description': 'foo {} {}',
                'message_text': 'foo 1 2',
                }],
            is_personal=True,
            )

    def test_send_notification__no_reply_markup(self):
        self.translation.return_value = 'foo_translation'
        yield from self.sender.send_notification('foo')
        self.translation.assert_called_once_with('foo')
        self.sender.sendMessage.assert_called_once_with(
            '*Rand Talk:* foo_translation',
            disable_notification=None,
            disable_web_page_preview=None,
            parse_mode='Markdown',
            reply_markup=None,
            )

    def test_send_notification__format(self):
        self.translation.return_value = '{0} {2} foo_translation {1}'
        yield from self.sender.send_notification(
            'foo',
            'zero',
            'one',
            2,
            )
        self.translation.assert_called_once_with('foo')
        self.sender.sendMessage.assert_called_once_with(
            '*Rand Talk:* zero 2 foo_translation one',
            disable_notification=None,
            disable_web_page_preview=None,
            parse_mode='Markdown',
            reply_markup=None,
            )

    def test_send_notification__escapes_markdown(self):
        self.translation.return_value = '{0} {1}'
        yield from self.sender.send_notification(
            'foo',
            '*foo* _bar_ [baz](http://boo.com)',
            'foo\\\\` `bar baz\\\\boo foo``',
            )
        self.sender.sendMessage.assert_called_once_with(
            '*Rand Talk:* \\*foo\\* \\_bar\\_ \\[baz](http://boo.com) '
                'foo\\\\\\` \\`bar baz\\\\boo foo\\`\\`',
            disable_notification=None,
            disable_web_page_preview=None,
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
            disable_notification=None,
            disable_web_page_preview=None,
            parse_mode='Markdown',
            reply_markup={
                'no_keyboard': True,
                },
            )

    def test_send_notification__disable_notification_and_preview(self):
        self.translation.return_value = 'foo_translation'
        yield from self.sender.send_notification(
            'foo',
            disable_notification=True,
            disable_web_page_preview=True,
            )
        self.sender.sendMessage.assert_called_once_with(
            '*Rand Talk:* foo_translation',
            disable_notification=True,
            disable_web_page_preview=True,
            parse_mode='Markdown',
            reply_markup=None,
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
            disable_notification=None,
            disable_web_page_preview=None,
            parse_mode='Markdown',
            reply_markup={
                'keyboard': [
                    ['foo_translation', 'foo_translation'],
                    ['foo_translation', 'foo_translation'],
                    ],
                'one_time_keyboard': True,
                },
            )

    def test_send__text(self):
        message = Mock()
        message.type = 'text'
        message.sending_kwargs = {
            'foo': 'bar',
            'baz': 'boo',
            }
        yield from self.sender.send(message)
        self.sender.sendMessage.assert_called_once_with(**message.sending_kwargs)

    def test_send__unknown_content_type(self):
        message = Mock()
        message.type = 'foo_type'
        with self.assertRaises(StrangerSenderError):
            yield from self.sender.send(message)
        self.sender.sendMessage.assert_not_called()

    @patch('randtalkbot.stranger_sender.get_translation', Mock(return_value='foo_translation'))
    @asynctest.ignore_loop
    def test_update_translation__has_partner(self):
        from randtalkbot.stranger_sender import get_translation
        self.stranger.get_common_languages.reset_mock()
        self.stranger.get_common_languages.return_value = 'foo_common_languages'
        partner = Mock()
        self.sender.update_translation(partner)
        self.stranger.get_common_languages.assert_called_once_with(partner)
        get_translation.assert_called_once_with('foo_common_languages')
        self.assertEqual(self.sender._, 'foo_translation')

    @patch('randtalkbot.stranger_sender.get_translation', Mock(return_value='foo_translation'))
    @asynctest.ignore_loop
    def test_update_translation__has_not_partner(self):
        from randtalkbot.stranger_sender import get_translation
        self.stranger.partner = None
        self.sender.update_translation()
        get_translation.assert_called_once_with('foo_languages')
        self.assertEqual(self.sender._, 'foo_translation')
