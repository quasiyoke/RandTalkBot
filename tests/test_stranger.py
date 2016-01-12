# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import asynctest
import datetime
from asynctest.mock import create_autospec, patch, Mock, CoroutineMock
from peewee import *
from playhouse.test_utils import test_database
from randtalkbot import stranger
from randtalkbot.stranger import Stranger, MissingPartnerError, StrangerError
from randtalkbot.stranger_sender import StrangerSenderError
from randtalkbot.stranger_sender_service import StrangerSenderService

database = SqliteDatabase(':memory:')
stranger.database_proxy.initialize(database)

class TestStranger(asynctest.TestCase):
    def setUp(self):
        database.create_tables([Stranger])
        self.stranger = Stranger.create(
            telegram_id=31416,
            )
        self.stranger2 = Stranger.create(
            telegram_id=27183,
            )
        self.stranger3 = Stranger.create(
            telegram_id=23571,
            )

    def tearDown(self):
        database.drop_tables([Stranger])

    @asynctest.ignore_loop
    def test_init(self):
        stranger = Stranger.get(Stranger.telegram_id == 31416)
        self.assertEqual(stranger.partner, None)
        self.assertEqual(stranger.looking_for_partner_from, None)

    def test_end_chatting__not_chatting_or_looking_for_partner(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        yield from self.stranger.end_chatting()
        stranger = Stranger.get(Stranger.telegram_id == 31416)
        self.assertEqual(stranger.partner, None)
        self.assertEqual(stranger.looking_for_partner_from, None)
        sender.send.assert_not_called()
        sender.send_notification.assert_not_called()

    def test_end_chatting__chatting_stranger(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.partner = self.stranger2
        self.stranger.save()
        self.stranger2.kick = CoroutineMock()
        yield from self.stranger.end_chatting()
        sender.send_notification.assert_called_once_with(
            'Chat was finished. Feel free to /begin a new one.',
            )
        sender.send.assert_not_called()
        self.stranger2.kick.assert_called_once_with()
        stranger = Stranger.get(Stranger.telegram_id == 31416)
        self.assertEqual(stranger.partner, None)
        self.assertEqual(stranger.looking_for_partner_from, None)

    def test_end_chatting__looking_for_partner(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.looking_for_partner_from = datetime.datetime(1970, 1, 1)
        self.stranger.save()
        yield from self.stranger.end_chatting()
        sender.send_notification.assert_called_once_with(
            'Looking for partner was stopped.',
            )
        sender.send.assert_not_called()
        stranger = Stranger.get(Stranger.telegram_id == 31416)
        self.assertEqual(stranger.partner, None)
        self.assertEqual(stranger.looking_for_partner_from, None)

    @asynctest.ignore_loop
    @patch('randtalkbot.stranger.StrangerSenderService', create_autospec(StrangerSenderService))
    def test_get_sender(self):
        from randtalkbot.stranger import StrangerSenderService
        StrangerSenderService.get_instance.return_value.get_or_create_stranger_sender \
            .return_value = 'foo_sender'
        self.assertEqual(self.stranger.get_sender(), 'foo_sender')
        StrangerSenderService.get_instance.return_value.get_or_create_stranger_sender \
            .assert_called_once_with(31416)

    def test_kick(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.partner = self.stranger2
        self.stranger.save()
        yield from self.stranger.kick()
        sender.send_notification.assert_called_once_with(
            'Your partner has left chat. Feel free to /begin a new conversation.',
            )
        sender.send.assert_not_called()
        stranger = Stranger.get(Stranger.telegram_id == 31416)
        self.assertEqual(stranger.partner, None)
        self.assertEqual(stranger.looking_for_partner_from, None)

    def test_set_partner__chatting_stranger(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.partner = self.stranger2
        self.stranger.save()
        yield from self.stranger.set_partner(self.stranger3)
        sender.send_notification.assert_called_once_with(
            'Here\'s another stranger. Have fun!',
            )
        sender.send.assert_not_called()
        stranger = Stranger.get(Stranger.telegram_id == 31416)
        self.assertEqual(stranger.partner, self.stranger3)
        self.assertEqual(stranger.looking_for_partner_from, None)

    def test_set_partner__not_chatting_stranger(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        yield from self.stranger.set_partner(self.stranger3)
        sender.send_notification.assert_called_once_with(
            'Your partner is here. Have a nice chat!',
            )
        sender.send.assert_not_called()
        stranger = Stranger.get(Stranger.telegram_id == 31416)
        self.assertEqual(stranger.partner, self.stranger3)
        self.assertEqual(stranger.looking_for_partner_from, None)

    def test_send__ok(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        yield from self.stranger.send('content_type', 'content_kwargs')
        sender.send.assert_called_once_with('content_type', 'content_kwargs')
        sender.send_notification.assert_not_called()

    def test_send__sender_error(self):
        sender = CoroutineMock()
        sender.send.side_effect = StrangerSenderError()
        self.stranger.get_sender = Mock(return_value=sender)
        with self.assertRaises(StrangerError):
            yield from self.stranger.send('content_type', 'content_kwargs')
        sender.send.assert_called_once_with('content_type', 'content_kwargs')
        sender.send_notification.assert_not_called()

    def test_send_to_partner__chatting_stranger(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.partner = self.stranger2
        self.stranger2.send = CoroutineMock()
        self.stranger.save()
        yield from self.stranger.send_to_partner('content_type', 'content_kwargs')
        self.stranger2.send.assert_called_once_with('content_type', 'content_kwargs')
        sender.send_notification.assert_not_called()
        sender.send.assert_not_called()

    def test_send_to_partner__not_chatting_stranger(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        with self.assertRaises(MissingPartnerError):
            yield from self.stranger.send_to_partner('content_type', 'content_kwargs')
        sender.send_notification.assert_not_called()
        sender.send.assert_not_called()

    @patch('randtalkbot.stranger.datetime')
    @asyncio.coroutine
    def test_set_looking_for_partner__chatting_stranger(self, datetime_mock):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.partner = self.stranger2
        self.stranger2.kick = CoroutineMock()
        self.stranger.save()
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(1980, 1, 1)
        yield from self.stranger.set_looking_for_partner()
        self.stranger2.kick.assert_called_once_with()
        sender.send_notification.assert_called_once_with(
            'Looking for a stranger for you.',
            )
        sender.send.assert_not_called()
        stranger = Stranger.get(Stranger.telegram_id == 31416)
        self.assertEqual(stranger.partner, None)
        self.assertEqual(stranger.looking_for_partner_from, datetime.datetime(1980, 1, 1))

    @patch('randtalkbot.stranger.datetime')
    @asyncio.coroutine
    def test_set_looking_for_partner__looking_for_partner_already(self, datetime_mock):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.partner = self.stranger2
        self.stranger2.kick = CoroutineMock()
        self.stranger.save()
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(1980, 1, 1)
        yield from self.stranger.set_looking_for_partner()
        self.stranger2.kick.assert_called_once_with()
        sender.send_notification.assert_called_once_with(
            'Looking for a stranger for you.',
            )
        sender.send.assert_not_called()
        stranger = Stranger.get(Stranger.telegram_id == 31416)
        self.assertEqual(stranger.partner, None)
        self.assertEqual(stranger.looking_for_partner_from, datetime.datetime(1980, 1, 1))
