# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
from .stranger import Stranger
from peewee import *

class StrangerServiceError(Exception):
    pass

class StrangerObtainingError(Exception):
    pass

class PartnerObtainingError(Exception):
    pass

class StrangerService:
    def __init__(self, configuration):
        self._strangers = {}
        self._db = MySQLDatabase(
            configuration.database_name,
            host=configuration.database_host,
            user=configuration.database_user,
            password=configuration.database_password,
            )
        # Connect to database just to check if configuration has errors.
        try:
            self._db.connect()
        except DatabaseError as e:
            logging.error('Troubles with connecting to database.')
            raise StrangerServiceError()
        self._db.close()

    @asyncio.coroutine
    def set_partner(self, stranger):
        partner = None
        for telegram_id, potential_partner in self._strangers.items():
            if potential_partner.is_looking_for_partner and (not partner or \
                potential_partner.looking_for_partner_from < partner.looking_for_partner_from):
                partner = potential_partner
        if not partner:
            yield from stranger.set_looking_for_partner()
            raise PartnerObtainingError()
        yield from stranger.set_partner(partner)
        yield from partner.set_partner(stranger)

    def get_or_create_stranger(self, telegram_id, stranger_handler):
        try:
            return self._strangers[telegram_id]
        except KeyError:
            stranger = Stranger(telegram_id, stranger_handler)
            self._strangers[telegram_id] = stranger
            return stranger
