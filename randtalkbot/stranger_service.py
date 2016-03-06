# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from .errors import PartnerObtainingError, StrangerServiceError
from .stranger import INVITATION_LENGTH, Stranger
from peewee import *

LOGGER = logging.getLogger('randtalkbot.stranger_service')

class StrangerService:
    def __init__(self):
        self._strangers_cache = {}

    def get_cached_stranger(self, stranger):
        try:
            return self._strangers_cache[stranger.id]
        except KeyError:
            self._strangers_cache[stranger.id] = stranger
            if stranger.partner is not None:
                stranger.partner = self.get_cached_stranger(stranger.partner)
            return stranger

    def get_full_strangers(self):
        for stranger in Stranger.select():
            if stranger.is_full():
                yield stranger

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
            if stranger.sex == 'not_specified':
                possible_partners = possible_partners.where(Stranger.partner_sex == 'not_specified')
            else:
                possible_partners = possible_partners.where(
                    (Stranger.partner_sex == stranger.sex) | (Stranger.partner_sex == 'not_specified'),
                    )
            # If stranger wants to filter partners by sex, let's do that.
            if stranger.partner_sex == 'male' or stranger.partner_sex == 'female':
                possible_partners = possible_partners.where(
                    Stranger.sex == stranger.partner_sex,
                    )
            possible_partners = possible_partners.order_by(
                Stranger.bonus_count.desc(),
                Stranger.looking_for_partner_from,
                )
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
            try:
                stranger = Stranger.get(Stranger.telegram_id == telegram_id)
            except DoesNotExist:
                stranger = Stranger.create(
                    invitation=Stranger.get_invitation(),
                    telegram_id=telegram_id,
                    )
        except DatabaseError as e:
            raise StrangerServiceError(
                'Database problems during `get_or_create_stranger`: {0}'.format(e),
                )
        return self.get_cached_stranger(stranger)

    def get_stranger(self, telegram_id):
        try:
            stranger = Stranger.get(Stranger.telegram_id == telegram_id)
        except (DatabaseError, DoesNotExist) as e:
            raise StrangerServiceError(
                'Database problems during `get_stranger`: {0}'.format(e),
                )
        return self.get_cached_stranger(stranger)

    def get_stranger_by_invitation(self, invitation):
        if len(invitation) != INVITATION_LENGTH:
            raise StrangerServiceError(
                'Invitation length is wrong: \"{0}\"'.format(invitation),
                )
        try:
            stranger = Stranger.get(Stranger.invitation == invitation)
        except (DatabaseError, DoesNotExist) as e:
            raise StrangerServiceError(
                'Database problems during `get_stranger_by_invitation`: {0}'.format(e),
                )
        return self.get_cached_stranger(stranger)
