# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import json
import logging
from peewee import *

LOGGER = logging.getLogger('randtalkbot.stats')

def _(s): return s

database_proxy = Proxy()

class Stats(Model):
    data_json = TextField()
    created = DateTimeField(default=datetime.datetime.utcnow, index=True)

    class Meta:
        database = database_proxy

    def get_data(self):
        try:
            return self._data_cache
        except AttributeError:
            self._data_cache = json.loads(self.data_json)
            return self._data_cache

    def set_data(self, data):
        self._data_cache = data
        self.data_json = json.dumps(data)

    def get_sex_ratio(self):
        '''
        @return Ratio of males to females.
        @see https://en.wikipedia.org/wiki/Human_sex_ratio
        '''
        try:
            sex_data = self.get_data()['sex_distribution']
        except (KeyError, TypeError):
            return 1
        males_count = sex_data.get('male', 0)
        females_count = sex_data.get('female', 0)
        if males_count > 0 and females_count > 0:
            return males_count / females_count
        elif males_count > 0:
            return 10
        elif females_count > 0:
            return 0.1
        else:
            return 1
