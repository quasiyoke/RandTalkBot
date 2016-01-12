# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from .stranger import Stranger
from peewee import *
from randtalkbot import stranger

class PartnerObtainingError(Exception):
    pass

class StrangerServiceError(Exception):
    pass

class StrangerService:
    def __init__(self, configuration):
        self._strangers_cache = {}
        self._database = MySQLDatabase(
            configuration.database_name,
            host=configuration.database_host,
            user=configuration.database_user,
            password=configuration.database_password,
            )
        # Connect to database just to check if configuration has errors.
        try:
            self._database.connect()
        except DatabaseError as e:
            raise StrangerServiceError('DatabaseError during connecting to database: {0}'.format(e))
        self._database.close()
        stranger.database_proxy.initialize(self._database)

    def install(self):
        try:
            self._database.create_tables([Stranger])
        except DatabaseError as e:
            raise StrangerServiceError('DatabaseError during creating tables: {0}'.format(e))

    def get_cached_stranger(self, stranger):
        try:
            return self._strangers_cache[stranger.id]
        except KeyError:
            self._strangers_cache[stranger.id] = stranger
            if stranger.partner is not None:
                stranger.partner = self.get_cached_stranger(stranger.partner)
            return stranger

    def get_partner(self, stranger):
        try:
            try:
                partner = Stranger.select().where(
                    Stranger.id != stranger.id,
                    Stranger.partner == None,
                    Stranger.looking_for_partner_from != None,
                    ).order_by(Stranger.looking_for_partner_from).get()
                return self.get_cached_stranger(partner)
            except DoesNotExist as e:
                raise PartnerObtainingError()
        except DatabaseError as e:
            raise StrangerServiceError('Database problems during `set_partner`: {0}'.format(e))

    def get_or_create_stranger(self, telegram_id):
        try:
            stranger, created = Stranger.get_or_create(telegram_id=telegram_id)
        except DatabaseError as e:
            raise StrangerServiceError('Database problems during `get_or_create_stranger`: {0}'.format(e))
        return self.get_cached_stranger(stranger)
