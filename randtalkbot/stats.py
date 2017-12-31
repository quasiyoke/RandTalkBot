# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import json
import logging
from peewee import DateTimeField, Model, Proxy, TextField

LOGGER = logging.getLogger('randtalkbot.stats')

def _(string):
    return string

DATABASE_PROXY = Proxy()
RATIO_MAX = 10

class Stats(Model):
    data_json = TextField()
    created = DateTimeField(default=datetime.datetime.utcnow, index=True)

    class Meta:
        database = DATABASE_PROXY

    def __init__(self, *args, **kwargs):
        super(Stats, self).__init__(*args, **kwargs)
        self._data_cache = None

    def get_data(self):
        if self._data_cache is None:
            self._data_cache = json.loads(self.data_json)

        return self._data_cache

    def set_data(self, data):
        self._data_cache = data
        self.data_json = json.dumps(data)

    def get_sex_ratio(self):
        """https://en.wikipedia.org/wiki/Human_sex_ratio

        Returns:
            float: Ratio of males over the females.

        """
        try:
            sex_data = self.get_data()['sex_distribution']
        except (KeyError, TypeError):
            return 1

        males_count = sex_data.get('male', 0)
        females_count = sex_data.get('female', 0)

        if males_count > 0 and females_count > 0:
            return males_count / females_count
        elif males_count > 0:
            return RATIO_MAX
        elif females_count > 0:
            return 1 / RATIO_MAX

        return 1
