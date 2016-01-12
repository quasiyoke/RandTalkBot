# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import datetime
import unittest
from asynctest.mock import CoroutineMock
from peewee import DatabaseError, DoesNotExist, MySQLDatabase
from randtalkbot.stranger import Stranger
from randtalkbot.stranger_service import StrangerService, StrangerServiceError, PartnerObtainingError
from unittest.mock import call, create_autospec, patch, Mock

class TestStrangerService(unittest.TestCase):
    @patch('randtalkbot.stranger_service.MySQLDatabase', create_autospec(MySQLDatabase))
    @patch('randtalkbot.stranger_service.Stranger', create_autospec(Stranger))
    def setUp(self):
        from randtalkbot.stranger_service import MySQLDatabase
        from randtalkbot.stranger_service import Stranger as stranger_cls_mock
        stranger_mock = Mock()
        stranger_mock.id = 1
        stranger_cls_mock.get_or_create.return_value = (stranger_mock, False)
        self.configuration = Mock()
        self.configuration.database_host = 'foo_host'
        self.configuration.database_name = 'foo_name'
        self.configuration.database_user = 'foo_user'
        self.configuration.database_password = 'foo_password'
        self.database = Mock()
        MySQLDatabase.return_value = self.database
        self.stranger_service = StrangerService(self.configuration)
        self.stranger_0 = Mock()
        self.stranger_0.telegram_id = 27183
        self.stranger_0.partner = None
        self.stranger_0.looking_for_partner_from = None
        self.stranger_0.set_partner = CoroutineMock()
        self.stranger_1 = Mock()
        self.stranger_1.telegram_id = 31416
        self.stranger_1.partner = None
        self.stranger_1.looking_for_partner_from = None
        self.stranger_1.set_partner = CoroutineMock()
        self.stranger_2 = Mock()
        self.stranger_2.telegram_id = 23571
        self.stranger_2.partner = None
        self.stranger_2.looking_for_partner_from = None
        self.stranger_2.set_partner = CoroutineMock()

    @patch('randtalkbot.stranger_service.MySQLDatabase', Mock())
    @patch('randtalkbot.stranger.database_proxy', Mock())
    def test_init__ok(self):
        from randtalkbot.stranger_service import MySQLDatabase
        from randtalkbot.stranger import database_proxy
        database = Mock()
        MySQLDatabase.return_value = database
        stranger_service = StrangerService(self.configuration)
        self.assertEqual(stranger_service._database, database)
        MySQLDatabase.assert_called_once_with(
            'foo_name',
            host='foo_host',
            user='foo_user',
            password='foo_password',
            )
        database_proxy.initialize.assert_called_once_with(database)

    @patch('randtalkbot.stranger_service.MySQLDatabase', Mock())
    def test_init__database_troubles(self):
        from randtalkbot.stranger_service import MySQLDatabase
        MySQLDatabase.return_value.connect.side_effect = StrangerServiceError()
        with self.assertRaises(StrangerServiceError):
            StrangerService(self.configuration)
        MySQLDatabase.assert_called_once_with(
            'foo_name',
            host='foo_host',
            user='foo_user',
            password='foo_password',
            )

    def test_install__ok(self):
        self.stranger_service.install()
        self.stranger_service._database.create_tables.assert_called_once_with([Stranger])

    def test_install__database_error(self):
        self.database.create_tables.side_effect = DatabaseError()
        with self.assertRaises(StrangerServiceError):
            self.stranger_service.install()
        self.database.create_tables.assert_called_once_with([Stranger])

    def test_get_cached_stranger__cached(self):
        stranger = Mock()
        stranger.id = 31416
        self.stranger_service._strangers_cache[31416] = stranger
        self.assertEqual(self.stranger_service.get_cached_stranger(stranger), stranger)

    def test_get_cached_stranger__not_cached_no_partner(self):
        stranger = Mock()
        stranger.id = 31416
        stranger.partner = None
        self.assertEqual(self.stranger_service.get_cached_stranger(stranger), stranger)
        self.assertEqual(self.stranger_service._strangers_cache[31416], stranger)

    @patch('randtalkbot.stranger_service.Stranger', create_autospec(Stranger))
    def test_get_partner__ok(self):
        from randtalkbot.stranger_service import Stranger
        Stranger.select.return_value.where.return_value.order_by.return_value.get \
            .return_value = self.stranger_0
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        self.assertEqual(self.stranger_service.get_partner(self.stranger_0), 'cached_partner')
        self.stranger_service.get_cached_stranger.assert_called_once_with(self.stranger_0)

    @patch('randtalkbot.stranger_service.Stranger', create_autospec(Stranger))
    def test_get_partner__database_error(self):
        from randtalkbot.stranger_service import Stranger
        Stranger.select.return_value.where.return_value.order_by.return_value.get \
            .side_effect = DatabaseError()
        self.stranger_service.get_cached_stranger = Mock(return_value='cached_partner')
        with self.assertRaises(StrangerServiceError):
            self.stranger_service.get_partner(self.stranger_0)
        self.stranger_service.get_cached_stranger.assert_not_called()

    @patch('randtalkbot.stranger_service.Stranger', create_autospec(Stranger))
    def test_get_partner__does_not_exist(self):
        from randtalkbot.stranger_service import Stranger
        Stranger.select.return_value.where.return_value.order_by.return_value.get \
            .side_effect = DoesNotExist()
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
