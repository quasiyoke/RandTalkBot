# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import unittest
from peewee import *
from playhouse.test_utils import test_database
from randtalkbot import talk, stranger
from randtalkbot.errors import WrongStrangerError
from randtalkbot.talk import Talk
from randtalkbot.stranger import Stranger
from unittest.mock import create_autospec, patch, Mock

database = SqliteDatabase(':memory:')
stranger.database_proxy.initialize(database)
talk.database_proxy.initialize(database)

class TestTalk(unittest.TestCase):
    def setUp(self):
        database.create_tables([Stranger, Talk])
        self.stranger_0 = Stranger.create(
            invitation='foo',
            telegram_id=31416,
            )
        self.stranger_1 = Stranger.create(
            invitation='bar',
            telegram_id=27183,
            )
        self.stranger_2 = Stranger.create(
            invitation='baz',
            telegram_id=23571,
            )
        self.stranger_3 = Stranger.create(
            invitation='zig',
            telegram_id=11317,
            )
        self.stranger_4 = Stranger.create(
            invitation='zap',
            telegram_id=19232,
            )
        self.talk_0 = Talk.create(
            partner1=self.stranger_0,
            partner1_sent=1000,
            partner2=self.stranger_1,
            partner2_sent=2000,
            searched_since=datetime.datetime(1980, 1, 1),
            )
        self.talk_1 = Talk.create(
            partner1=self.stranger_2,
            partner2=self.stranger_3,
            searched_since=datetime.datetime(1990, 1, 1),
            )
        self.talk_2 = Talk.create(
            partner1=self.stranger_2,
            partner2=self.stranger_4,
            searched_since=datetime.datetime(2000, 1, 1),
            end=datetime.datetime(2010, 1, 1),
            )

    def tearDown(self):
        database.drop_tables([Talk, Stranger])

    @patch('randtalkbot.talk.StrangerService', Mock())
    def test_get_talk__0(self):
        from randtalkbot.talk import StrangerService
        stranger_service = StrangerService.get_instance.return_value
        stranger_service.get_cached_stranger.side_effect = [self.stranger_2, self.stranger_3, ]
        talk = Talk.get_talk(self.stranger_0)
        self.assertEqual(talk, self.talk_0)
        self.assertEqual(talk.partner1, self.stranger_2)
        self.assertEqual(talk.partner2, self.stranger_3)

    @patch('randtalkbot.talk.StrangerService', Mock())
    def test_get_talk__1(self):
        self.assertEqual(Talk.get_talk(self.stranger_1), self.talk_0)
        self.assertEqual(Talk.get_talk(self.stranger_2), self.talk_1)
        self.assertEqual(Talk.get_talk(self.stranger_3), self.talk_1)
        self.assertEqual(Talk.get_talk(self.stranger_4), None)

    def test_get_partner(self):
        self.assertEqual(self.talk_0.get_partner(self.stranger_0), self.stranger_1)
        self.assertEqual(self.talk_0.get_partner(self.stranger_1), self.stranger_0)
        with self.assertRaises(WrongStrangerError):
            self.talk_0.get_partner(self.stranger_2)

    def test_get_sent(self):
        self.assertEqual(self.talk_0.get_sent(self.stranger_0), 1000)
        self.assertEqual(self.talk_0.get_sent(self.stranger_1), 2000)
        with self.assertRaises(WrongStrangerError):
            self.talk_0.get_sent(self.stranger_2)

    def test_increment_sent(self):
        self.talk_0.save = Mock()
        self.talk_0.increment_sent(self.stranger_0)
        self.assertEqual(self.talk_0.partner1_sent, 1001)
        self.assertEqual(self.talk_0.partner2_sent, 2000)
        self.talk_0.save.assert_called_once_with()
        self.talk_0.increment_sent(self.stranger_1)
        self.assertEqual(self.talk_0.partner1_sent, 1001)
        self.assertEqual(self.talk_0.partner2_sent, 2001)
        with self.assertRaises(WrongStrangerError):
            self.talk_0.increment_sent(self.stranger_2)
