# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
from unittest.mock import create_autospec
import asynctest
from asynctest.mock import call, patch, Mock, CoroutineMock
from peewee import DatabaseError, DoesNotExist, SqliteDatabase
from randtalkbot import stranger
from randtalkbot.errors import StrangerError, StrangerServiceError, \
    PartnerObtainingError
from randtalkbot.stranger import Stranger
from randtalkbot.stranger_service import StrangerService


class TestStrangerService(asynctest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestStrangerService, self).__init__(*args, **kwargs)
        self.database = SqliteDatabase(':memory:')

    def setUp(self):
        self.stranger_service = StrangerService()
        stranger.DATABASE_PROXY.initialize(self.database)
        self.database.create_tables([Stranger])
        self.stranger_0 = Stranger.create(
            invitation='foo',
            languages='["foo"]',
            telegram_id=27183,
            sex='female',
            partner_sex='male',
            )
        self.stranger_1 = Stranger.create(
            invitation='bar',
            languages='["foo"]',
            telegram_id=31416,
            sex='male',
            partner_sex='female',
            )
        self.stranger_2 = Stranger.create(
            invitation='baz',
            languages='["foo"]',
            telegram_id=23571,
            sex='male',
            partner_sex='female',
            )
        self.stranger_3 = Stranger.create(
            invitation='zen',
            languages='["foo"]',
            telegram_id=11317,
            sex='male',
            partner_sex='female',
            )
        self.stranger_4 = Stranger.create(
            invitation='zig',
            languages='["foo"]',
            telegram_id=19232,
            sex='male',
            partner_sex='female',
            )
        self.stranger_5 = Stranger.create(
            invitation='zam',
            languages='["foo"]',
            telegram_id=93137,
            sex='male',
            partner_sex='female',
            )
        self.stranger_6 = Stranger.create(
            invitation='zom',
            languages=None,
            telegram_id=0,
            sex=None,
            partner_sex=None
            )

    def tearDown(self):
        self.database.drop_tables([Stranger])

    @patch('randtalkbot.stranger_service.StrangerService.__init__', Mock(return_value=None))
    @asynctest.ignore_loop
    def test_get_instance(self):
        self.assertEqual(StrangerService.get_instance(), StrangerService._instance)
        StrangerService.__init__.assert_not_called()
        del StrangerService._instance
        instance = StrangerService.get_instance()
        self.assertEqual(StrangerService._instance, instance)
        self.assertTrue(StrangerService.__init__.called)

    @asynctest.ignore_loop
    def test_get_full_strangers(self):
        full_strangers = list(self.stranger_service.get_full_strangers())
        self.assertEqual(len(full_strangers), 6)

    @patch('randtalkbot.stranger_service.Stranger', create_autospec(Stranger))
    @asynctest.ignore_loop
    def test_get_or_create_stranger__database_error(self):
        from randtalkbot.stranger_service import Stranger as stranger_cls_mock
        self.stranger_service.get_cached_stranger = Mock()
        stranger_cls_mock.get.side_effect = DatabaseError()
        with self.assertRaises(StrangerServiceError):
            self.stranger_service.get_or_create_stranger(31416)

    @patch('randtalkbot.stranger_service.Stranger.get', Mock(side_effect=DatabaseError()))
    @asynctest.ignore_loop
    def test_get_stranger__database_error(self):
        with self.assertRaises(StrangerServiceError):
            self.stranger_service.get_stranger(31416)

    @patch('randtalkbot.stranger_service.INVITATION_LENGTH', 3)
    @asynctest.ignore_loop
    def test_get_stranger_by_invitation__wrong_length(self):
        self.stranger_service.get_cached_stranger = Mock()
        self.stranger_service.get_cached_stranger.return_value = 'cached_stranger'
        with self.assertRaises(StrangerServiceError):
            self.stranger_service.get_stranger_by_invitation('booo')
        self.stranger_service.get_cached_stranger.assert_not_called()

    @patch('randtalkbot.stranger_service.INVITATION_LENGTH', 3)
    @patch('randtalkbot.stranger_service.Stranger.get', Mock(side_effect=DatabaseError()))
    @asynctest.ignore_loop
    def test_get_stranger_by_invitation__database_error(self):
        with self.assertRaises(StrangerServiceError):
            self.stranger_service.get_stranger_by_invitation('zam')

    @patch('randtalkbot.talk.Talk', Mock())
    @asynctest.ignore_loop
    def test_match_partner__does_not_exist(self):
        from randtalkbot.talk import Talk
        Talk.get_last_partners_ids.return_value = []
        self.stranger_0.languages = '["boo"]'
        self.stranger_0.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        with self.assertRaises(PartnerObtainingError):
            self.stranger_service._match_partner(self.stranger_0)
        self.stranger_service.get_cached_stranger.assert_not_called()

    async def test_match_partner__stranger_error(self):
        stranger_mock = CoroutineMock()
        partner = CoroutineMock()
        partner.id = 31416
        self.stranger_service._match_partner = Mock(return_value=partner)
        self.stranger_service._locked_strangers_ids = Mock()
        self.stranger_service.get_stranger_by_id = Mock(return_value=stranger_mock)
        stranger_mock.notify_partner_found.side_effect = StrangerError()
        with self.assertRaises(StrangerServiceError):
            await self.stranger_service.match_partner(27183)
        self.stranger_service._locked_strangers_ids.discard. \
            assert_called_once_with(31416)
        stranger_mock.set_partner.assert_not_called()

    async def test_match_partner__first_partner_has_blocked_the_bot(self):
        stranger_mock = CoroutineMock()
        partner = CoroutineMock()
        partner.id = 31416
        self.stranger_service._match_partner = Mock(return_value=partner)
        self.stranger_service._locked_strangers_ids = Mock()
        self.stranger_service.get_stranger_by_id = Mock(return_value=stranger_mock)
        partner.notify_partner_found.side_effect = [StrangerError(), None]
        stranger_id = 271828
        await self.stranger_service.match_partner(stranger_id)
        self.assertEqual(
            self.stranger_service._locked_strangers_ids.discard.call_args_list,
            [
                call(partner.id),
                call(partner.id),
                ],
            )
        self.assertEqual(
            partner.notify_partner_found.call_args_list,
            [
                call(stranger_id),
                call(stranger_id),
                ],
            )
        stranger_mock.notify_partner_found.assert_called_once_with(partner.id)

    async def test_match_partner__partner_obtaining_error(self):
        stranger_mock = CoroutineMock()
        self.stranger_service._match_partner = Mock(
            side_effect=PartnerObtainingError,
            )
        self.stranger_service.get_stranger_by_id = Mock(return_value=stranger_mock)
        with self.assertRaises(PartnerObtainingError):
            await self.stranger_service.match_partner(271828)
