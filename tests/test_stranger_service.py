# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asynctest
import datetime
import unittest
from asynctest.mock import call, patch, Mock, CoroutineMock
from peewee import *
from playhouse.test_utils import test_database
from randtalkbot import stranger
from randtalkbot.errors import StrangerError, StrangerServiceError, \
    PartnerObtainingError
from randtalkbot.stranger import Stranger
from randtalkbot.stranger_service import StrangerService
from unittest.mock import create_autospec


class TestStrangerService(asynctest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestStrangerService, self).__init__(*args, **kwargs)
        self.database = SqliteDatabase(':memory:')

    def setUp(self):
        self.stranger_service = StrangerService()
        stranger.database_proxy.initialize(self.database)
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
    def test_get_cached_stranger__cached(self):
        cached_stranger = Mock()
        cached_stranger.id = 31416
        self.stranger_service._strangers_cache[31416] = cached_stranger
        stranger = Mock()
        stranger.id = 31416
        self.assertEqual(self.stranger_service.get_cached_stranger(stranger), cached_stranger)

    @asynctest.ignore_loop
    def test_get_cached_stranger__not_cached(self):
        stranger = Mock()
        stranger.id = 31416
        self.assertEqual(self.stranger_service.get_cached_stranger(stranger), stranger)
        self.assertEqual(self.stranger_service._strangers_cache[31416], stranger)

    @asynctest.ignore_loop
    def test_get_cache_size(self):
        self.assertEqual(self.stranger_service.get_cache_size(), 0)
        self.stranger_service._strangers_cache = {
            0: 0,
            1: 1,
            }
        self.assertEqual(self.stranger_service.get_cache_size(), 2)

    @asynctest.ignore_loop
    def test_get_full_strangers(self):
        full_strangers = list(self.stranger_service.get_full_strangers())
        self.assertEqual(len(full_strangers), 6)

    @patch('randtalkbot.stranger_service.Stranger', create_autospec(Stranger))
    @asynctest.ignore_loop
    def test_get_or_create_stranger__stranger_found(self):
        from randtalkbot.stranger_service import Stranger
        Stranger.get.return_value = self.stranger_0
        self.stranger_service.get_cached_stranger = Mock()
        self.stranger_service.get_cached_stranger.return_value = 'cached_stranger'
        self.assertEqual(
            self.stranger_service.get_or_create_stranger(31416),
            'cached_stranger',
            )
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_0)

    @patch('randtalkbot.stranger_service.Stranger', create_autospec(Stranger))
    @asynctest.ignore_loop
    def test_get_or_create_stranger__stranger_not_found(self):
        from randtalkbot.stranger_service import Stranger
        Stranger.get.side_effect = DoesNotExist()
        Stranger.create.return_value = self.stranger_0
        self.stranger_service.get_cached_stranger = Mock()
        self.stranger_service.get_cached_stranger.return_value = 'cached_stranger'
        self.assertEqual(
            self.stranger_service.get_or_create_stranger(31416),
            'cached_stranger',
            )
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_0)

    @patch('randtalkbot.stranger_service.Stranger', create_autospec(Stranger))
    @asynctest.ignore_loop
    def test_get_or_create_stranger__database_error(self):
        from randtalkbot.stranger_service import Stranger
        self.stranger_service.get_cached_stranger = Mock()
        Stranger.get.side_effect = DatabaseError()
        with self.assertRaises(StrangerServiceError):
            self.stranger_service.get_or_create_stranger(31416)

    @asynctest.ignore_loop
    def test_get_stranger__stranger_found(self):
        self.stranger_service.get_cached_stranger = Mock()
        self.stranger_service.get_cached_stranger.return_value = 'cached_stranger'
        self.assertEqual(
            self.stranger_service.get_stranger(31416),
            'cached_stranger',
            )
        self.assertEqual(
            self.stranger_service.get_cached_stranger.call_args[0][0].id,
            self.stranger_1.id,
            )

    @patch('randtalkbot.stranger_service.Stranger.get', Mock(side_effect=DatabaseError()))
    @asynctest.ignore_loop
    def test_get_stranger__database_error(self):
        with self.assertRaises(StrangerServiceError):
            self.stranger_service.get_stranger(31416)

    @patch('randtalkbot.stranger_service.INVITATION_LENGTH', 3)
    @asynctest.ignore_loop
    def test_get_stranger_by_invitation__ok(self):
        self.stranger_service.get_cached_stranger = Mock()
        self.stranger_service.get_cached_stranger.return_value = 'cached_stranger'
        self.assertEqual(
            self.stranger_service.get_stranger_by_invitation('zam'),
            'cached_stranger',
            )
        self.assertEqual(
            self.stranger_service.get_cached_stranger.call_args[0][0].id,
            self.stranger_5.id,
            )

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
    def test_match_partner__returns_the_longest_waiting_stranger_1(self):
        from randtalkbot.talk import Talk
        Talk.get_last_partners_ids.return_value = []
        self.stranger_0.languages = '["foo", "bar", "baz"]'
        self.stranger_0.save()
        # The longest waiting stranger with max bonus count.
        self.stranger_1.looking_for_partner_from = datetime.datetime(1990, 1, 1)
        self.stranger_1.bonus_count = 1
        self.stranger_1.save()
        self.stranger_2.looking_for_partner_from = datetime.datetime(1980, 1, 1)
        self.stranger_2.save()
        self.stranger_3.looking_for_partner_from = datetime.datetime(1991, 1, 1)
        self.stranger_3.bonus_count = 1
        self.stranger_3.save()
        self.stranger_4.looking_for_partner_from = datetime.datetime(1993, 1, 1)
        self.stranger_4.save()
        self.stranger_5.looking_for_partner_from = datetime.datetime(1992, 1, 1)
        self.stranger_5.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        self.assertEqual(self.stranger_service._match_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_1)

    @patch('randtalkbot.talk.Talk', Mock())
    @asynctest.ignore_loop
    def test_match_partner__returns_the_longest_waiting_stranger_2(self):
        from randtalkbot.talk import Talk
        Talk.get_last_partners_ids.return_value = []
        self.stranger_0.languages = '["foo", "bar", "baz"]'
        self.stranger_0.save()
        self.stranger_1.looking_for_partner_from = datetime.datetime(1990, 1, 1)
        self.stranger_1.save()
        self.stranger_2.looking_for_partner_from = datetime.datetime(1994, 1, 1)
        self.stranger_2.bonus_count = 1
        self.stranger_2.save()
        self.stranger_3.looking_for_partner_from = datetime.datetime(1991, 1, 1)
        self.stranger_3.save()
        # The longest waiting stranger with max bonus count.
        self.stranger_4.looking_for_partner_from = datetime.datetime(1993, 1, 1)
        self.stranger_4.bonus_count = 1
        self.stranger_4.save()
        self.stranger_5.looking_for_partner_from = datetime.datetime(1992, 1, 1)
        self.stranger_5.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        self.assertEqual(self.stranger_service._match_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_4)

    @patch('randtalkbot.talk.Talk', Mock())
    @asynctest.ignore_loop
    def test_match_partner__returns_stranger_with_proper_sex_1(self):
        from randtalkbot.talk import Talk
        Talk.get_last_partners_ids.return_value = []
        self.stranger_0.languages = '["foo", "bar", "baz"]'
        self.stranger_0.save()
        self.stranger_1.sex = 'female'
        self.stranger_1.partner_sex = 'female'
        self.stranger_1.looking_for_partner_from = datetime.datetime(1990, 1, 1)
        self.stranger_1.save()
        self.stranger_2.sex = 'female'
        self.stranger_2.partner_sex = 'female'
        self.stranger_2.looking_for_partner_from = datetime.datetime(1980, 1, 1)
        self.stranger_2.save()
        # Stranger with proper sex.
        self.stranger_3.sex = 'male'
        self.stranger_3.partner_sex = 'female'
        self.stranger_3.looking_for_partner_from = datetime.datetime(1991, 1, 1)
        self.stranger_3.save()
        self.stranger_4.sex = 'female'
        self.stranger_4.partner_sex = 'female'
        self.stranger_4.looking_for_partner_from = datetime.datetime(1993, 1, 1)
        self.stranger_4.save()
        self.stranger_5.sex = 'female'
        self.stranger_5.partner_sex = 'female'
        self.stranger_5.looking_for_partner_from = datetime.datetime(1992, 1, 1)
        self.stranger_5.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        self.assertEqual(self.stranger_service._match_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_3)

    @patch('randtalkbot.talk.Talk', Mock())
    @asynctest.ignore_loop
    def test_match_partner__returns_stranger_with_proper_sex_2(self):
        from randtalkbot.talk import Talk
        Talk.get_last_partners_ids.return_value = []
        self.stranger_0.languages = '["foo", "bar", "baz"]'
        self.stranger_0.save()
        self.stranger_1.sex = 'female'
        self.stranger_1.partner_sex = 'female'
        self.stranger_1.looking_for_partner_from = datetime.datetime(1990, 1, 1)
        self.stranger_1.save()
        self.stranger_2.sex = 'female'
        self.stranger_2.partner_sex = 'female'
        self.stranger_2.looking_for_partner_from = datetime.datetime(1980, 1, 1)
        self.stranger_2.save()
        self.stranger_3.sex = 'female'
        self.stranger_3.partner_sex = 'female'
        self.stranger_3.looking_for_partner_from = datetime.datetime(1991, 1, 1)
        self.stranger_3.save()
        # Stranger with proper sex.
        self.stranger_4.sex = 'male'
        self.stranger_4.partner_sex = 'female'
        self.stranger_4.looking_for_partner_from = datetime.datetime(1993, 1, 1)
        self.stranger_4.save()
        self.stranger_5.sex = 'female'
        self.stranger_5.partner_sex = 'female'
        self.stranger_5.looking_for_partner_from = datetime.datetime(1992, 1, 1)
        self.stranger_5.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        self.assertEqual(self.stranger_service._match_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_4)

    @patch('randtalkbot.talk.Talk', Mock())
    @asynctest.ignore_loop
    def test_match_partner__returns_stranger_looking_for_proper_sex_1(self):
        from randtalkbot.talk import Talk
        Talk.get_last_partners_ids.return_value = []
        self.stranger_0.languages = '["foo", "bar", "baz"]'
        self.stranger_0.save()
        self.stranger_1.sex = 'male'
        self.stranger_1.partner_sex = 'male'
        self.stranger_1.looking_for_partner_from = datetime.datetime(1990, 1, 1)
        self.stranger_1.save()
        self.stranger_2.sex = 'male'
        self.stranger_2.partner_sex = 'male'
        self.stranger_2.looking_for_partner_from = datetime.datetime(1980, 1, 1)
        self.stranger_2.save()
        # Stranger looking for proper sex.
        self.stranger_3.sex = 'male'
        self.stranger_3.partner_sex = 'female'
        self.stranger_3.looking_for_partner_from = datetime.datetime(1991, 1, 1)
        self.stranger_3.save()
        self.stranger_4.sex = 'male'
        self.stranger_4.partner_sex = 'male'
        self.stranger_4.looking_for_partner_from = datetime.datetime(1993, 1, 1)
        self.stranger_4.save()
        self.stranger_5.sex = 'male'
        self.stranger_5.partner_sex = 'male'
        self.stranger_5.looking_for_partner_from = datetime.datetime(1992, 1, 1)
        self.stranger_5.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        self.assertEqual(self.stranger_service._match_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_3)

    @patch('randtalkbot.talk.Talk', Mock())
    @asynctest.ignore_loop
    def test_match_partner__returns_stranger_looking_for_proper_sex_2(self):
        from randtalkbot.talk import Talk
        Talk.get_last_partners_ids.return_value = []
        self.stranger_0.languages = '["foo", "bar", "baz"]'
        self.stranger_0.save()
        self.stranger_1.sex = 'male'
        self.stranger_1.partner_sex = 'male'
        self.stranger_1.looking_for_partner_from = datetime.datetime(1990, 1, 1)
        self.stranger_1.save()
        self.stranger_2.sex = 'male'
        self.stranger_2.partner_sex = 'male'
        self.stranger_2.looking_for_partner_from = datetime.datetime(1980, 1, 1)
        self.stranger_2.save()
        self.stranger_3.sex = 'male'
        self.stranger_3.partner_sex = 'male'
        self.stranger_3.looking_for_partner_from = datetime.datetime(1991, 1, 1)
        self.stranger_3.save()
        # Stranger looking for proper sex.
        self.stranger_4.sex = 'male'
        self.stranger_4.partner_sex = 'female'
        self.stranger_4.looking_for_partner_from = datetime.datetime(1993, 1, 1)
        self.stranger_4.save()
        self.stranger_5.sex = 'male'
        self.stranger_5.partner_sex = 'male'
        self.stranger_5.looking_for_partner_from = datetime.datetime(1992, 1, 1)
        self.stranger_5.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        self.assertEqual(self.stranger_service._match_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_4)

    @patch('randtalkbot.talk.Talk', Mock())
    @asynctest.ignore_loop
    def test_match_partner__filters_strangers_when_stranger_partner_sex_isnt_specified_1(self):
        from randtalkbot.talk import Talk
        Talk.get_last_partners_ids.return_value = []
        self.stranger_0.languages = '["foo", "bar", "baz"]'
        self.stranger_0.partner_sex = 'not_specified'
        self.stranger_0.save()
        self.stranger_1.sex = 'male'
        self.stranger_1.partner_sex = 'male'
        self.stranger_1.looking_for_partner_from = datetime.datetime(1990, 1, 1)
        self.stranger_1.save()
        self.stranger_2.sex = 'male'
        self.stranger_2.partner_sex = 'male'
        self.stranger_2.looking_for_partner_from = datetime.datetime(1980, 1, 1)
        self.stranger_2.save()
        # Stranger looking for proper sex.
        self.stranger_3.sex = 'male'
        self.stranger_3.partner_sex = 'female'
        self.stranger_3.looking_for_partner_from = datetime.datetime(1991, 1, 1)
        self.stranger_3.save()
        self.stranger_4.sex = 'male'
        self.stranger_4.partner_sex = 'male'
        self.stranger_4.looking_for_partner_from = datetime.datetime(1993, 1, 1)
        self.stranger_4.save()
        self.stranger_5.sex = 'male'
        self.stranger_5.partner_sex = 'male'
        self.stranger_5.looking_for_partner_from = datetime.datetime(1992, 1, 1)
        self.stranger_5.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        self.assertEqual(self.stranger_service._match_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_3)

    @patch('randtalkbot.talk.Talk', Mock())
    @asynctest.ignore_loop
    def test_match_partner__filters_strangers_when_stranger_partner_sex_isnt_specified_2(self):
        from randtalkbot.talk import Talk
        Talk.get_last_partners_ids.return_value = []
        self.stranger_0.languages = '["foo", "bar", "baz"]'
        self.stranger_0.partner_sex = 'not_specified'
        self.stranger_0.save()
        # Stranger looking for proper sex.
        self.stranger_1.sex = 'male'
        self.stranger_1.partner_sex = 'female'
        self.stranger_1.looking_for_partner_from = datetime.datetime(1990, 1, 1)
        self.stranger_1.save()
        self.stranger_2.sex = 'male'
        self.stranger_2.partner_sex = 'male'
        self.stranger_2.looking_for_partner_from = datetime.datetime(1980, 1, 1)
        self.stranger_2.save()
        self.stranger_3.sex = 'male'
        self.stranger_3.partner_sex = 'male'
        self.stranger_3.looking_for_partner_from = datetime.datetime(1991, 1, 1)
        self.stranger_3.save()
        self.stranger_4.sex = 'male'
        self.stranger_4.partner_sex = 'male'
        self.stranger_4.looking_for_partner_from = datetime.datetime(1993, 1, 1)
        self.stranger_4.save()
        self.stranger_5.sex = 'male'
        self.stranger_5.partner_sex = 'male'
        self.stranger_5.looking_for_partner_from = datetime.datetime(1992, 1, 1)
        self.stranger_5.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        self.assertEqual(self.stranger_service._match_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_1)

    @patch('randtalkbot.talk.Talk', Mock())
    @asynctest.ignore_loop
    def test_match_partner__returns_stranger_looking_for_any_sex_in_case_of_rare_sex_1(self):
        from randtalkbot.talk import Talk
        Talk.get_last_partners_ids.return_value = []
        self.stranger_0.languages = '["foo", "bar", "baz"]'
        self.stranger_0.save()
        self.stranger_1.sex = 'male'
        self.stranger_1.partner_sex = 'male'
        self.stranger_1.looking_for_partner_from = datetime.datetime(1990, 1, 1)
        self.stranger_1.save()
        self.stranger_2.sex = 'male'
        self.stranger_2.partner_sex = 'male'
        self.stranger_2.looking_for_partner_from = datetime.datetime(1980, 1, 1)
        self.stranger_2.save()
        # Stranger looking for any sex.
        self.stranger_3.sex = 'male'
        self.stranger_3.partner_sex = 'not_specified'
        self.stranger_3.looking_for_partner_from = datetime.datetime(1991, 1, 1)
        self.stranger_3.save()
        self.stranger_4.sex = 'male'
        self.stranger_4.partner_sex = 'male'
        self.stranger_4.looking_for_partner_from = datetime.datetime(1993, 1, 1)
        self.stranger_4.save()
        self.stranger_5.sex = 'male'
        self.stranger_5.partner_sex = 'male'
        self.stranger_5.looking_for_partner_from = datetime.datetime(1992, 1, 1)
        self.stranger_5.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        self.assertEqual(self.stranger_service._match_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_3)

    @patch('randtalkbot.talk.Talk', Mock())
    @asynctest.ignore_loop
    def test_match_partner__returns_stranger_looking_for_any_sex_in_case_of_rare_sex_2(self):
        from randtalkbot.talk import Talk
        Talk.get_last_partners_ids.return_value = []
        self.stranger_0.languages = '["foo", "bar", "baz"]'
        self.stranger_0.save()
        self.stranger_1.sex = 'male'
        self.stranger_1.partner_sex = 'male'
        self.stranger_1.looking_for_partner_from = datetime.datetime(1990, 1, 1)
        self.stranger_1.save()
        self.stranger_2.sex = 'male'
        self.stranger_2.partner_sex = 'male'
        self.stranger_2.looking_for_partner_from = datetime.datetime(1980, 1, 1)
        self.stranger_2.save()
        self.stranger_3.sex = 'male'
        self.stranger_3.partner_sex = 'male'
        self.stranger_3.looking_for_partner_from = datetime.datetime(1991, 1, 1)
        self.stranger_3.save()
        # Stranger looking for any sex.
        self.stranger_4.sex = 'male'
        self.stranger_4.partner_sex = 'not_specified'
        self.stranger_4.looking_for_partner_from = datetime.datetime(1993, 1, 1)
        self.stranger_4.save()
        self.stranger_5.sex = 'male'
        self.stranger_5.partner_sex = 'male'
        self.stranger_5.looking_for_partner_from = datetime.datetime(1992, 1, 1)
        self.stranger_5.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        self.assertEqual(self.stranger_service._match_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_4)

    @patch('randtalkbot.talk.Talk', Mock())
    @asynctest.ignore_loop
    def test_match_partner__returns_stranger_looking_for_any_sex_if_sex_is_not_specified_1(self):
        from randtalkbot.talk import Talk
        Talk.get_last_partners_ids.return_value = []
        self.stranger_0.languages = '["foo", "bar", "baz"]'
        self.stranger_0.sex = 'not_specified'
        self.stranger_0.partner_sex = 'not_specified'
        self.stranger_0.save()
        self.stranger_1.sex = 'male'
        self.stranger_1.partner_sex = 'male'
        self.stranger_1.looking_for_partner_from = datetime.datetime(1990, 1, 1)
        self.stranger_1.save()
        self.stranger_2.sex = 'male'
        self.stranger_2.partner_sex = 'male'
        self.stranger_2.looking_for_partner_from = datetime.datetime(1980, 1, 1)
        self.stranger_2.save()
        # Stranger looking for any sex.
        self.stranger_3.sex = 'male'
        self.stranger_3.partner_sex = 'not_specified'
        self.stranger_3.looking_for_partner_from = datetime.datetime(1991, 1, 1)
        self.stranger_3.save()
        self.stranger_4.sex = 'male'
        self.stranger_4.partner_sex = 'male'
        self.stranger_4.looking_for_partner_from = datetime.datetime(1993, 1, 1)
        self.stranger_4.save()
        self.stranger_5.sex = 'male'
        self.stranger_5.partner_sex = 'male'
        self.stranger_5.looking_for_partner_from = datetime.datetime(1992, 1, 1)
        self.stranger_5.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        self.assertEqual(self.stranger_service._match_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_3)

    @patch('randtalkbot.talk.Talk', Mock())
    @asynctest.ignore_loop
    def test_match_partner__returns_stranger_looking_for_any_sex_if_sex_is_not_specified_2(self):
        from randtalkbot.talk import Talk
        Talk.get_last_partners_ids.return_value = []
        self.stranger_0.languages = '["foo", "bar", "baz"]'
        self.stranger_0.sex = 'not_specified'
        self.stranger_0.partner_sex = 'not_specified'
        self.stranger_0.save()
        self.stranger_1.sex = 'male'
        self.stranger_1.partner_sex = 'male'
        self.stranger_1.looking_for_partner_from = datetime.datetime(1990, 1, 1)
        self.stranger_1.save()
        self.stranger_2.sex = 'male'
        self.stranger_2.partner_sex = 'male'
        self.stranger_2.looking_for_partner_from = datetime.datetime(1980, 1, 1)
        self.stranger_2.save()
        self.stranger_3.sex = 'male'
        self.stranger_3.partner_sex = 'male'
        self.stranger_3.looking_for_partner_from = datetime.datetime(1991, 1, 1)
        self.stranger_3.save()
        # Stranger looking for any sex.
        self.stranger_4.sex = 'male'
        self.stranger_4.partner_sex = 'not_specified'
        self.stranger_4.looking_for_partner_from = datetime.datetime(1993, 1, 1)
        self.stranger_4.save()
        self.stranger_5.sex = 'male'
        self.stranger_5.partner_sex = 'male'
        self.stranger_5.looking_for_partner_from = datetime.datetime(1992, 1, 1)
        self.stranger_5.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        self.assertEqual(self.stranger_service._match_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_4)

    @patch('randtalkbot.talk.Talk', Mock())
    @asynctest.ignore_loop
    def test_match_partner__returns_stranger_speaking_on_highest_priority_language_1(self):
        from randtalkbot.talk import Talk
        Talk.get_last_partners_ids.return_value = []
        self.stranger_0.languages = '["foo", "bar", "baz", "boo", "bim"]'
        self.stranger_0.save()
        self.stranger_1.languages = '["BAR", "baz", "FOO"]'
        self.stranger_1.looking_for_partner_from = datetime.datetime(1990, 1, 1)
        self.stranger_1.save()
        self.stranger_2.languages = '["boo"]'
        self.stranger_2.looking_for_partner_from = datetime.datetime(1980, 1, 1)
        self.stranger_2.save()
        # Stranger speaking on highest priority language (foo).
        self.stranger_3.languages = '["BAR", "BAZ", "foo"]'
        self.stranger_3.looking_for_partner_from = datetime.datetime(1991, 1, 1)
        self.stranger_3.save()
        self.stranger_4.languages = '["BAR", "BAZ", "boo", "BIM"]'
        self.stranger_4.looking_for_partner_from = datetime.datetime(1993, 1, 1)
        self.stranger_4.save()
        self.stranger_5.languages = '["bar"]'
        self.stranger_5.looking_for_partner_from = datetime.datetime(1992, 1, 1)
        self.stranger_5.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        self.assertEqual(self.stranger_service._match_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_3)

    @patch('randtalkbot.talk.Talk', Mock())
    @asynctest.ignore_loop
    def test_match_partner__returns_stranger_speaking_on_highest_priority_language_2(self):
        from randtalkbot.talk import Talk
        Talk.get_last_partners_ids.return_value = []
        self.stranger_0.languages = '["foo", "bar", "baz", "boo", "bim"]'
        self.stranger_0.save()
        self.stranger_1.languages = '["BAR", "baz", "FOO"]'
        self.stranger_1.looking_for_partner_from = datetime.datetime(1990, 1, 1)
        self.stranger_1.save()
        self.stranger_2.languages = '["boo"]'
        self.stranger_2.looking_for_partner_from = datetime.datetime(1980, 1, 1)
        self.stranger_2.save()
        self.stranger_3.languages = '["BAR", "BAZ", "bim"]'
        self.stranger_3.looking_for_partner_from = datetime.datetime(1991, 1, 1)
        self.stranger_3.save()
        # Stranger speaking on highest priority language (foo).
        self.stranger_4.languages = '["BAR", "BAZ", "BOO", "foo", "BIM"]'
        self.stranger_4.looking_for_partner_from = datetime.datetime(1993, 1, 1)
        self.stranger_4.save()
        self.stranger_5.languages = '["bar"]'
        self.stranger_5.looking_for_partner_from = datetime.datetime(1992, 1, 1)
        self.stranger_5.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        self.assertEqual(self.stranger_service._match_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_4)

    @patch('randtalkbot.talk.Talk', Mock())
    @asynctest.ignore_loop
    def test_match_partner__returns_fresh_stranger_1(self):
        from randtalkbot.talk import Talk
        Talk.get_last_partners_ids.return_value = [self.stranger_2.id, 11111, 22222]
        self.stranger_0.languages = '["foo", "bar", "baz", "boo", "bim"]'
        self.stranger_0.save()
        self.stranger_1.languages = '["BAR", "baz", "FOO"]'
        self.stranger_1.looking_for_partner_from = datetime.datetime(1990, 1, 1)
        self.stranger_1.save()
        # Stranger speaking on highest priority language, NOT FRESH
        self.stranger_2.languages = '["foo"]'
        self.stranger_2.looking_for_partner_from = datetime.datetime(1980, 1, 1)
        self.stranger_2.save()
        self.stranger_3.languages = '["BAR", "BAZ", "bim"]'
        self.stranger_3.looking_for_partner_from = datetime.datetime(1991, 1, 1)
        self.stranger_3.save()
        # Stranger speaking on highest priority language (foo), FRESH
        self.stranger_4.languages = '["BAR", "BAZ", "BOO", "foo", "BIM"]'
        self.stranger_4.looking_for_partner_from = datetime.datetime(1993, 1, 1)
        self.stranger_4.save()
        self.stranger_5.languages = '["bar"]'
        self.stranger_5.looking_for_partner_from = datetime.datetime(1992, 1, 1)
        self.stranger_5.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        self.assertEqual(self.stranger_service._match_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_4)

    @patch('randtalkbot.talk.Talk', Mock())
    @asynctest.ignore_loop
    def test_match_partner__returns_fresh_stranger_2(self):
        from randtalkbot.talk import Talk
        Talk.get_last_partners_ids.return_value = [self.stranger_4.id, 33333, 44444]
        self.stranger_0.languages = '["foo", "bar", "baz", "boo", "bim"]'
        self.stranger_0.save()
        self.stranger_1.languages = '["BAR", "baz", "FOO"]'
        self.stranger_1.looking_for_partner_from = datetime.datetime(1990, 1, 1)
        self.stranger_1.save()
        # Stranger speaking on highest priority language, FRESH
        self.stranger_2.languages = '["foo"]'
        self.stranger_2.looking_for_partner_from = datetime.datetime(1980, 1, 1)
        self.stranger_2.save()
        self.stranger_3.languages = '["BAR", "BAZ", "bim"]'
        self.stranger_3.looking_for_partner_from = datetime.datetime(1991, 1, 1)
        self.stranger_3.save()
        # Stranger speaking on highest priority language (foo), NOT FRESH
        self.stranger_4.languages = '["BAR", "BAZ", "BOO", "foo", "BIM"]'
        self.stranger_4.looking_for_partner_from = datetime.datetime(1993, 1, 1)
        self.stranger_4.save()
        self.stranger_5.languages = '["bar"]'
        self.stranger_5.looking_for_partner_from = datetime.datetime(1992, 1, 1)
        self.stranger_5.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        self.assertEqual(self.stranger_service._match_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_2)

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

    async def test_match_partner__ok(self):
        stranger = CoroutineMock()
        partner = CoroutineMock()
        partner.id = 31416
        self.stranger_service._match_partner = Mock(return_value=partner)
        self.stranger_service._locked_strangers_ids = Mock()
        await self.stranger_service.match_partner(stranger)
        self.stranger_service._locked_strangers_ids.discard. \
            assert_called_once_with(31416)
        stranger.notify_partner_found.assert_called_once_with(partner)
        partner.notify_partner_found.assert_called_once_with(stranger)
        stranger.set_partner.assert_called_once_with(partner)

    async def test_match_partner__stranger_error(self):
        stranger = CoroutineMock()
        partner = CoroutineMock()
        partner.id = 31416
        self.stranger_service._match_partner = Mock(return_value=partner)
        self.stranger_service._locked_strangers_ids = Mock()
        stranger.notify_partner_found.side_effect = StrangerError()
        with self.assertRaises(StrangerServiceError):
            await self.stranger_service.match_partner(stranger)
        self.stranger_service._locked_strangers_ids.discard. \
            assert_called_once_with(31416)
        stranger.set_partner.assert_not_called()

    async def test_match_partner__first_partner_has_blocked_the_bot(self):
        stranger = CoroutineMock()
        partner = CoroutineMock()
        partner.id = 31416
        self.stranger_service._match_partner = Mock(return_value=partner)
        self.stranger_service._locked_strangers_ids = Mock()
        partner.notify_partner_found.side_effect = [StrangerError(), None]
        await self.stranger_service.match_partner(stranger)
        self.assertEqual(
            self.stranger_service._locked_strangers_ids.discard.call_args_list,
            [
                call(31416),
                call(31416),
                ],
            )
        self.assertEqual(
            partner.notify_partner_found.call_args_list,
            [
                call(stranger),
                call(stranger),
                ],
            )
        stranger.notify_partner_found.assert_called_once_with(partner)

    async def test_match_partner__partner_obtaining_error(self):
        from randtalkbot.stranger_service import PartnerObtainingError
        stranger = CoroutineMock()
        self.stranger_service._match_partner = Mock(
            side_effect=PartnerObtainingError,
            )
        with self.assertRaises(PartnerObtainingError):
            await self.stranger_service.match_partner(stranger)
