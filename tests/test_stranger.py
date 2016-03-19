# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import asynctest
import datetime
from asynctest.mock import call, patch, Mock, CoroutineMock
from peewee import *
from playhouse.test_utils import test_database
from randtalkbot import stranger
from randtalkbot.errors import MissingPartnerError, StrangerError
from randtalkbot.stranger import Stranger
from randtalkbot.stranger_sender import StrangerSenderError
from randtalkbot.stranger_sender_service import StrangerSenderService
from telepot import TelegramError
from unittest.mock import create_autospec

database = SqliteDatabase(':memory:')
stranger.database_proxy.initialize(database)

class TestStranger(asynctest.TestCase):
    def setUp(self):
        database.create_tables([Stranger])
        self.stranger = Stranger.create(
            invitation='foo',
            telegram_id=31416,
            )
        self.stranger2 = Stranger.create(
            invitation='bar',
            telegram_id=27183,
            )
        self.stranger3 = Stranger.create(
            invitation='baz',
            telegram_id=23571,
            )
        self.stranger4 = Stranger.create(
            invitation='zig',
            telegram_id=11317,
            )

    def tearDown(self):
        database.drop_tables([Stranger])

    @asynctest.ignore_loop
    def test_init(self):
        stranger = Stranger.get(Stranger.telegram_id == 31416)
        self.assertEqual(stranger.looking_for_partner_from, None)

    @patch('randtalkbot.stranger.INVITATION_LENGTH', 5)
    @asynctest.ignore_loop
    def test_get_invitation(self):
        invitation = Stranger.get_invitation()
        self.assertIsInstance(invitation, str)
        self.assertEqual(len(invitation), 5)

    async def test_add_bonuses__ok(self):
        self.stranger.bonus_count = 1000
        self.stranger._notify_about_bonuses = CoroutineMock()
        self.stranger.save = Mock()
        await self.stranger._add_bonuses(31415)
        self.stranger.save.assert_called_once_with()
        self.assertEqual(self.stranger.bonus_count, 32415)
        self.stranger._notify_about_bonuses.assert_called_once_with(31415)

    async def test_add_bonuses__muted(self):
        self.stranger.bonus_count = 1000
        self.stranger._notify_about_bonuses = CoroutineMock()
        self.stranger.save = Mock()
        self.stranger._bonuses_notifications_muted = True
        await self.stranger._add_bonuses(1)
        self.stranger.save.assert_called_once_with()
        self.assertEqual(self.stranger.bonus_count, 1001)
        self.stranger._notify_about_bonuses.assert_not_called()

    @patch('randtalkbot.stranger.asyncio', CoroutineMock())
    @patch('randtalkbot.stranger.StatsService')
    async def test_advertise__people_are_searching_chat_lacks_males(self, stats_service_mock):
        from randtalkbot.stranger import asyncio
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.get_start_args = Mock(return_value='foo_start_args')
        self.stranger.looking_for_partner_from = datetime.datetime.utcnow()
        self.stranger.save()
        self.stranger2.looking_for_partner_from = datetime.datetime.utcnow()
        self.stranger2.save()
        stats_service_mock.get_instance.return_value.get_stats.return_value.get_sex_ratio.return_value = 0.9
        await self.stranger._advertise()
        asyncio.sleep.assert_called_once_with(30)
        self.assertEqual(
            sender.send_notification.call_args_list,
            [
                call(
                    'The search is going on. {0} users are looking for partner -- change your '
                        'preferences (languages, partner\'s sex) using /setup command to talk with them.\n'
                        'Chat *lacks males!* Send the link to your friends and earn {1} bonuses for every '
                        'invited male and {2} bonus for each female (the more bonuses you have -- the faster '
                        'partner\'s search will be):',
                    2,
                    3,
                    1,
                    disable_notification=True,
                    ),
                call(
                    'Do you want to talk with somebody, practice in foreign languages or you just want '
                        'to have some fun? Rand Talk will help you! It\'s a bot matching you with '
                        'a random stranger of desired sex speaking on your language. {0}',
                    'https://telegram.me/RandTalkBot?start=foo_start_args',
                    disable_notification=True,
                    disable_web_page_preview=True,
                    ),
                ],
            )

    @patch('randtalkbot.stranger.asyncio', CoroutineMock())
    @patch('randtalkbot.stranger.StatsService')
    async def test_advertise__people_are_searching_chat_lacks_females(self, stats_service_mock):
        from randtalkbot.stranger import asyncio
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.get_invitation_link = Mock(return_value='foo_invitation_link')
        self.stranger.looking_for_partner_from = datetime.datetime.utcnow()
        self.stranger.save()
        self.stranger2.looking_for_partner_from = datetime.datetime.utcnow()
        self.stranger2.save()
        stats_service_mock.get_instance.return_value.get_stats.return_value.get_sex_ratio.return_value = 1.1
        await self.stranger._advertise()
        asyncio.sleep.assert_called_once_with(30)
        self.assertEqual(
            sender.send_notification.call_args_list,
            [
                call(
                    'The search is going on. {0} users are looking for partner -- change your '
                        'preferences (languages, partner\'s sex) using /setup command to talk with them.\n'
                        'Chat *lacks females!* Send the link to your friends and earn {1} bonuses for every '
                        'invited female and {2} bonus for each male (the more bonuses you have -- the faster '
                        'partner\'s search will be):',
                    2,
                    3,
                    1,
                    disable_notification=True,
                    ),
                call(
                    'Do you want to talk with somebody, practice in foreign languages or you just want '
                        'to have some fun? Rand Talk will help you! It\'s a bot matching you with '
                        'a random stranger of desired sex speaking on your language. {0}',
                    'foo_invitation_link',
                    disable_notification=True,
                    disable_web_page_preview=True,
                    ),
                ],
            )

    @patch('randtalkbot.stranger.asyncio', CoroutineMock())
    async def test_advertise__people_are_not_searching(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.looking_for_partner_from = datetime.datetime.utcnow()
        self.stranger.save()
        await self.stranger._advertise()
        sender.send_notification.assert_not_called()

    @patch('randtalkbot.stranger.asyncio', CoroutineMock())
    @patch('randtalkbot.stranger.StatsService')
    @patch('randtalkbot.stranger.LOGGER', Mock())
    async def test_advertise__stranger_has_blocked_the_bot(self, stats_service_mock):
        from randtalkbot.stranger import asyncio
        from randtalkbot.stranger import LOGGER
        self.stranger.get_sender = Mock()
        self.stranger.get_sender.return_value.send_notification = CoroutineMock(
            side_effect=TelegramError('', 0),
            )
        self.stranger.get_invitation_link = Mock(return_value='foo_invitation_link')
        self.stranger.looking_for_partner_from = datetime.datetime.utcnow()
        self.stranger.save()
        self.stranger2.looking_for_partner_from = datetime.datetime.utcnow()
        self.stranger2.save()
        stats_service_mock.get_instance.return_value.get_stats.return_value.get_sex_ratio.return_value = 1.1
        
        await self.stranger._advertise()
        self.assertTrue(LOGGER.warning.called)

    @patch('randtalkbot.stranger.asyncio')
    async def test_advertise_later(self, asyncio_mock):
        self.stranger._advertise = Mock(return_value='foo')
        asyncio_mock.sleep = CoroutineMock()
        self.stranger.advertise_later()
        asyncio_mock.get_event_loop.return_value.create_task.assert_called_once_with('foo')

    async def test_end_talk__not_chatting_or_looking_for_partner(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.get_partner = Mock(return_value=None)
        self.stranger.set_partner = CoroutineMock()
        await self.stranger.end_talk()
        self.assertEqual(self.stranger.looking_for_partner_from, None)
        sender.send_notification.assert_not_called()
        self.stranger.set_partner.assert_called_once_with(None)

    async def test_end_talk__chatting_stranger(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.get_partner = Mock(return_value=self.stranger2)
        self.stranger._notify_talk_ended = CoroutineMock()
        self.stranger.set_partner = CoroutineMock()
        await self.stranger.end_talk()
        self.stranger._notify_talk_ended.assert_called_once_with(by_self=True)
        self.assertEqual(self.stranger.looking_for_partner_from, None)
        self.stranger.set_partner.assert_called_once_with(None)

    @patch('randtalkbot.stranger.LOGGER', Mock())
    async def test_end_talk__chatting_stranger_has_blocked_the_bot(self):
        from randtalkbot.stranger import LOGGER
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.get_partner = Mock(return_value=self.stranger2)
        self.stranger._notify_talk_ended = CoroutineMock(side_effect=StrangerError())
        self.stranger.set_partner = CoroutineMock()
        await self.stranger.end_talk()
        self.assertTrue(LOGGER.warning.called)
        self.assertEqual(self.stranger.looking_for_partner_from, None)
        self.stranger.set_partner.assert_called_once_with(None)

    async def test_end_talk__looking_for_partner(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.looking_for_partner_from = datetime.datetime(1970, 1, 1)
        self.stranger.get_partner = Mock(return_value=None)
        self.stranger._notify_talk_ended = CoroutineMock()
        self.stranger.set_partner = CoroutineMock()
        await self.stranger.end_talk()
        sender.send_notification.assert_called_once_with('Looking for partner was stopped.')
        sender.send.assert_not_called()
        self.assertEqual(self.stranger.looking_for_partner_from, None)
        self.stranger.set_partner.assert_called_once_with(None)

    @patch('randtalkbot.stranger.LOGGER', Mock())
    async def test_end_talk__stranger_looking_for_partner_has_blocked_the_bot(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.looking_for_partner_from = datetime.datetime(1970, 1, 1)
        self.stranger.get_partner = Mock(return_value=None)
        self.stranger.set_partner = CoroutineMock()
        sender.send_notification.side_effect = TelegramError('foo_description', 123)
        await self.stranger.end_talk()
        sender.send_notification.assert_called_once_with('Looking for partner was stopped.')
        sender.send.assert_not_called()
        self.assertEqual(self.stranger.looking_for_partner_from, None)
        self.stranger.set_partner.assert_called_once_with(None)

    @asynctest.ignore_loop
    def test_get_common_languages__preserves_languages_order(self):
        self.stranger.languages = '["foo", "bar", "baz", "boo", "zen"]'
        self.stranger2.languages = '["zen", "baz", "zig", "foo", "zam", "baz"]'
        self.assertEqual(self.stranger.get_common_languages(self.stranger2), ["foo", "baz", "zen"])
        self.stranger.languages = '["zen", "bar", "baz", "foo", "boo"]'
        self.stranger2.languages = '["zen", "baz", "zig", "foo", "zam", "baz"]'
        self.assertEqual(self.stranger.get_common_languages(self.stranger2), ["zen", "baz", "foo"])

    @asynctest.ignore_loop
    def test_get_invitation_link(self):
        self.stranger.get_start_args = Mock(return_value='foo_start_args')
        self.assertEqual(
            self.stranger.get_invitation_link(),
            'https://telegram.me/RandTalkBot?start=foo_start_args',
            )

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
    def test_get_partner__cached(self):
        self.stranger._partner = Mock()
        self.assertEqual(self.stranger.get_partner(), self.stranger._partner)

    @asynctest.ignore_loop
    def test_get_partner__none(self):
        self.stranger.get_talk = Mock(return_value=None)
        self.assertEqual(self.stranger.get_partner(), None)

    @asynctest.ignore_loop
    def test_get_partner__ok(self):
        talk = Mock()
        self.stranger.get_talk = Mock(return_value=talk)
        partner = talk.get_partner.return_value
        self.assertEqual(self.stranger.get_partner(), partner)
        talk.get_partner.assert_called_once_with(self.stranger)
        self.assertEqual(self.stranger._partner, partner)

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
    def test_get_start_args(self):
        self.assertEqual(self.stranger.get_start_args(), 'eyJpIjoiZm9vIn0=')

    @asynctest.ignore_loop
    def test_get_talk__cached(self):
        self.stranger._talk = Mock()
        self.assertEqual(self.stranger.get_talk(), self.stranger._talk)

    @asynctest.ignore_loop
    @patch('randtalkbot.talk.Talk', Mock())
    def test_get_talk__ok(self):
        from randtalkbot.talk import Talk
        self.assertEqual(self.stranger.get_talk(), Talk.get_talk.return_value)
        Talk.get_talk.assert_called_once_with(self.stranger)

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

    async def test_kick__ok(self):
        self.stranger._notify_talk_ended = CoroutineMock()
        self.stranger._pay_for_talk = Mock()
        self.stranger._partner = self.stranger2
        self.stranger._talk = 'foo_talk'
        await self.stranger.kick()
        self.stranger._notify_talk_ended.assert_called_once_with(by_self=False)
        self.stranger._pay_for_talk.assert_called_once_with()
        self.assertEqual(self.stranger._partner, None)
        self.assertEqual(self.stranger._talk, None)

    @patch('randtalkbot.stranger.LOGGER', Mock())
    async def test_kick__telegram_error(self):
        from randtalkbot.stranger import LOGGER
        error = StrangerError()
        self.stranger._notify_talk_ended = CoroutineMock(side_effect=error)
        self.stranger._pay_for_talk = Mock()
        self.stranger._partner = self.stranger2
        self.stranger._talk = 'foo_talk'
        await self.stranger.kick()
        self.stranger._pay_for_talk.assert_called_once_with()
        self.assertEqual(self.stranger._partner, None)
        self.assertEqual(self.stranger._talk, None)
        LOGGER.warning.assert_called_once_with('Kick. Can\'t notify stranger %d: %s', self.stranger.id, error)

    @patch('randtalkbot.stranger.asyncio')
    async def test_mute_bonuses_notifications(self, asyncio_mock):
        self.stranger._unmute_bonuses_notifications = Mock(return_value='foo')
        self.stranger.mute_bonuses_notifications()
        asyncio_mock.get_event_loop.return_value.create_task.assert_called_once_with('foo')

    @patch('randtalkbot.stranger.asyncio', CoroutineMock())
    async def test_unmute_bonuses_notifications(self):
        from randtalkbot.stranger import asyncio
        self.stranger.bonus_count = 1200
        self.stranger._notify_about_bonuses = CoroutineMock()
        await self.stranger._unmute_bonuses_notifications(1000)
        asyncio.sleep.assert_called_once_with(3600)
        self.stranger._notify_about_bonuses.assert_called_once_with(200)

    async def test_notify_about_bonuses__zero(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        await self.stranger._notify_about_bonuses(0)
        sender.send_notification.assert_not_called()

    async def test_notify_about_bonuses__one(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.bonus_count = 1000
        await self.stranger._notify_about_bonuses(1)
        sender.send_notification.assert_called_once_with(
            'You\'ve received one bonus for inviting a person to the bot. '
                'Bonuses will help you to find partners quickly. Total bonuses count: {0}. '
                'Congratulations!\n'
                'To mute this notifications, use /mute\\_bonuses.',
            1000,
            )

    async def test_notify_about_bonuses__many(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.bonus_count = 1000
        await self.stranger._notify_about_bonuses(2)
        sender.send_notification.assert_called_once_with(
            'You\'ve received {0} bonuses for inviting a person to the bot. '
                'Bonuses will help you to find partners quickly. Total bonuses count: {1}. '
                'Congratulations!\n'
                'To mute this notifications, use /mute\\_bonuses.',
            2,
            1000,
            )

    @patch('randtalkbot.stranger.LOGGER', Mock())
    async def test_notify_about_bonuses__telegram_error(self):
        from randtalkbot.stranger import LOGGER
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        error = TelegramError('foo_description', 123)
        sender.send_notification.side_effect = error
        await self.stranger._notify_about_bonuses(1)
        LOGGER.info.assert_called_once_with('Can\'t notify stranger %d about bonuses: %s', 1, error)

    async def test_notify_talk_ended__by_self_no_bonuses(self):
        from randtalkbot.stranger import get_languages_names
        sender = CoroutineMock()
        sender._ = Mock(side_effect=['Chat was finished.', 'Feel free to /begin a new talk.'])
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.get_partner = Mock(return_value=None)
        talk = Mock()
        talk.is_successful.return_value = True
        talk.partner1 = self.stranger
        self.stranger.get_talk = Mock(return_value=talk)
        self.stranger.bonus_count = 0
        await self.stranger._notify_talk_ended(by_self=True)
        self.assertEqual(
            sender._.call_args_list,
            [
                call('Chat was finished.'),
                call('Feel free to /begin a new talk.'),
                ],
            )
        sender.send_notification.assert_called_once_with('Chat was finished. Feel free to /begin a new talk.')

    async def test_notify_talk_ended__not_by_self_no_bonuses(self):
        from randtalkbot.stranger import get_languages_names
        sender = CoroutineMock()
        sender._ = Mock(side_effect=['Your partner has left chat.', 'Feel free to /begin a new talk.'])
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.get_partner = Mock(return_value=None)
        talk = Mock()
        talk.is_successful.return_value = True
        talk.partner1 = self.stranger
        self.stranger.get_talk = Mock(return_value=talk)
        self.stranger.bonus_count = 0
        await self.stranger._notify_talk_ended(by_self=False)
        self.assertEqual(
            sender._.call_args_list,
            [
                call('Your partner has left chat.'),
                call('Feel free to /begin a new talk.'),
                ],
            )
        sender.send_notification.assert_called_once_with(
            'Your partner has left chat. Feel free to /begin a new talk.',
            )

    async def test_notify_talk_ended__telegram_error(self):
        from randtalkbot.stranger import get_languages_names
        sender = CoroutineMock()
        sender.send_notification.side_effect = TelegramError('', 0)
        sender._ = Mock(side_effect=['Your partner has left chat.', 'Feel free to /begin a new talk.'])
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.get_partner = Mock(return_value=None)
        talk = Mock()
        talk.is_successful.return_value = True
        talk.partner1 = self.stranger
        self.stranger.get_talk = Mock(return_value=talk)
        self.stranger.bonus_count = 0
        with self.assertRaises(StrangerError):
            await self.stranger._notify_talk_ended(by_self=False)

    async def test_notify_talk_ended__not_by_self_was_used_last_bonus(self):
        from randtalkbot.stranger import get_languages_names
        sender = CoroutineMock()
        sender._ = Mock(
            side_effect=[
                'Your partner has left chat.',
                'You\'ve used your last bonus.',
                'Feel free to /begin a new talk.',
                ],
            )
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.get_partner = Mock(return_value=None)
        talk = Mock()
        talk.is_successful.return_value = True
        talk.partner1 = self.stranger
        self.stranger.get_talk = Mock(return_value=talk)
        self.stranger.bonus_count = 1
        await self.stranger._notify_talk_ended(by_self=False)
        self.assertEqual(
            sender._.call_args_list,
            [
                call('Your partner has left chat.'),
                call('You\'ve used your last bonus.'),
                call('Feel free to /begin a new talk.'),
                ],
            )
        sender.send_notification.assert_called_once_with(
            'Your partner has left chat. You\'ve used your last bonus. Feel free to /begin a new talk.',
            )

    async def test_notify_talk_ended__not_by_self_was_used_a_bonus(self):
        from randtalkbot.stranger import get_languages_names
        sender = CoroutineMock()
        sender._ = Mock(
            side_effect=[
                'Your partner has left chat.',
                'You\'ve used one bonus. {0} bonus(es) left.',
                'Feel free to /begin a new talk.',
                ],
            )
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.get_partner = Mock(return_value=None)
        talk = Mock()
        talk.is_successful.return_value = True
        talk.partner1 = self.stranger
        self.stranger.get_talk = Mock(return_value=talk)
        self.stranger.bonus_count = 1000
        await self.stranger._notify_talk_ended(by_self=False)
        self.assertEqual(
            sender._.call_args_list,
            [
                call('Your partner has left chat.'),
                call('You\'ve used one bonus. {0} bonus(es) left.'),
                call('Feel free to /begin a new talk.'),
                ],
            )
        sender.send_notification.assert_called_once_with(
            'Your partner has left chat. You\'ve used one bonus. 999 bonus(es) left. Feel free to /begin '
                'a new talk.',
            )

    @patch('randtalkbot.stranger.get_languages_names', Mock())
    async def test_notify_partner_found__all_languages_are_common(self):
        from randtalkbot.stranger import get_languages_names
        sender = CoroutineMock()
        sender.update_translation = Mock()
        sender._ = Mock(side_effect=['Your partner is here.', 'Have a nice chat!'])
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.languages = '["foo", "bar", "baz"]'
        self.stranger.get_partner = Mock(return_value=None)
        self.stranger2.languages = '["baz", "bar", "foo"]'
        await self.stranger.notify_partner_found(self.stranger2)
        self.assertEqual(
            sender._.call_args_list,
            [
                call('Your partner is here.'),
                call('Have a nice chat!'),
                ],
            )
        sender.send_notification.assert_called_once_with(
            'Your partner is here. Have a nice chat!',
            )

    @patch('randtalkbot.stranger.get_languages_names', Mock())
    async def test_notify_partner_found__had_partner_already_no_bonuses(self):
        from randtalkbot.stranger import get_languages_names
        sender = CoroutineMock()
        sender.update_translation = Mock()
        sender._ = Mock(side_effect=['Here\'s another stranger.', 'Have a nice chat!'])
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.languages = '["foo", "bar", "baz"]'
        self.stranger.get_partner = Mock(return_value=self.stranger3)
        talk = Mock()
        talk.is_successful.return_value = True
        talk.partner1 = self.stranger
        self.stranger.get_talk = Mock(return_value=talk)
        self.stranger.bonus_count = 0
        self.stranger2.languages = '["baz", "bar", "foo"]'
        await self.stranger.notify_partner_found(self.stranger2)
        self.assertEqual(
            sender._.call_args_list,
            [
                call('Here\'s another stranger.'),
                call('Have a nice chat!'),
                ],
            )
        sender.send_notification.assert_called_once_with(
            'Here\'s another stranger. Have a nice chat!',
            )

    @patch('randtalkbot.stranger.get_languages_names', Mock())
    async def test_notify_partner_found__was_bonus_used(self):
        from randtalkbot.stranger import get_languages_names
        sender = CoroutineMock()
        sender.update_translation = Mock()
        sender._ = Mock(
            side_effect=[
                'You\'ve used one bonus with previous partner. {0} bonus(es) left.',
                'Here\'s another stranger.',
                ],
            )
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.languages = '["foo", "bar", "baz"]'
        self.stranger.get_partner = Mock(return_value=self.stranger3)
        talk = Mock()
        talk.is_successful.return_value = True
        talk.partner1 = self.stranger
        self.stranger.get_talk = Mock(return_value=talk)
        self.stranger.bonus_count = 1001
        self.stranger.looking_for_partner_from = datetime.datetime.utcnow()
        self.stranger2.languages = '["baz", "bar", "foo"]'
        await self.stranger.notify_partner_found(self.stranger2)
        self.assertEqual(
            sender._.call_args_list,
            [
                call('You\'ve used one bonus with previous partner. {0} bonus(es) left.'),
                call('Here\'s another stranger.'),
                ],
            )
        sender.send_notification.assert_called_once_with(
            'You\'ve used one bonus with previous partner. 1000 bonus(es) left. Here\'s another stranger.',
            )

    @patch('randtalkbot.stranger.get_languages_names', Mock())
    async def test_notify_partner_found__was_bonus_used_no_bonuses_left(self):
        from randtalkbot.stranger import get_languages_names
        sender = CoroutineMock()
        sender.update_translation = Mock()
        sender._ = Mock(
            side_effect=[
                'You\'ve used your last bonus with previous partner.',
                'Here\'s another stranger.',
                ],
            )
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.languages = '["foo", "bar", "baz"]'
        self.stranger.get_partner = Mock(return_value=self.stranger3)
        talk = Mock()
        talk.is_successful.return_value = True
        talk.partner1 = self.stranger
        self.stranger.get_talk = Mock(return_value=talk)
        self.stranger.bonus_count = 1
        self.stranger.looking_for_partner_from = datetime.datetime.utcnow()
        self.stranger2.languages = '["baz", "bar", "foo"]'
        await self.stranger.notify_partner_found(self.stranger2)
        self.assertEqual(
            sender._.call_args_list,
            [
                call('You\'ve used your last bonus with previous partner.'),
                call('Here\'s another stranger.'),
                ],
            )
        sender.send_notification.assert_called_once_with(
            'You\'ve used your last bonus with previous partner. Here\'s another stranger.',
            )

    @patch('randtalkbot.stranger.get_languages_names', Mock(return_value='Foo'))
    async def test_notify_partner_found__knows_uncommon_languages_one_common(self):
        from randtalkbot.stranger import get_languages_names
        sender = CoroutineMock()
        sender.update_translation = Mock()
        sender._ = Mock(side_effect=['Use {0} please.', 'Your partner is here.', ])
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.languages = '["foo", "bar", "baz", "boo"]'
        self.stranger.get_partner = Mock(return_value=None)
        self.stranger2.languages = '["zet", "zen", "foo"]'
        await self.stranger.notify_partner_found(self.stranger2)
        get_languages_names.assert_called_once_with(['foo'])
        self.assertEqual(
            sender.update_translation.call_args_list,
            [
                call(self.stranger2),
                call(),
                ],
            )
        self.assertEqual(
            sender._.call_args_list,
            [
                call('Use {0} please.'),
                call('Your partner is here.'),
                ],
            )
        sender.send_notification.assert_called_once_with(
            'Your partner is here. Use Foo please.',
            )

    @patch('randtalkbot.stranger.get_languages_names', Mock(return_value='Foo, Bar'))
    async def test_notify_partner_found__knows_uncommon_languages_several_common(self):
        from randtalkbot.stranger import get_languages_names
        sender = CoroutineMock()
        sender.update_translation = Mock()
        sender._ = Mock(side_effect=['You can use the following languages: {0}.', 'Your partner is here.', ])
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.languages = '["foo", "bar", "baz", "boo"]'
        self.stranger.get_partner = Mock(return_value=None)
        self.stranger2.languages = '["zet", "bar", "foo"]'
        await self.stranger.notify_partner_found(self.stranger2)
        get_languages_names.assert_called_once_with(['foo', 'bar'])
        self.assertEqual(
            sender.update_translation.call_args_list,
            [
                call(self.stranger2),
                call(),
                ],
            )
        self.assertEqual(
            sender._.call_args_list,
            [
                call('You can use the following languages: {0}.'),
                call('Your partner is here.'),
                ],
            )
        sender.send_notification.assert_called_once_with(
            'Your partner is here. You can use the following languages: Foo, Bar.',
            )

    @patch('randtalkbot.stranger.datetime', Mock())
    async def test_notify_partner_found__waiting_several_minutes(self):
        sender = CoroutineMock()
        sender._ = Mock(side_effect=[
            'Your partner is here.',
            'Your partner\'s been looking for you for {0} min. Say him \"Hello\" -- '
                'if he doesn\'t respond to you, launch search again by /begin command.',
            ])
        self.stranger.get_sender = Mock(return_value=sender)
        from randtalkbot.stranger import datetime as datetime_mock
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(1970, 1, 1, 10, 11)
        self.stranger2.looking_for_partner_from = datetime.datetime(1970, 1, 1, 10, 0)
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.languages = '["foo", "bar", "baz"]'
        self.stranger.get_partner = Mock(return_value=None)
        self.stranger2.languages = '["baz", "bar", "foo"]'
        await self.stranger.notify_partner_found(self.stranger2)
        self.assertEqual(
            sender._.call_args_list,
            [
                call('Your partner is here.'),
                call('Your partner\'s been looking for you for {0} min. Say him \"Hello\" -- '
                    'if he doesn\'t respond to you, launch search again by /begin command.'),
                ],
            )
        sender.send_notification.assert_called_once_with(
            'Your partner is here. Your partner\'s been looking for you for 11 min. '
                'Say him "Hello" -- if he doesn\'t respond to you, launch search again by /begin command.',
            )

    @patch('randtalkbot.stranger.datetime', Mock())
    async def test_notify_partner_found__waiting_several_hours(self):
        sender = CoroutineMock()
        sender._ = Mock(side_effect=[
            'Your partner is here.',
            'Your partner\'s been looking for you for {0} hr. Say him \"Hello\" -- '
                'if he doesn\'t respond to you, launch search again by /begin command.',
            ])
        self.stranger.get_sender = Mock(return_value=sender)
        from randtalkbot.stranger import datetime as datetime_mock
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(1970, 1, 1, 11, 0)
        self.stranger2.looking_for_partner_from = datetime.datetime(1970, 1, 1, 10, 0)
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.languages = '["foo", "bar", "baz"]'
        self.stranger.get_partner = Mock(return_value=None)
        self.stranger2.languages = '["baz", "bar", "foo"]'
        await self.stranger.notify_partner_found(self.stranger2)
        self.assertEqual(
            sender._.call_args_list,
            [
                call('Your partner is here.'),
                call('Your partner\'s been looking for you for {0} hr. Say him \"Hello\" -- '
                    'if he doesn\'t respond to you, launch search again by /begin command.'),
                ],
            )
        sender.send_notification.assert_called_once_with(
            'Your partner is here. Your partner\'s been looking for you for 1 hr. '
                'Say him "Hello" -- if he doesn\'t respond to you, launch search again by /begin command.',
            )

    @patch('randtalkbot.stranger.datetime', Mock())
    async def test_notify_partner_found__partner_doesnt_wait(self):
        sender = CoroutineMock()
        sender._ = Mock(side_effect=[
            'Your partner is here.',
            'Have a nice chat!',
            ])
        self.stranger.get_sender = Mock(return_value=sender)
        from randtalkbot.stranger import datetime as datetime_mock
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(1970, 1, 1, 11, 0)
        self.stranger.looking_for_partner_from = datetime.datetime(1970, 1, 1, 10, 0)
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.languages = '["foo", "bar", "baz"]'
        self.stranger.get_partner = Mock(return_value=None)
        self.stranger2.languages = '["baz", "bar", "foo"]'
        await self.stranger.notify_partner_found(self.stranger2)
        self.assertEqual(
            sender._.call_args_list,
            [
                call('Your partner is here.'),
                call('Have a nice chat!'),
                ],
            )
        sender.send_notification.assert_called_once_with('Your partner is here. Have a nice chat!')

    @patch('randtalkbot.stranger.datetime', Mock())
    async def test_notify_partner_found__waiting_only_a_little_bit(self):
        sender = CoroutineMock()
        sender._ = Mock(side_effect=[
            'Your partner is here.',
            'Have a nice chat!',
            ])
        self.stranger.get_sender = Mock(return_value=sender)
        from randtalkbot.stranger import datetime as datetime_mock
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(1970, 1, 1, 10, 4)
        self.stranger2.looking_for_partner_from = datetime.datetime(1970, 1, 1, 10, 0)
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.languages = '["foo", "bar", "baz"]'
        self.stranger.get_partner = Mock(return_value=None)
        self.stranger2.languages = '["baz", "bar", "foo"]'
        await self.stranger.notify_partner_found(self.stranger2)
        self.assertEqual(
            sender._.call_args_list,
            [
                call('Your partner is here.'),
                call('Have a nice chat!'),
                ],
            )
        sender.send_notification.assert_called_once_with('Your partner is here. Have a nice chat!')

    @patch('randtalkbot.stranger.get_languages_names', Mock())
    async def test_notify_partner_found__telegram_error(self):
        from randtalkbot.stranger import get_languages_names
        sender = CoroutineMock()
        sender.send_notification.side_effect = TelegramError('foo_description', 123)
        sender.update_translation = Mock()
        sender._ = Mock(side_effect=[
            'Your partner is here.',
            'Have a nice chat!',
            ])
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.languages = '["foo", "bar", "baz"]'
        self.stranger.get_partner = Mock(return_value=None)
        self.stranger2.languages = '["baz", "bar", "foo"]'
        with self.assertRaises(StrangerError):
            await self.stranger.notify_partner_found(self.stranger2)
        self.assertEqual(
            sender._.call_args_list,
            [
                call('Your partner is here.'),
                call('Have a nice chat!'),
                ],
            )
        sender.send_notification.assert_called_once_with('Your partner is here. Have a nice chat!')

    async def test_pay__ok(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.bonus_count = 1000
        self.stranger.save = Mock()
        await self.stranger.pay(31416, 'foo_gratitude')
        self.stranger.save.assert_called_once_with()
        self.assertEqual(self.stranger.bonus_count, 32416)
        sender.send_notification.assert_called_once_with(
            'You\'ve earned {0} bonuses. Total bonus amount: {1}. {2}',
            31416,
            32416,
            'foo_gratitude',
            )

    @patch('randtalkbot.stranger.LOGGER', Mock())
    async def test_pay__telegram_error(self):
        from randtalkbot.stranger import LOGGER
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.bonus_count = 1000
        self.stranger.save = Mock()
        error = TelegramError('foo_description', 123)
        sender.send_notification.side_effect = error
        await self.stranger.pay(31416, 'foo_gratitude')
        self.stranger.save.assert_called_once_with()
        self.assertEqual(self.stranger.bonus_count, 32416)
        LOGGER.info.assert_called_once_with('Pay. Can\'t notify stranger %d: %s', 1, error)

    @asynctest.ignore_loop
    def test_pay_for_talk__ok(self):
        talk = Mock()
        talk.is_successful.return_value = True
        talk.partner1 = self.stranger
        self.stranger.get_talk = Mock(return_value=talk)
        self.stranger.bonus_count = 1000
        self.stranger.save = Mock()
        self.stranger._pay_for_talk()
        self.assertEqual(self.stranger.bonus_count, 999)
        self.stranger.save.assert_called_once_with()

    @asynctest.ignore_loop
    def test_pay_for_talk__not_successful(self):
        talk = Mock()
        talk.is_successful.return_value = False
        talk.partner1 = self.stranger
        self.stranger.get_talk = Mock(return_value=talk)
        self.stranger.bonus_count = 1000
        self.stranger.save = Mock()
        self.stranger._pay_for_talk()
        self.assertEqual(self.stranger.bonus_count, 1000)

    @asynctest.ignore_loop
    def test_pay_for_talk__no_bonuses(self):
        talk = Mock()
        talk.is_successful.return_value = True
        talk.partner1 = self.stranger
        self.stranger.get_talk = Mock(return_value=talk)
        self.stranger.bonus_count = 0
        self.stranger.save = Mock()
        self.stranger._pay_for_talk()
        self.stranger.save.assert_not_called()

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
        self.assertEqual(getattr(stranger, '_deferred_advertising', None), None)

    @asynctest.ignore_loop
    def test_prevent_advertising__deferred_is_none(self):
        self.stranger._deferred_advertising = None
        self.stranger.prevent_advertising()
        self.assertEqual(self.stranger._deferred_advertising, None)

    @patch('randtalkbot.stranger.StatsService', Mock())
    async def test_reward_inviter__chat_lacks_such_user(self):
        from randtalkbot.stranger import StatsService
        StatsService.get_instance.return_value.get_stats.return_value.get_sex_ratio.return_value = 1.1
        self.stranger.invited_by = self.stranger2
        self.stranger2._add_bonuses = CoroutineMock()
        self.stranger.save = Mock()
        self.stranger.sex = 'female'
        await self.stranger._reward_inviter()
        StatsService.get_instance.return_value.get_stats.return_value.get_sex_ratio.assert_called_once_with()
        self.assertEqual(self.stranger.was_invited_as, 'female')
        self.stranger.save.assert_called_once_with()
        self.stranger.invited_by._add_bonuses.assert_called_once_with(3)

    @patch('randtalkbot.stranger.StatsService', Mock())
    async def test_reward_inviter__chat_doesnt_lack_such_user(self):
        from randtalkbot.stranger import StatsService
        StatsService.get_instance.return_value.get_stats.return_value.get_sex_ratio.return_value = 1.1
        self.stranger.invited_by = self.stranger2
        self.stranger2._add_bonuses = CoroutineMock()
        self.stranger.save = Mock()
        self.stranger.sex = 'not_specified'
        await self.stranger._reward_inviter()
        self.assertEqual(self.stranger.was_invited_as, 'not_specified')
        self.stranger.save.assert_called_once_with()
        self.stranger.invited_by._add_bonuses.assert_called_once_with(1)

    async def test_send__ok(self):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        message = Mock()
        await self.stranger.send(message)
        sender.send.assert_called_once_with(message)
        sender.send_notification.assert_not_called()

    async def test_send__sender_error(self):
        sender = CoroutineMock()
        sender.send.side_effect = StrangerSenderError()
        self.stranger.get_sender = Mock(return_value=sender)
        message = Mock()
        with self.assertRaises(StrangerError):
            await self.stranger.send(message)
        sender.send.assert_called_once_with(message)
        sender.send_notification.assert_not_called()

    async def test_send_to_partner__chatting_stranger(self):
        self.stranger.get_partner = Mock(return_value=self.stranger2)
        self.stranger2.send = CoroutineMock()
        message = Mock()
        talk = Mock()
        self.stranger.get_talk = Mock(return_value=talk)
        await self.stranger.send_to_partner(message)
        self.stranger2.send.assert_called_once_with(message)
        talk.increment_sent.assert_called_once_with(self.stranger)

    async def test_send_to_partner__not_chatting_stranger(self):
        self.stranger.get_partner = Mock(return_value=None)
        with self.assertRaises(MissingPartnerError):
            await self.stranger.send_to_partner(Mock())

    async def test_send_to_partner__telegram_error(self):
        self.stranger.get_partner = Mock(return_value=self.stranger2)
        self.stranger2.send = CoroutineMock(side_effect=TelegramError('', 100))
        message = Mock()
        with self.assertRaises(TelegramError):
            await self.stranger.send_to_partner(message)

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
        from randtalkbot.errors import EmptyLanguagesError
        with self.assertRaises(EmptyLanguagesError):
            self.stranger.set_languages([])

    @asynctest.ignore_loop
    def test_set_languages__same_empty(self):
        from randtalkbot.errors import EmptyLanguagesError
        self.stranger.languages = None
        with self.assertRaises(EmptyLanguagesError):
            self.stranger.set_languages(['same'])

    @asynctest.ignore_loop
    def test_set_languages__too_much(self):
        from randtalkbot.errors import StrangerError
        self.stranger.languages = None
        with self.assertRaises(StrangerError):
            # 7 languages.
            self.stranger.set_languages(['ru', 'en', 'it', 'fr', 'de', 'pt', 'po'])

    @patch('randtalkbot.stranger.datetime')
    async def test_set_looking_for_partner__ok(self, datetime_mock):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.set_partner = CoroutineMock()
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(1980, 1, 1)
        await self.stranger.set_looking_for_partner()
        sender.send_notification.assert_called_once_with('Looking for a stranger for you.')
        self.assertEqual(self.stranger.looking_for_partner_from, datetime.datetime(1980, 1, 1))
        self.stranger.set_partner.assert_called_once_with(None)

    @patch('randtalkbot.stranger.datetime')
    async def test_set_looking_for_partner__looking_for_partner_already(self, datetime_mock):
        sender = CoroutineMock()
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.set_partner = CoroutineMock()
        self.stranger.looking_for_partner_from = datetime.datetime(1970, 1, 1)
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(1980, 1, 1)
        await self.stranger.set_looking_for_partner()
        self.assertEqual(self.stranger.looking_for_partner_from, datetime.datetime(1970, 1, 1))
        self.stranger.set_partner.assert_called_once_with(None)

    @patch('randtalkbot.stranger.datetime')
    async def test_set_looking_for_partner__bot_was_blocked(self, datetime_mock):
        sender = CoroutineMock()
        sender.send_notification.side_effect = TelegramError('', 0)
        self.stranger.get_sender = Mock(return_value=sender)
        self.stranger.set_partner = CoroutineMock()
        datetime_mock.datetime.utcnow.return_value = 'foo_time'
        await self.stranger.set_looking_for_partner()
        sender.send_notification.assert_called_once_with('Looking for a stranger for you.')
        self.assertEqual(self.stranger.looking_for_partner_from, None)
        self.stranger.set_partner.assert_called_once_with(None)

    @patch('randtalkbot.stranger.datetime', Mock())
    @patch('randtalkbot.talk.Talk', Mock())
    async def test_set_partner__chatting_stranger(self):
        from randtalkbot.stranger import datetime
        from randtalkbot.talk import Talk
        self.stranger3.looking_for_partner_from = 'foo_searched_since'
        self.stranger3.save = Mock()
        self.stranger2.get_partner = Mock(return_value=self.stranger)
        self.stranger2.kick = CoroutineMock()
        self.stranger.get_partner = Mock(return_value=self.stranger2)
        self.stranger._partner = self.stranger2
        talk = Mock()
        self.stranger._talk = talk
        datetime.datetime.utcnow.return_value = 'now'
        new_talk = Mock()
        Talk.create.return_value = new_talk
        await self.stranger.set_partner(self.stranger3)
        self.stranger2.kick.assert_called_once_with()
        self.assertEqual(talk.end, 'now')
        talk.save.assert_called_once_with()
        Talk.create.assert_called_once_with(
            partner1=self.stranger,
            partner2=self.stranger3,
            searched_since='foo_searched_since',
            )
        self.assertEqual(self.stranger._partner, self.stranger3)
        self.assertEqual(self.stranger._talk, new_talk)
        self.assertEqual(self.stranger3._partner, self.stranger)
        self.assertEqual(self.stranger3._talk, new_talk)
        self.assertEqual(self.stranger3.looking_for_partner_from, None)
        self.stranger3.save.assert_called_once_with()

    async def test_set_partner__chatting_stranger_none(self):
        self.stranger2.get_partner = Mock(return_value=self.stranger)
        self.stranger2.kick = CoroutineMock()
        self.stranger.get_partner = Mock(return_value=self.stranger2)
        self.stranger._partner = self.stranger2
        self.stranger._talk = Mock()
        await self.stranger.set_partner(None)
        self.stranger2.kick.assert_called_once_with()
        self.assertEqual(self.stranger._partner, None)
        self.assertEqual(self.stranger._talk, None)

    async def test_set_partner__same(self):
        self.stranger.get_partner = Mock(return_value=self.stranger2)
        self.stranger.save = Mock()
        await self.stranger.set_partner(self.stranger2)
        self.stranger.save.assert_called_once_with()

    @patch('randtalkbot.stranger.datetime', Mock())
    @patch('randtalkbot.talk.Talk', Mock())
    async def test_set_partner__buggy_chatting_stranger(self):
        from randtalkbot.stranger import datetime
        from randtalkbot.talk import Talk
        self.stranger3.looking_for_partner_from = 'foo_searched_since'
        self.stranger3.save = Mock()
        self.stranger2.get_partner = Mock(return_value=self.stranger4)
        self.stranger2.kick = CoroutineMock()
        self.stranger.get_partner = Mock(return_value=self.stranger2)
        self.stranger._partner = self.stranger2
        self.stranger.looking_for_partner_from = 'bar_searched_since'
        self.looking_for_partner_from = None
        talk = Mock()
        self.stranger._talk = talk
        datetime.datetime.utcnow.return_value = 'now'
        new_talk = Mock()
        Talk.create.return_value = new_talk
        await self.stranger.set_partner(self.stranger3)
        self.stranger2.kick.assert_not_called()
        self.assertEqual(self.stranger.looking_for_partner_from, None)

    @patch('randtalkbot.stranger.datetime', Mock())
    @patch('randtalkbot.talk.Talk', Mock())
    async def test_set_partner__not_chatting_stranger(self):
        from randtalkbot.stranger import datetime
        from randtalkbot.talk import Talk
        self.stranger3.looking_for_partner_from = 'foo_searched_since'
        self.stranger3.save = Mock()
        self.stranger.get_partner = Mock(return_value=None)
        self.stranger._partner = None
        self.stranger.bonus_count = 1000
        self.looking_for_partner_from = None
        talk = Mock()
        self.stranger._talk = talk
        datetime.datetime.utcnow.return_value = 'now'
        new_talk = Mock()
        Talk.create.return_value = new_talk
        await self.stranger.set_partner(self.stranger3)
        self.assertEqual(self.stranger.bonus_count, 1000)

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
        from randtalkbot.errors import SexError
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
        from randtalkbot.errors import SexError
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
