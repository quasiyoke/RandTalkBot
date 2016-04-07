# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from .errors import PartnerObtainingError, StrangerError, StrangerServiceError
from .stranger import INVITATION_LENGTH, Stranger
from peewee import *

LOGGER = logging.getLogger('randtalkbot.stranger_service')

class StrangerService:
    def __init__(self):
        self._strangers_cache = {}
        type(self)._instance = self

    @classmethod
    def get_instance(cls):
        try:
            return cls._instance
        except AttributeError:
            cls._instance = cls()
            return cls._instance

    def get_cached_stranger(self, stranger):
        try:
            return self._strangers_cache[stranger.id]
        except KeyError:
            self._strangers_cache[stranger.id] = stranger
            return stranger

    def get_cache_size(self):
        return len(self._strangers_cache)

    def get_full_strangers(self):
        for stranger in Stranger.select():
            if stranger.is_full():
                yield stranger

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

    def _match_partner(self, stranger):
        '''
        Tries to find a partner for obtained stranger or throws PartnerObtainingError if there's no
        proper partner.

        @throws PartnerObtainingError
        '''
        from .talk import Talk

        possible_partners = Stranger.select().where(
            Stranger.id != stranger.id,
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

        last_partners_ids = frozenset(Talk.get_last_partners_ids(stranger))

        partner = None
        partner_language_priority = 1000
        for possible_partner in possible_partners:
            if possible_partner.id in last_partners_ids:
                continue
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

    async def match_partner(self, stranger):
        '''
        Finds partner for the stranger. Does handling of strangers who have blocked the bot.

        @raise PartnerObtainingError if there's no proper partners.
        @raise StrangerServiceError if the stranger has blocked the bot.
        '''
        while True:
            partner = self._match_partner(stranger)
            try:
                await partner.notify_partner_found(stranger)
            except StrangerError as e:
                # Potential partner has blocked the bot. Let's look for next potential partner.
                LOGGER.info('Bad potential partner for %d. %s', stranger.id, e)
                await partner.end_talk()
                continue
            break
        try:
            await stranger.notify_partner_found(partner)
        except StrangerError as e:
            # Stranger has blocked the bot.
            raise StrangerServiceError('Can\'t notify seeking for partner stranger: {}'.format(e))
        await stranger.set_partner(partner)
        LOGGER.debug('Found partner: %d -> %d.', stranger.id, partner.id)
