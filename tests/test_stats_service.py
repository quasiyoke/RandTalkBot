# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import asynctest
import datetime
import json
import types
import unittest
from asynctest.mock import patch, Mock, CoroutineMock
from peewee import *
from randtalkbot import stats
from randtalkbot.stats_service import StatsService
from randtalkbot.stats import Stats

STRANGERS = [
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['ru'], 'sex': 'female', 'partner_sex': 'male'},
    {'languages': ['ru'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['en', 'it'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['it'], 'sex': 'female', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['en', 'it'], 'sex': 'male', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'not_specified'},
    {'languages': ['en', 'it'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['ru'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['it'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['ru'], 'sex': 'male', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['ru'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['en', 'it'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'male'},
    {'languages': ['en', 'it'], 'sex': 'male', 'partner_sex': 'not_specified'},
    {'languages': ['en', 'it'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['ru', 'en'], 'sex': 'male', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'male'},
    {'languages': ['ru'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['it'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    {'languages': ['it'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['it'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['en', 'it'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['ru', 'en'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['ru', 'it'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'female', 'partner_sex': 'male'},
    {'languages': ['en', 'it'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['en', 'it'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['it'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'not_specified'},
    {'languages': ['ru'], 'sex': 'female', 'partner_sex': 'male'},
    {'languages': ['en', 'it'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['ru'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['ru'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['de'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    ]

def get_strangers():
    for stranger_json in STRANGERS:
        stranger = Mock()
        stranger.sex = stranger_json['sex']
        stranger.partner_sex = stranger_json['partner_sex']
        stranger.get_languages = Mock(return_value=stranger_json['languages'])
        yield stranger

class TestStatsService(asynctest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestStatsService, self).__init__(*args, **kwargs)
        self.database = SqliteDatabase(':memory:')

    def setUp(self):
        stats.database_proxy.initialize(self.database)
        self.database.create_tables([Stats])
        self.update_stats = StatsService._update_stats
        StatsService._update_stats = Mock()
        self.stats_service = StatsService()
        self.stats = Mock()
        self.stats.created = datetime.datetime(1990, 1, 1)
        self.stats_service._stats = self.stats

    def tearDown(self):
        self.database.drop_tables([Stats])
        StatsService._update_stats = self.update_stats

    @asynctest.ignore_loop
    def test_init__no_stats_in_db(self):
        self.stats_service._update_stats.assert_called_once_with()

    @asynctest.ignore_loop
    def test_init__some_stats_in_db_1(self):
        stats1 = Stats.create(data_json='', created=datetime.datetime(1980, 1, 1))
        stats2 = Stats.create(data_json='', created=datetime.datetime(1990, 1, 1))
        stats_service = StatsService()
        self.assertEqual(stats_service._stats, stats2)

    @asynctest.ignore_loop
    def test_init__some_stats_in_db_2(self):
        stats1 = Stats.create(data_json='', created=datetime.datetime(1990, 1, 1))
        stats2 = Stats.create(data_json='', created=datetime.datetime(1980, 1, 1))
        stats_service = StatsService()
        self.assertEqual(stats_service._stats, stats1)

    @asynctest.ignore_loop
    def test_get_instance__ok(self):
        self.assertEqual(StatsService.get_instance(), self.stats_service)

    @asynctest.ignore_loop
    def test_get_instance__runtime_error(self):
        del StatsService._instance
        with self.assertRaises(RuntimeError):
            StatsService.get_instance()

    @asynctest.ignore_loop
    def test_get_stats(self):
        self.assertEqual(self.stats_service.get_stats(), self.stats)

    @patch('randtalkbot.stats_service.asyncio', CoroutineMock())
    @patch('randtalkbot.stats_service.datetime', Mock())
    async def test_run__ok(self):
        from randtalkbot.stats_service import asyncio
        from randtalkbot.stats_service import datetime as datetime_mock
        self.stats_service._update_stats.reset_mock()
        datetime_mock.datetime.utcnow.side_effect = [datetime.datetime(1990, 1, 1, 3), RuntimeError]
        with self.assertRaises(RuntimeError):
            await self.stats_service.run()
        asyncio.sleep.assert_called_once_with(3600)
        self.stats_service._update_stats.assert_called_once_with()

    @patch('randtalkbot.stats_service.asyncio')
    @patch('randtalkbot.stats_service.datetime', Mock())
    async def test_run__too_late(self, asyncio):
        from randtalkbot.stats_service import datetime as datetime_mock
        self.stats_service._update_stats.reset_mock()
        datetime_mock.datetime.utcnow.side_effect = [
            datetime.datetime(1990, 1, 1, 4, 0, 1),
            RuntimeError,
            ]
        with self.assertRaises(RuntimeError):
            await self.stats_service.run()
        asyncio.sleep.assert_not_called()
        self.stats_service._update_stats.assert_called_once_with()

    @asynctest.ignore_loop
    @patch('randtalkbot.stranger_service.StrangerService', Mock())
    def test_update_stats(self):
        from randtalkbot.stranger_service import StrangerService
        stranger_service = StrangerService.get_instance.return_value
        stranger_service.get_full_strangers = get_strangers
        self.stats_service._update_stats = types.MethodType(self.update_stats, self.stats_service)
        self.stats_service._update_stats()
        self.assertEqual(
            json.loads(self.stats_service._stats.data_json),
            {"languages_count_distribution": [[1, 88], [2, 13]], "partner_sex_distribution": {"male": 38,
                "not_specified": 32, "female": 31}, "languages_popularity": [["en", 67], ["it", 34], ["ru",
                12]], "sex_distribution": {"male": 36, "not_specified": 32, "female": 33}, "total_count":
                101, "languages_to_orientation": [["en", {"not_specified not_specified": 6, "female male":
                5, "female female": 6, "not_specified male": 11, "male not_specified": 6,
                "not_specified female": 7, "male female": 5, "male male": 10, "female not_specified": 11}],
                ["it", {"not_specified not_specified": 5, "female male": 2, "not_specified male": 1,
                "female female": 5, "male not_specified": 3, "not_specified female": 4, "male female": 7,
                "male male": 5, "female not_specified": 2}], ["ru", {"female male": 2,
                "not_specified male": 1, "female female": 2, "male not_specified": 2, "male male": 2,
                "female not_specified": 3}]]}
            )
