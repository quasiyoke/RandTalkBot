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
from telepot import TelegramError

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

    @patch('randtalkbot.stranger.asyncio')
    @asyncio.coroutine
    def test_advertise__people_are_searching(self, asyncio_mock):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.looking_for_partner_from = datetime.datetime.utcnow()
        self.stranger.save()
        self.stranger2.looking_for_partner_from = datetime.datetime.utcnow()
        self.stranger2.save()
        yield from self.stranger._advertise()
        asyncio_mock.sleep.assert_called_once_with(30)
        sender.send_notification.assert_called_once_with(
            'You\'re still searching for partner among {0} people. You can talk with some of them if you '
                'remove partner\'s sex restrictions or extend the list of languages you know using /setup '
                'command. You can share the link to the bot between your friends: telegram.me/RandTalkBot '
                'or [vote for Rand Talk](https://telegram.me/storebot?start=randtalkbot). More people '
                '-- more fun!',
            2,
            )

    @patch('randtalkbot.stranger.asyncio')
    @asyncio.coroutine
    def test_advertise__people_are_not_searching(self, asyncio_mock):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.looking_for_partner_from = datetime.datetime.utcnow()
        self.stranger.save()
        yield from self.stranger._advertise()
        sender.send_notification.assert_not_called()

    @patch('randtalkbot.stranger.asyncio')
    @asyncio.coroutine
    def test_advertise_later(self, asyncio_mock):
        self.stranger._advertise = Mock(return_value='foo')
        self.stranger.advertise_later()
        asyncio_mock.get_event_loop.return_value.create_task \
            .assert_called_once_with('foo')

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
        self.stranger2.partner = self.stranger
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

    @patch('randtalkbot.stranger.LOGGER', Mock())
    @asyncio.coroutine
    def test_end_chatting__chatting_stranger_has_blocked_the_bot(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger2.partner = self.stranger
        self.stranger.partner = self.stranger2
        self.stranger.save()
        self.stranger2.kick = CoroutineMock()
        sender.send_notification.side_effect = TelegramError('foo_description', 123)
        yield from self.stranger.end_chatting()
        self.stranger2.kick.assert_called_once_with()
        stranger = Stranger.get(Stranger.telegram_id == 31416)
        self.assertEqual(stranger.partner, None)
        self.assertEqual(stranger.looking_for_partner_from, None)

    def test_end_chatting__buggy_stranger(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger2.partner = None
        self.stranger.partner = self.stranger2
        self.stranger.save()
        self.stranger2.kick = CoroutineMock()
        yield from self.stranger.end_chatting()
        sender.send_notification.assert_called_once_with(
            'Chat was finished. Feel free to /begin a new one.',
            )
        sender.send.assert_not_called()
        self.stranger2.kick.assert_not_called()
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

    @patch('randtalkbot.stranger.LOGGER', Mock())
    @asyncio.coroutine
    def test_end_chatting__stranger_looking_for_partner_has_blocked_the_bot(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.looking_for_partner_from = datetime.datetime(1970, 1, 1)
        self.stranger.save = Mock()
        sender.send_notification.side_effect = TelegramError('foo_description', 123)
        yield from self.stranger.end_chatting()
        sender.send_notification.assert_called_once_with(
            'Looking for partner was stopped.',
            )
        sender.send.assert_not_called()
        stranger = Stranger.get(Stranger.telegram_id == 31416)
        self.assertEqual(stranger.partner, None)
        self.assertEqual(stranger.looking_for_partner_from, None)
        self.stranger.save.assert_called_once_with()

    @asynctest.ignore_loop
    def test_get_languages__has_languages(self):
        self.stranger.languages = '["foo", "bar", "baz"]'
        self.assertEqual(self.stranger.get_languages(), ["foo", "bar", "baz"])

    @asynctest.ignore_loop
    def test_get_languages__no_languages(self):
        self.stranger.languages = None
        self.assertEqual(self.stranger.get_languages(), [])

    @asynctest.ignore_loop
    def test_get_languages__corrupted_json(self):
        self.stranger.languages = '["foo'
        self.assertEqual(self.stranger.get_languages(), ['en'])

    @asynctest.ignore_loop
    @patch('randtalkbot.stranger.StrangerSenderService', create_autospec(StrangerSenderService))
    def test_get_sender(self):
        from randtalkbot.stranger import StrangerSenderService
        StrangerSenderService.get_instance.return_value.get_or_create_stranger_sender \
            .return_value = 'foo_sender'
        self.assertEqual(self.stranger.get_sender(), 'foo_sender')
        StrangerSenderService.get_instance.return_value.get_or_create_stranger_sender \
            .assert_called_once_with(self.stranger)

    @asynctest.ignore_loop
    def test_is_novice__novice(self):
        self.stranger.languages = None
        self.stranger.sex = None
        self.stranger.partner_sex = None
        self.assertTrue(self.stranger.is_novice())

    @asynctest.ignore_loop
    def test_is_novice__not_novice(self):
        self.stranger.languages = 'foo'
        self.stranger.sex = None
        self.stranger.partner_sex = None
        self.assertFalse(self.stranger.is_novice())

    @asynctest.ignore_loop
    def test_is_full__full(self):
        self.stranger.languages = 'foo'
        self.stranger.sex = 'foo'
        self.stranger.partner_sex = 'foo'
        self.assertTrue(self.stranger.is_full())

    @asynctest.ignore_loop
    def test_is_full__not_full(self):
        self.stranger.languages = 'foo'
        self.stranger.sex = 'foo'
        self.stranger.partner_sex = None
        self.assertFalse(self.stranger.is_full())

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

    @patch('randtalkbot.stranger.LOGGER', Mock())
    @asyncio.coroutine
    def test_kick(self):
        from randtalkbot.stranger import LOGGER
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.partner = self.stranger2
        self.stranger.save()
        error =  TelegramError('foo_description', 123)
        sender.send_notification.side_effect =error
        yield from self.stranger.kick()
        stranger = Stranger.get(Stranger.telegram_id == 31416)
        self.assertEqual(stranger.partner, None)
        self.assertEqual(stranger.looking_for_partner_from, None)
        LOGGER.warning.assert_called_once_with('Kick. Can\'t notify stranger %d: %s', stranger.id, error)

    @asynctest.ignore_loop
    def test_prevent_advertising__ok(self):
        deferred_advertising = Mock()
        self.stranger._deferred_advertising = deferred_advertising
        self.stranger.prevent_advertising()
        deferred_advertising.cancel.assert_called_once_with()
        self.assertEqual(self.stranger._deferred_advertising, None)

    @asynctest.ignore_loop
    def test_prevent_advertising__deferred_is_not_set(self):
        self.stranger.prevent_advertising()
        self.assertTrue(True)

    @asynctest.ignore_loop
    def test_prevent_advertising__deferred_is_none(self):
        self.stranger._deferred_advertising = None
        self.stranger.prevent_advertising()
        self.assertTrue(True)

    def test_send__ok(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        message = Mock()
        yield from self.stranger.send(message)
        sender.send.assert_called_once_with(message)
        sender.send_notification.assert_not_called()

    def test_send__sender_error(self):
        sender = CoroutineMock()
        sender.send.side_effect = StrangerSenderError()
        self.stranger.get_sender = Mock(return_value=sender)
        message = Mock()
        with self.assertRaises(StrangerError):
            yield from self.stranger.send(message)
        sender.send.assert_called_once_with(message)
        sender.send_notification.assert_not_called()

    @patch('randtalkbot.stranger.get_languages_names', Mock())
    @asyncio.coroutine
    def test_send_notification_about_another_partner__knows_uncommon_languages_one_common(self):
        from randtalkbot.stranger import get_languages_names
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.languages = '["foo", "bar", "baz", "boo"]'
        self.stranger2.languages = '["zet", "zen", "foo"]'
        yield from self.stranger.send_notification_about_another_partner(self.stranger2)
        get_languages_names.assert_called_once_with({'foo'})
        sender.send_notification.assert_called_once_with(
            'Here\'s another stranger. Use {0} please.',
            get_languages_names.return_value,
            )

    @patch('randtalkbot.stranger.get_languages_names', Mock())
    @asyncio.coroutine
    def test_send_notification_about_another_partner__knows_uncommon_languages_several_common(self):
        from randtalkbot.stranger import get_languages_names
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.languages = '["foo", "bar", "baz", "boo"]'
        self.stranger2.languages = '["zet", "bar", "foo"]'
        yield from self.stranger.send_notification_about_another_partner(self.stranger2)
        get_languages_names.assert_called_once_with({'foo', 'bar'})
        sender.send_notification.assert_called_once_with(
            'Here\'s another stranger. You can use the following languages: {0}.',
            get_languages_names.return_value,
            )

    @patch('randtalkbot.stranger.get_languages_names', Mock())
    @asyncio.coroutine
    def test_send_notification_about_another_partner__all_languages_are_common(self):
        from randtalkbot.stranger import get_languages_names
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.languages = '["foo", "bar", "baz"]'
        self.stranger2.languages = '["baz", "bar", "foo"]'
        yield from self.stranger.send_notification_about_another_partner(self.stranger2)
        sender.send_notification.assert_called_once_with(
            'Here\'s another stranger. Have fun!',
            )

    @patch('randtalkbot.stranger.get_languages_names', Mock())
    @asyncio.coroutine
    def test_send_notification_about_retrieving_partner__knows_uncommon_languages_one_common(self):
        from randtalkbot.stranger import get_languages_names
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.languages = '["foo", "bar", "baz", "boo"]'
        self.stranger2.languages = '["zet", "zen", "foo"]'
        yield from self.stranger.send_notification_about_retrieving_partner(self.stranger2)
        get_languages_names.assert_called_once_with({'foo'})
        sender.send_notification.assert_called_once_with(
            'Your partner is here. Use {0} please.',
            get_languages_names.return_value,
            )

    @patch('randtalkbot.stranger.get_languages_names', Mock())
    @asyncio.coroutine
    def test_send_notification_about_retrieving_partner__knows_uncommon_languages_several_common(self):
        from randtalkbot.stranger import get_languages_names
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.languages = '["foo", "bar", "baz", "boo"]'
        self.stranger2.languages = '["zet", "bar", "foo"]'
        yield from self.stranger.send_notification_about_retrieving_partner(self.stranger2)
        get_languages_names.assert_called_once_with({'foo', 'bar'})
        sender.send_notification.assert_called_once_with(
            'Your partner is here. You can use the following languages: {0}.',
            get_languages_names.return_value,
            )

    @patch('randtalkbot.stranger.get_languages_names', Mock())
    @asyncio.coroutine
    def test_send_notification_about_retrieving_partner__all_languages_are_common(self):
        from randtalkbot.stranger import get_languages_names
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.languages = '["foo", "bar", "baz"]'
        self.stranger2.languages = '["baz", "bar", "foo"]'
        yield from self.stranger.send_notification_about_retrieving_partner(self.stranger2)
        sender.send_notification.assert_called_once_with(
            'Your partner is here. Have a nice chat!',
            )

    def test_send_to_partner__chatting_stranger(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.partner = self.stranger2
        self.stranger2.send = CoroutineMock()
        self.stranger.save()
        message = Mock()
        yield from self.stranger.send_to_partner(message)
        self.stranger2.send.assert_called_once_with(message)
        sender.send_notification.assert_not_called()
        sender.send.assert_not_called()

    def test_send_to_partner__not_chatting_stranger(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        with self.assertRaises(MissingPartnerError):
            yield from self.stranger.send_to_partner(Mock())
        sender.send_notification.assert_not_called()
        sender.send.assert_not_called()

    @asynctest.ignore_loop
    def test_set_languages__ok(self):
        # 6 languages.
        self.stranger.set_languages(['ru', 'en', 'it', 'fr', 'de', 'pt', ])
        self.assertEqual(self.stranger.languages, '["ru", "en", "it", "fr", "de", "pt"]')

    @asynctest.ignore_loop
    def test_set_languages__same(self):
        self.stranger.languages = '["foo", "bar", "baz"]'
        self.stranger.set_languages(['same'])
        self.assertEqual(self.stranger.languages, '["foo", "bar", "baz"]')

    @asynctest.ignore_loop
    def test_set_languages__empty(self):
        from randtalkbot.stranger import EmptyLanguagesError
        with self.assertRaises(EmptyLanguagesError):
            self.stranger.set_languages([])

    @asynctest.ignore_loop
    def test_set_languages__same_empty(self):
        from randtalkbot.stranger import EmptyLanguagesError
        self.stranger.languages = None
        with self.assertRaises(EmptyLanguagesError):
            self.stranger.set_languages(['same'])

    @asynctest.ignore_loop
    def test_set_languages__too_much(self):
        from randtalkbot.stranger import StrangerError
        self.stranger.languages = None
        with self.assertRaises(StrangerError):
            # 7 languages.
            self.stranger.set_languages(['ru', 'en', 'it', 'fr', 'de', 'pt', 'po'])

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

    def test_set_partner__chatting_stranger(self):
        self.stranger2.partner = self.stranger
        self.stranger2.kick = CoroutineMock()
        self.stranger.partner = self.stranger2
        self.stranger.send_notification_about_another_partner = CoroutineMock()
        self.stranger.prevent_advertising = Mock()
        self.stranger.save()
        yield from self.stranger.set_partner(self.stranger3)
        self.stranger.prevent_advertising.assert_called_once_with()
        self.stranger.send_notification_about_another_partner.assert_called_once_with(self.stranger3)
        self.stranger2.kick.assert_called_once_with()
        stranger = Stranger.get(Stranger.telegram_id == 31416)
        self.assertEqual(stranger.partner, self.stranger3)
        self.assertEqual(stranger.looking_for_partner_from, None)

    def test_set_partner__buggy_chatting_stranger(self):
        self.stranger.send_notification_about_another_partner = CoroutineMock()
        self.stranger2.kick = CoroutineMock()
        self.stranger.partner = self.stranger2
        self.stranger.save()
        yield from self.stranger.set_partner(self.stranger3)
        self.stranger2.kick.assert_not_called()
        stranger = Stranger.get(Stranger.telegram_id == 31416)
        self.assertEqual(stranger.partner, self.stranger3)
        self.assertEqual(stranger.looking_for_partner_from, None)

    @patch('randtalkbot.stranger.LOGGER', Mock())
    @asyncio.coroutine
    def test_set_partner__chatting_stranger_has_blocked_the_bot(self):
        from randtalkbot.stranger import LOGGER
        self.stranger2.partner = self.stranger
        self.stranger2.kick = CoroutineMock()
        error = TelegramError('foo_description', 123)
        self.stranger.partner = self.stranger2
        self.stranger.send_notification_about_another_partner = CoroutineMock(side_effect=error)
        self.stranger.save()
        with self.assertRaises(StrangerError):
            yield from self.stranger.set_partner(self.stranger3)
        self.stranger2.kick.assert_called_once_with()
        stranger = Stranger.get(Stranger.telegram_id == 31416)
        self.assertEqual(stranger.partner, None)
        self.assertEqual(stranger.looking_for_partner_from, None)
        LOGGER.warning.assert_called_once_with(
            'Set partner. Can\'t notify stranger %d: %s',
            self.stranger.id,
            error,
            )

    def test_set_partner__not_chatting_stranger(self):
        self.stranger.send_notification_about_retrieving_partner = CoroutineMock()
        yield from self.stranger.set_partner(self.stranger3)
        self.stranger.send_notification_about_retrieving_partner.assert_called_once_with(self.stranger3)
        stranger = Stranger.get(Stranger.telegram_id == 31416)
        self.assertEqual(stranger.partner, self.stranger3)
        self.assertEqual(stranger.looking_for_partner_from, None)

    @patch('randtalkbot.stranger.LOGGER', Mock())
    @asyncio.coroutine
    def test_set_partner__not_chatting_stranger_has_blocked_the_bot(self):
        from randtalkbot.stranger import LOGGER
        error = TelegramError('foo_description', 123)
        self.stranger.send_notification_about_retrieving_partner = CoroutineMock(side_effect=error)
        with self.assertRaises(StrangerError):
            yield from self.stranger.set_partner(self.stranger3)
        stranger = Stranger.get(Stranger.telegram_id == 31416)
        self.assertEqual(stranger.partner, None)
        self.assertEqual(stranger.looking_for_partner_from, None)
        LOGGER.warning.assert_called_once_with(
            'Set partner. Can\'t notify stranger %d: %s',
            self.stranger.id,
            error,
            )

    @asynctest.ignore_loop
    def test_set_sex__correct(self):
        self.stranger.set_sex('  mALe ')
        self.assertEqual(self.stranger.sex, 'male')

    @asynctest.ignore_loop
    def test_set_sex__translated(self):
        self.stranger.set_sex('  МУЖСКОЙ ')
        self.assertEqual(self.stranger.sex, 'male')

    @asynctest.ignore_loop
    def test_set_sex__additional(self):
        self.stranger.set_sex('  МАЛЬЧИК ')
        self.assertEqual(self.stranger.sex, 'male')

    @asynctest.ignore_loop
    def test_set_sex__incorrect(self):
        from randtalkbot.stranger import SexError
        self.stranger.sex = 'foo'
        with self.assertRaises(SexError):
            self.stranger.set_sex('not_a_sex')
        self.assertEqual(self.stranger.sex, 'foo')

    @asynctest.ignore_loop
    def test_set_partner_sex__correct(self):
        self.stranger.set_partner_sex('  mALe ')
        self.assertEqual(self.stranger.partner_sex, 'male')

    @asynctest.ignore_loop
    def test_set_partner_sex__additional(self):
        self.stranger.set_partner_sex('  МАЛЬЧИК ')
        self.assertEqual(self.stranger.partner_sex, 'male')

    @asynctest.ignore_loop
    def test_set_partner_sex__incorrect(self):
        from randtalkbot.stranger import SexError
        self.stranger.partner_sex = 'foo'
        with self.assertRaises(SexError):
            self.stranger.set_partner_sex('not_a_sex')
        self.assertEqual(self.stranger.partner_sex, 'foo')

    @asynctest.ignore_loop
    def test_speaks_on_language__novice(self):
        self.stranger.languages = None
        self.assertFalse(self.stranger.speaks_on_language('foo'))

    @asynctest.ignore_loop
    def test_speaks_on_language__speaks(self):
        self.stranger.languages = '["foo", "bar", "baz"]'
        self.assertTrue(self.stranger.speaks_on_language('bar'))

    @asynctest.ignore_loop
    def test_speaks_on_language__not_speaks(self):
        self.stranger.languages = '["foo", "bar", "baz"]'
        self.assertFalse(self.stranger.speaks_on_language('boo'))
