# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from peewee import *
from randtalkbot.stats import Stats
from unittest.mock import create_autospec, patch, Mock

class TestStats(unittest.TestCase):
    def setUp(self):
        self.stats = Stats(data_json='{"foo": "bar"}')

    def test_get_data(self):
        self.assertEqual(self.stats.get_data(), {'foo': 'bar'})

    def test_set_data(self):
        self.stats.set_data({'bar': 'boo'})
        self.assertEqual(self.stats.data_json, '{"bar": "boo"}')

    def test_get_sex_ratio(self):
        stats = Stats(data_json='{"sex_distribution": {"male": 2000, "female": 1000}}')
        self.assertEqual(stats.get_sex_ratio(), 2)
        stats = Stats(data_json='{"sex_distribution": {"female": 1000}}')
        self.assertEqual(stats.get_sex_ratio(), 0.1)
        stats = Stats(data_json='{"sex_distribution": {"male": 2000}}')
        self.assertEqual(stats.get_sex_ratio(), 10)
        stats = Stats(data_json='{"sex_distribution": {}}')
        self.assertEqual(stats.get_sex_ratio(), 1)
        stats = Stats(data_json='[]')
        self.assertEqual(stats.get_sex_ratio(), 1)
