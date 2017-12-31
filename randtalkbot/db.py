# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from peewee import DatabaseError, MySQLDatabase
from playhouse.shortcuts import RetryOperationalError
from randtalkbot import stats, stranger, talk
from .errors import DBError
from .stats import Stats
from .stranger import Stranger
from .talk import Talk

LOGGER = logging.getLogger('randtalkbot.db')

class RetryingDB(RetryOperationalError, MySQLDatabase):
    """Automatically reconnecting database class.
    @see http://docs.peewee-orm.com/en/latest/peewee/database.html#automatic-reconnect
    """
    pass

class DB:
    def __init__(self, configuration):
        self._db = RetryingDB(
            configuration.database_name,
            host=configuration.database_host,
            user=configuration.database_user,
            password=configuration.database_password,
            )

        # Connect to database just to check if configuration has errors.
        try:
            self._db.connect()
        except DatabaseError as err:
            raise DBError('DatabaseError during connecting to database') from err

        self._db.close()
        stats.DATABASE_PROXY.initialize(self._db)
        stranger.DATABASE_PROXY.initialize(self._db)
        talk.DATABASE_PROXY.initialize(self._db)

    def install(self):
        try:
            self._db.create_tables([Stats, Stranger, Talk])
        except DatabaseError as err:
            raise DBError('DatabaseError during creating tables') from err
