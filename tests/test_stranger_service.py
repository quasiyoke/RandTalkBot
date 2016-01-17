# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import datetime
import unittest
from asynctest.mock import CoroutineMock
from peewee import *
from playhouse.test_utils import test_database
from randtalkbot import stranger
from randtalkbot.stranger import Stranger
from randtalkbot.stranger_service import \
    StrangerService, StrangerServiceError, PartnerObtainingError, RetryingMySQLDatabase
from unittest.mock import create_autospec, patch, Mock

class TestStrangerServiceMocked(unittest.TestCase):
    @patch('randtalkbot.stranger_service.RetryingMySQLDatabase', create_autospec(RetryingMySQLDatabase))
    @patch('randtalkbot.stranger_service.stranger')
    def setUp(self, stranger_module_mock):
        from randtalkbot.stranger_service import RetryingMySQLDatabase
        self.stranger_module_mock = stranger_module_mock
        self.database = Mock()
        self.RetryingMySQLDatabase = RetryingMySQLDatabase
        self.RetryingMySQLDatabase.return_value = self.database
        self.configuration = Mock()
        self.configuration.database_host = 'foo_host'
        self.configuration.database_name = 'foo_name'
        self.configuration.database_user = 'foo_user'
        self.configuration.database_password = 'foo_password'
        self.RetryingMySQLDatabase.reset_mock()
        self.stranger_service = StrangerService(self.configuration)

    def test_init__ok(self):
        self.RetryingMySQLDatabase.assert_called_once_with(
            'foo_name',
            host='foo_host',
            user='foo_user',
            password='foo_password',
            )
        self.stranger_module_mock.database_proxy.initialize.assert_called_once_with(self.database)

    def test_init__database_troubles(self):
        self.RetryingMySQLDatabase.return_value.connect.side_effect = DatabaseError()
        with self.assertRaises(StrangerServiceError):
            StrangerService(self.configuration)
        self.RetryingMySQLDatabase.assert_called_once_with(
            'foo_name',
            host='foo_host',
            user='foo_user',
            password='foo_password',
            )
        self.stranger_module_mock.database_proxy.initialize.assert_not_called()

    def test_install__ok(self):
        self.stranger_service.install()
        self.database.create_tables.assert_called_once_with([Stranger])

    def test_install__database_error(self):
        self.database.create_tables.side_effect = DatabaseError()
        with self.assertRaises(StrangerServiceError):
            self.stranger_service.install()
        self.database.create_tables.assert_called_once_with([Stranger])

