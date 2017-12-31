# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from peewee import *
from randtalkbot.db import DB, RetryingDB
from randtalkbot.errors import DBError
from randtalkbot.stats import Stats
from randtalkbot.stranger import Stranger
from randtalkbot.talk import Talk
from unittest.mock import create_autospec, patch, Mock

class TestDB(unittest.TestCase):
    @patch('randtalkbot.db.RetryingDB', create_autospec(RetryingDB))
    @patch('randtalkbot.db.stats')
    @patch('randtalkbot.db.stranger')
    @patch('randtalkbot.db.talk')
    def setUp(self, stats_module_mock, stranger_module_mock, talk_module_mock):
        from randtalkbot.db import RetryingDB
        self.stats_module_mock = stats_module_mock
        self.stranger_module_mock = stranger_module_mock
        self.talk_module_mock = talk_module_mock
        self.database = Mock()
        self.RetryingDB = RetryingDB
        self.RetryingDB.return_value = self.database
        self.configuration = Mock()
        self.configuration.database_host = 'foo_host'
        self.configuration.database_name = 'foo_name'
        self.configuration.database_user = 'foo_user'
        self.configuration.database_password = 'foo_password'
        self.RetryingDB.reset_mock()
        self.db = DB(self.configuration)

    def test_init__ok(self):
        self.RetryingDB.assert_called_once_with(
            'foo_name',
            host='foo_host',
            user='foo_user',
            password='foo_password',
            )
        self.stats_module_mock.DATABASE_PROXY.initialize.assert_called_once_with(self.database)
        self.stranger_module_mock.DATABASE_PROXY.initialize.assert_called_once_with(self.database)
        self.talk_module_mock.DATABASE_PROXY.initialize.assert_called_once_with(self.database)

    def test_init__database_troubles(self):
        self.RetryingDB.return_value.connect.side_effect = DatabaseError()
        with self.assertRaises(DBError):
            DB(self.configuration)

    def test_install__ok(self):
        self.db.install()
        self.database.create_tables.assert_called_once_with([Stats, Stranger, Talk])

    def test_install__database_error(self):
        self.database.create_tables.side_effect = DatabaseError()
        with self.assertRaises(DBError):
            self.db.install()
