# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import asynctest
from randtalkbot.stranger import Stranger, MissingPartnerError
from asynctest.mock import patch, Mock, MagicMock, CoroutineMock

class TestStranger(asynctest.TestCase):
    def setUp(self):
        self.handler = CoroutineMock()
        self.stranger = Stranger(31416, self.handler)

    @asynctest.ignore_loop
    def test_init(self):
        self.assertEqual(self.stranger.telegram_id, 31416)
        self.assertFalse(self.stranger._is_chatting)
        self.assertEqual(self.stranger._partner, None)
        self.assertFalse(self.stranger.is_looking_for_partner)
        self.assertEqual(self.stranger.looking_for_partner_from, None)

    def test_end_chatting__not_chatting_or_looking_stranger(self):
        yield from self.stranger.end_chatting()
        self.handler.send_notification.assert_not_called()
        self.handler.send.assert_not_called()
        self.assertFalse(self.stranger._is_chatting)
        self.assertEqual(self.stranger._partner, None)
        self.assertFalse(self.stranger.is_looking_for_partner)
        self.assertEqual(self.stranger.looking_for_partner_from, None)

    def test_end_chatting__chatting_stranger(self):
        partner = CoroutineMock()
        yield from self.stranger.set_partner(partner)
        self.handler.reset_mock()
        partner.reset_mock()
        yield from self.stranger.end_chatting()
        self.handler.send_notification.assert_called_once_with(
            'Chat was finished. Feel free to /begin a new one.',
            )
        self.handler.send.assert_not_called()
        partner.kick.assert_called_once_with()
        self.assertFalse(self.stranger._is_chatting)
        self.assertEqual(self.stranger._partner, None)
        self.assertFalse(self.stranger.is_looking_for_partner)
        self.assertEqual(self.stranger.looking_for_partner_from, None)

    def test_end_chatting__looking_stranger(self):
        yield from self.stranger.set_looking_for_partner()
        self.handler.reset_mock()
        yield from self.stranger.end_chatting()
        self.handler.send_notification.assert_called_once_with(
            'Looking for partner was stopped.',
            )
        self.handler.send.assert_not_called()
        self.assertFalse(self.stranger._is_chatting)
        self.assertEqual(self.stranger._partner, None)
        self.assertFalse(self.stranger.is_looking_for_partner)
        self.assertEqual(self.stranger.looking_for_partner_from, None)

    def test_kick(self):
        yield from self.stranger.kick()
        self.handler.send_notification.assert_called_once_with(
            'Your partner has left chat. Feel free to /begin a new conversation.',
            )
        self.handler.send.assert_not_called()
        self.assertFalse(self.stranger._is_chatting)
        self.assertEqual(self.stranger._partner, None)

    def test_set_partner__chatting_stranger(self):
        partner = CoroutineMock()
        yield from self.stranger.set_partner(partner)
        self.handler.reset_mock()
        partner.reset_mock()
        partner2 = CoroutineMock()
        yield from self.stranger.set_partner(partner2)
        self.handler.send_notification.assert_called_once_with(
            'Here\'s another stranger. Have fun!',
            )
        self.handler.send.assert_not_called()
        self.assertTrue(self.stranger._is_chatting)
        self.assertEqual(self.stranger._partner, partner2)
        self.assertFalse(self.stranger.is_looking_for_partner)
        self.assertEqual(self.stranger.looking_for_partner_from, None)

    def test_set_partner__not_chatting_stranger(self):
        partner = CoroutineMock()
        yield from self.stranger.set_partner(partner)
        self.handler.send_notification.assert_called_once_with(
            'Your partner is here. Have a nice chat!',
            )
        self.handler.send.assert_not_called()
        self.assertTrue(self.stranger._is_chatting)
        self.assertEqual(self.stranger._partner, partner)
        self.assertFalse(self.stranger.is_looking_for_partner)
        self.assertEqual(self.stranger.looking_for_partner_from, None)

    def test_send(self):
        yield from self.stranger.send('content_type', 'content_kwargs')
        self.handler.send.assert_called_once_with('content_type', 'content_kwargs')
        self.handler.send_notification.assert_not_called()

    def test_send_to_partner__chatting_stranger(self):
        partner = CoroutineMock()
        yield from self.stranger.set_partner(partner)
        self.handler.reset_mock()
        partner.reset_mock()
        yield from self.stranger.send_to_partner('content_type', 'content_kwargs')
        partner.send.assert_called_once_with('content_type', 'content_kwargs')
        self.handler.send_notification.assert_not_called()
        self.handler.send.assert_not_called()

    def test_send_to_partner__not_chatting_stranger(self):
        with self.assertRaises(MissingPartnerError):
            yield from self.stranger.send_to_partner('content_type', 'content_kwargs')
        self.handler.send_notification.assert_not_called()
        self.handler.send.assert_not_called()

    @patch('randtalkbot.stranger.datetime')
    @asyncio.coroutine
    def test_set_looking_for_partner__chatting_stranger(self, datetime_mock):
        partner = CoroutineMock()
        yield from self.stranger.set_partner(partner)
        self.handler.reset_mock()
        partner.reset_mock()
        datetime_mock.datetime.now.return_value = 'datetime_now'
        yield from self.stranger.set_looking_for_partner()
        partner.kick.assert_called_once_with()
        self.handler.send_notification.assert_called_once_with(
            'Looking for a stranger for you.',
            )
        self.handler.send.assert_not_called()
        self.assertFalse(self.stranger._is_chatting)
        self.assertEqual(self.stranger._partner, None)
        self.assertTrue(self.stranger.is_looking_for_partner)
        self.assertEqual(self.stranger.looking_for_partner_from, 'datetime_now')
