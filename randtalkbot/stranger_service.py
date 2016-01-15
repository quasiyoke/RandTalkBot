# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from .stranger import Stranger
from peewee import *
from playhouse.shortcuts import RetryOperationalError
from randtalkbot import stranger

class PartnerObtainingError(Exception):
    pass

class StrangerServiceError(Exception):
    pass

class RetryingMySQLDatabase(RetryOperationalError, MySQLDatabase):
    '''
    Automatically reconnecting database class.
    @see http://docs.peewee-orm.com/en/latest/peewee/database.html#automatic-reconnect
    '''
    pass

class StrangerService:
    def __init__(self, configuration):
        self._strangers_cache = {}
        self._database = RetryingMySQLDatabase(
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
        '''
        Tries to find a partner for obtained stranger or throws PartnerObtainingError if there's no
        proper partner.

        @throws PartnerObtainingError
        '''
        try:
            possible_partners = Stranger.select().where(
                Stranger.id != stranger.id,
                Stranger.partner == None,
                Stranger.looking_for_partner_from != None,
                )
            # If stranger has obtained us her (his) sex and she (he) wants to filter partners by sex,
            # let's do that.
            if stranger.partner_sex == 'male' or stranger.partner_sex == 'female':
                possible_partners = possible_partners.where(
                    Stranger.sex == stranger.partner_sex,
                    (Stranger.partner_sex == stranger.sex) | (Stranger.partner_sex == 'not_specified'),
                    )
            possible_partners = possible_partners.order_by(Stranger.looking_for_partner_from)
            partner = None
            partner_language_priority = 1000
            for possible_partner in possible_partners:
                for priority, language in enumerate(
                    stranger.get_languages()[:partner_language_priority],
                    ):
                    if possible_partner.speaks_on_language(language):
                        partner = possible_partner
                        partner_language_priority = priority
                        if priority == 0:
                            break
                else:
                    continue
                break
            if partner is None:
                raise PartnerObtainingError()
            return self.get_cached_stranger(partner)
        except DatabaseError as e:
            raise StrangerServiceError('Database problems during `get_partner`: {0}'.format(e))

    def get_or_create_stranger(self, telegram_id):
        try:
            stranger, created = Stranger.get_or_create(telegram_id=telegram_id)
        except DatabaseError as e:
            raise StrangerServiceError(
                'Database problems during `get_or_create_stranger`: {0}'.format(e),
                )
        return self.get_cached_stranger(stranger)