class TestStrangerServiceIntegrational(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestStrangerServiceIntegrational, self).__init__(*args, **kwargs)
        self.database = SqliteDatabase(':memory:')

    @patch('randtalkbot.stranger_service.RetryingMySQLDatabase', create_autospec(RetryingMySQLDatabase))
    @patch('randtalkbot.stranger_service.stranger')
    def setUp(self, stranger_module_mock):
        from randtalkbot.stranger_service import RetryingMySQLDatabase
        configuration = Mock()
        configuration.database_host = 'foo_host'
        configuration.database_name = 'foo_name'
        configuration.database_user = 'foo_user'
        configuration.database_password = 'foo_password'
        self.stranger_service = StrangerService(configuration)
        stranger.database_proxy.initialize(self.database)
        self.database.create_tables([Stranger])
        self.stranger_0 = Stranger.create(
            languages='["foo"]',
            telegram_id=27183,
            sex='female',
            partner_sex='male',
            )
        self.stranger_1 = Stranger.create(
            languages='["foo"]',
            telegram_id=31416,
            sex='male',
            partner_sex='female',
            )
        self.stranger_2 = Stranger.create(
            languages='["foo"]',
            telegram_id=23571,
            sex='male',
            partner_sex='female',
            )
        self.stranger_3 = Stranger.create(
            languages='["foo"]',
            telegram_id=11317,
            sex='male',
            partner_sex='female',
            )
        self.stranger_4 = Stranger.create(
            languages='["foo"]',
            telegram_id=19232,
            sex='male',
            partner_sex='female',
            )
        self.stranger_5 = Stranger.create(
            languages='["foo"]',
            telegram_id=93137,
            sex='male',
            partner_sex='female',
            )

    def tearDown(self):
        self.database.drop_tables([Stranger])

    def test_get_cached_stranger__cached(self):
        cached_stranger = Mock()
        cached_stranger.id = 31416
        self.stranger_service._strangers_cache[31416] = cached_stranger
        stranger = Mock()
        stranger.id = 31416
        self.assertEqual(self.stranger_service.get_cached_stranger(stranger), cached_stranger)

    def test_get_cached_stranger__not_cached_no_partner(self):
        stranger = Mock()
        stranger.id = 31416
        stranger.partner = None
        self.assertEqual(self.stranger_service.get_cached_stranger(stranger), stranger)
        self.assertEqual(self.stranger_service._strangers_cache[31416], stranger)

    def test_get_cached_stranger__not_cached_with_partner(self):
        stranger = Mock()
        stranger.id = 31416
        partner = Mock()
        partner.id = 27183
        partner.partner = None
        stranger.partner = partner
        self.stranger_service.get_cached_stranger = Mock(wraps=self.stranger_service.get_cached_stranger)
        self.assertEqual(self.stranger_service.get_cached_stranger(stranger), stranger)
        self.assertEqual(self.stranger_service._strangers_cache[31416], stranger)
        self.assertEqual(self.stranger_service.get_cached_stranger.call_count, 2)
        self.stranger_service.get_cached_stranger.assert_called_with(partner)

    def test_get_partner__returns_the_longest_waiting_stranger_1(self):
        self.stranger_0.languages = '["foo", "bar", "baz"]'
        self.stranger_0.save()
        self.stranger_1.looking_for_partner_from = datetime.datetime(1990, 1, 1)
        self.stranger_1.save()
        # The longest waiting stranger.
        self.stranger_2.looking_for_partner_from = datetime.datetime(1980, 1, 1)
        self.stranger_2.save()
        self.stranger_3.looking_for_partner_from = datetime.datetime(1991, 1, 1)
        self.stranger_3.save()
        self.stranger_4.looking_for_partner_from = datetime.datetime(1993, 1, 1)
        self.stranger_4.save()
        self.stranger_5.looking_for_partner_from = datetime.datetime(1992, 1, 1)
        self.stranger_5.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        self.assertEqual(self.stranger_service.get_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_2)

    def test_get_partner__returns_the_longest_waiting_stranger_2(self):
        self.stranger_0.languages = '["foo", "bar", "baz"]'
        self.stranger_0.save()
        # The longest waiting stranger.
        self.stranger_1.looking_for_partner_from = datetime.datetime(1990, 1, 1)
        self.stranger_1.save()
        self.stranger_2.looking_for_partner_from = datetime.datetime(1994, 1, 1)
        self.stranger_2.save()
        self.stranger_3.looking_for_partner_from = datetime.datetime(1991, 1, 1)
        self.stranger_3.save()
        self.stranger_4.looking_for_partner_from = datetime.datetime(1993, 1, 1)
        self.stranger_4.save()
        self.stranger_5.looking_for_partner_from = datetime.datetime(1992, 1, 1)
        self.stranger_5.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        self.assertEqual(self.stranger_service.get_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_1)

    def test_get_partner__returns_stranger_with_proper_sex_1(self):
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
        self.assertEqual(self.stranger_service.get_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_3)

    def test_get_partner__returns_stranger_with_proper_sex_2(self):
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
        self.assertEqual(self.stranger_service.get_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_4)

    def test_get_partner__returns_stranger_looking_for_proper_sex_1(self):
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
        self.assertEqual(self.stranger_service.get_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_3)

    def test_get_partner__returns_stranger_looking_for_proper_sex_2(self):
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
        self.assertEqual(self.stranger_service.get_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_4)

    def test_get_partner__filters_strangers_when_stranger_partner_sex_isnt_specified_1(self):
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
        self.assertEqual(self.stranger_service.get_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_3)

    def test_get_partner__filters_strangers_when_stranger_partner_sex_isnt_specified_2(self):
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
        self.assertEqual(self.stranger_service.get_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_1)

    def test_get_partner__returns_stranger_looking_for_any_sex_in_case_of_rare_sex_1(self):
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
        self.assertEqual(self.stranger_service.get_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_3)

    def test_get_partner__returns_stranger_looking_for_any_sex_in_case_of_rare_sex_2(self):
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
        self.assertEqual(self.stranger_service.get_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_4)

    def test_get_partner__returns_stranger_looking_for_any_sex_if_sex_is_not_specified_1(self):
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
        self.assertEqual(self.stranger_service.get_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_3)

    def test_get_partner__returns_stranger_looking_for_any_sex_if_sex_is_not_specified_2(self):
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
        self.assertEqual(self.stranger_service.get_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_4)

    def test_get_partner__returns_stranger_speaking_on_highest_priority_language_1(self):
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
        self.assertEqual(self.stranger_service.get_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_3)

    def test_get_partner__returns_stranger_speaking_on_highest_priority_language_2(self):
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
        self.assertEqual(self.stranger_service.get_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_4)

    @patch('randtalkbot.stranger_service.Stranger', create_autospec(Stranger))
    def test_get_partner__database_error(self):
        from randtalkbot.stranger_service import Stranger
        Stranger.select.side_effect = DatabaseError()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        with self.assertRaises(StrangerServiceError):
            self.stranger_service.get_partner(self.stranger_0)
        self.stranger_service.get_cached_stranger.assert_not_called()

    def test_get_partner__does_not_exist(self):
        self.stranger_0.languages = '["boo"]'
        self.stranger_0.save()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        with self.assertRaises(PartnerObtainingError):
            self.stranger_service.get_partner(self.stranger_0)
        self.stranger_service.get_cached_stranger.assert_not_called()

    @patch('randtalkbot.stranger_service.Stranger', create_autospec(Stranger))
    def test_get_or_create_stranger__stranger_found(self):
        from randtalkbot.stranger_service import Stranger
        Stranger.get_or_create.return_value = (self.stranger_0, False)
        self.stranger_service.get_cached_stranger = Mock()
        self.stranger_service.get_cached_stranger.return_value = 'cached_stranger'
        self.assertEqual(
            self.stranger_service.get_or_create_stranger(31416),
            'cached_stranger',
            )
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_0)

    @patch('randtalkbot.stranger_service.Stranger', create_autospec(Stranger))
    def test_get_or_create_stranger__database_error(self):
        from randtalkbot.stranger_service import Stranger
        self.stranger_service.get_cached_stranger = Mock()
        Stranger.get_or_create.side_effect = DatabaseError()
        with self.assertRaises(StrangerServiceError):
            self.stranger_service.get_or_create_stranger(31416)
        Stranger.get_or_create.assert_called_once_with(telegram_id=31416)
        self.stranger_service.get_cached_stranger.assert_not_called()
