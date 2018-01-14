# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import time
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
        """Raises:
            DBError: If there're some troubles during connection to the DB.

        """
        self._db = RetryingDB(
            configuration.database_name,
            host=configuration.database_host,
            user=configuration.database_user,
            password=configuration.database_password,
            )
        self._assert_configuration_ok()
        stats.DATABASE_PROXY.initialize(self._db)
        stranger.DATABASE_PROXY.initialize(self._db)
        talk.DATABASE_PROXY.initialize(self._db)

    def _assert_configuration_ok(self):
        """Connects to the DB just to check if configuration has errors.

        Raises:
            DBError: If there're some troubles during connection to the DB.

        """
        attempts_count = 10
        attempt_index = 0

        while True:
            try:
                self._db.connect()
            except DatabaseError as err:
                if attempt_index < attempts_count:
                    delay = 2
                    LOGGER.debug(
                        'Attempt #%d to connect to DB was unsuccessful. Will sleep %f sec. %s',
                        attempt_index,
                        delay,
                        err,
                        )
                    time.sleep(delay)
                else:
                    raise DBError('DatabaseError during connecting to database') from err
            else:
                self._db.close()
                break

            attempt_index += 1

    def install(self):
        """Raises:
            DBError: If there're some troubles during creating tables.

        """
        try:
            self._db.create_tables([Stats, Stranger, Talk])
        except DatabaseError as err:
            raise DBError('DatabaseError during creating tables') from err
