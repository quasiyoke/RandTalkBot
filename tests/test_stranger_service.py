# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import asynctest
import datetime
from randtalkbot.stranger_service import StrangerService, StrangerServiceError, \
    StrangerObtainingError, PartnerObtainingError
from asynctest.mock import patch, Mock, CoroutineMock

class TestStrangerService(asynctest.TestCase):
    @patch('randtalkbot.stranger_service.MySQLDatabase', Mock())
    @patch('randtalkbot.stranger_service.Stranger', CoroutineMock)
    def setUp(self):
        self.configuration = Mock()
        self.configuration.database_host = 'foo_host'
        self.configuration.database_name = 'foo_name'
        self.configuration.database_user = 'foo_user'
        self.configuration.database_password = 'foo_password'
        self.stranger_service = StrangerService(self.configuration)
        self.full_stranger_service = StrangerService(self.configuration)
        self.stranger_0 = self.full_stranger_service.get_or_create_stranger(27183, Mock())
        self.stranger_0.is_looking_for_partner = False
        self.stranger_0.looking_for_partner_from = None
        self.stranger_0.set_partner = CoroutineMock()
        self.stranger_1 = self.full_stranger_service.get_or_create_stranger(31416, Mock())
        self.stranger_1.is_looking_for_partner = False
        self.stranger_1.looking_for_partner_from = None
        self.stranger_1.set_partner = CoroutineMock()
        self.stranger_2 = self.full_stranger_service.get_or_create_stranger(23571, Mock())
        self.stranger_2.is_looking_for_partner = False
        self.stranger_2.looking_for_partner_from = None
        self.stranger_2.set_partner = CoroutineMock()

    @patch('randtalkbot.stranger_service.MySQLDatabase', Mock())
    @asynctest.ignore_loop
    def test_init__ok(self):
        from randtalkbot.stranger_service import MySQLDatabase
        database = Mock()
        MySQLDatabase.return_value = database
        stranger_service = StrangerService(self.configuration)
        self.assertEqual(stranger_service._db, database)
        MySQLDatabase.assert_called_once_with(
            'foo_name',
            host='foo_host',
            user='foo_user',
            password='foo_password',
            )

    @patch('randtalkbot.stranger_service.MySQLDatabase', Mock())
    @asynctest.ignore_loop
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

    def test_set_partner__ok(self):
        self.stranger_1.is_looking_for_partner = True
        self.stranger_1.looking_for_partner_from = datetime.datetime(1990, 1, 1)
        self.stranger_2.is_looking_for_partner = True
        self.stranger_2.looking_for_partner_from = datetime.datetime(1980, 1, 1)
        yield from self.full_stranger_service.set_partner(self.stranger_0)
        self.stranger_0.set_partner.assert_called_once_with(self.stranger_2)
        self.stranger_2.set_partner.assert_called_once_with(self.stranger_0)

    def test_set_partner__no_partner(self):
        self.stranger_0.set_looking_for_partner = CoroutineMock()
        with self.assertRaises(PartnerObtainingError):
            yield from self.full_stranger_service.set_partner(self.stranger_0)
        self.stranger_0.set_looking_for_partner.assert_called_once_with()

    @asynctest.ignore_loop
    def test_get_or_create_stranger__stranger_found(self):
        self.assertEqual(
            self.full_stranger_service.get_or_create_stranger(31416, Mock()),
            self.stranger_1,
            )

    @patch('randtalkbot.stranger_service.Stranger', Mock())
    @asynctest.ignore_loop
    def test_get_or_create_stranger__no_stranger(self):
        from randtalkbot.stranger_service import Stranger
        handler = Mock()
        self.stranger_service.get_or_create_stranger(31416, handler)
        Stranger.assert_called_once_with(31416, handler)
