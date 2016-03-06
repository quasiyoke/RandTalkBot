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
        return json.loads(self.data_json)

    def set_data(self, data):
        self.data_json = json.dumps(data)
