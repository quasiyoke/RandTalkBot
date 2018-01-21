# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from peewee import DatabaseError, DoesNotExist
from .errors import PartnerObtainingError, StrangerError, StrangerServiceError
from .stranger import INVITATION_LENGTH, Stranger

LOGGER = logging.getLogger('randtalkbot.stranger_service')


class StrangerService:
    def __init__(self):
        # We need to lock strangers for matching to prevent attempts to create
        # second conversation with single partner.
        self._locked_strangers_ids = set()
        type(self)._instance = self

    @classmethod
    def get_instance(cls):
        try:
            return cls._instance
        except AttributeError:
            cls._instance = cls()
            return cls._instance

    @classmethod
    def get_full_strangers(cls):
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
        except DatabaseError as err:
            raise StrangerServiceError('Database problems during `get_or_create_stranger`') from err

        return stranger

    def get_stranger(self, telegram_id):
        try:
            stranger = Stranger.get(Stranger.telegram_id == telegram_id)
        except (DatabaseError, DoesNotExist) as err:
            raise StrangerServiceError('Database problems during `get_stranger`') from err

        return stranger

    def get_stranger_by_id(self, stranger_id):
        return Stranger.get(Stranger.id == stranger_id)

    def get_stranger_by_invitation(self, invitation):
        if not isinstance(invitation, str) or len(invitation) != INVITATION_LENGTH:
            raise StrangerServiceError(f'Invitation length is wrong: `{invitation}`')

        try:
            stranger = Stranger.get(Stranger.invitation == invitation)
        except (DatabaseError, DoesNotExist) as err:
            raise StrangerServiceError('Database problems during `get_stranger_by_invitation`') \
                from err

        return stranger

    def _match_partner(self, stranger_id):
        """Tries to find a partner for obtained stranger.

        Args:
            stranger_id (int)

        Raises:
            PartnerObtainingError: If there's no proper partner.

        Returns:
            Stranger

        """
        from .talk import Talk

        possible_partners = Stranger.select() \
            .where(
                Stranger.id != stranger_id,
                Stranger.looking_for_partner_from != None,
                )

        stranger = self.get_stranger_by_id(stranger_id)

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

        last_partners_ids = frozenset(Talk.get_last_partners_ids(stranger_id))

        partner = None
        partner_language_priority = 1000

        for possible_partner in possible_partners:
            if possible_partner.id in last_partners_ids:
                LOGGER.debug(
                    'Stranger %d was a partner for %d recently',
                    possible_partner.id,
                    stranger_id,
                    )
                continue

            if possible_partner.id in self._locked_strangers_ids:
                LOGGER.debug(
                    'Stranger %d is locked (so she can\'t be a partner for %d)',
                    possible_partner.id,
                    stranger_id,
                    )
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

        self._locked_strangers_ids.add(partner.id)
        return partner

    async def match_partner(self, stranger_id):
        """Finds partner for the stranger. Does handling of strangers who have blocked the bot.

        Raises:
            PartnerObtainingError: If there's no proper partners.
            StrangerServiceError: If the stranger has blocked the bot.
        """
        stranger = self.get_stranger_by_id(stranger_id)

        while True:
            partner = self._match_partner(stranger_id)

            try:
                await partner.notify_partner_found(stranger_id)
            except StrangerError as err:
                # Potential partner has blocked the bot. Let's look for next
                # potential partner.
                LOGGER.info('Bad potential partner for %d. %s', stranger_id, err)
                await partner.end_talk()
                self._locked_strangers_ids.discard(partner.id)
                continue

            break

        try:
            await stranger.notify_partner_found(partner.id)
        except StrangerError as err:
            self._locked_strangers_ids.discard(partner.id)
            # Stranger has blocked the bot.
            raise StrangerServiceError('Can\'t notify seeking for partner stranger') from err

        await stranger.set_partner(partner.id)
        self._locked_strangers_ids.discard(partner.id)
        LOGGER.debug('Found partner: %d -> %d.', stranger_id, partner.id)
