# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import base64
import datetime
import json
import logging
import random
import string
from peewee import CharField, DateTimeField, ForeignKeyField, IntegerField, Model, Proxy
from telepot.exception import TelegramError
from .errors import EmptyLanguagesError, MissingPartnerError, SexError, StrangerError, \
    StrangerSenderError
from .i18n import get_languages_names, get_translations
from .stats_service import StatsService
from .stranger_sender_service import StrangerSenderService

INVITATION_CHARS = string.ascii_letters + string.digits + string.punctuation
INVITATION_LENGTH = 10
LANGUAGES_MAX_LENGTH = 40
LOGGER = logging.getLogger('randtalkbot.stranger')

def _(string_instance):
    return string_instance


def get_sex_names_to_codes():
    sex_names_to_codes = {}

    for translation in get_translations():
        for sex, name in SEX_CHOICES:
            sex_names_to_codes[translation(name).lower()] = sex

        for name, sex in ADDITIONAL_SEX_NAMES_TO_CODES.items():
            sex_names_to_codes[translation(name).lower()] = sex

    return sex_names_to_codes


SEX_CHOICES = (
    ('female', _('Female')),
    ('male', _('Male')),
    ('not_specified', _('Not specified')),
    )
ADDITIONAL_SEX_NAMES_TO_CODES = {
    'm': 'male',
    _('boy'): 'male',
    _('man'): 'male',
    'men': 'male',
    'f': 'female',
    _('girl'): 'female',
    _('woman'): 'female',
    'women': 'female',
}
SEX_MAX_LENGTH = 20
SEX_NAMES_TO_CODES = get_sex_names_to_codes()
SEX_NAMES = list(zip(*SEX_CHOICES))[1]
WIZARD_CHOICES = (
    ('none', 'None'),
    ('setup', 'Setup'),
    )
DATABASE_PROXY = Proxy()


class Stranger(Model):
    bonus_count = IntegerField(default=0)
    invitation = CharField(max_length=INVITATION_LENGTH, unique=True)
    invited_by = ForeignKeyField('self', null=True, related_name='invited')
    languages = CharField(max_length=LANGUAGES_MAX_LENGTH, null=True)
    looking_for_partner_from = DateTimeField(null=True)
    partner_sex = CharField(choices=SEX_CHOICES, max_length=SEX_MAX_LENGTH, null=True)
    sex = CharField(choices=SEX_CHOICES, max_length=SEX_MAX_LENGTH, null=True)
    telegram_id = IntegerField(unique=True)
    was_invited_as = CharField(choices=SEX_CHOICES, max_length=SEX_MAX_LENGTH, null=True)
    wizard = CharField(choices=WIZARD_CHOICES, default='none', max_length=20)
    wizard_step = CharField(max_length=20, null=True)

    ADVERTISING_DELAY = 30
    HOUR_TIMEDELTA = datetime.timedelta(hours=1)
    LONG_WAITING_TIMEDELTA = datetime.timedelta(minutes=5)
    REWARD_BIG = 3
    REWARD_SMALL = 1
    UNMUTE_BONUSES_NOTIFICATIONS_DELAY = 60 * 60

    class Meta:
        database = DATABASE_PROXY
        indexes = (
            (('partner_sex', 'bonus_count', 'looking_for_partner_from'), False),
            (('sex', 'partner_sex', 'bonus_count', 'looking_for_partner_from'), False),
            )

    @classmethod
    def get_invitation(cls):
        return ''.join([random.choice(INVITATION_CHARS) for i in range(INVITATION_LENGTH)])

    @classmethod
    def _get_sex_code(cls, sex_name):
        sex = sex_name.strip().lower()
        try:
            return SEX_NAMES_TO_CODES[sex]
        except KeyError:
            raise SexError(sex_name)

    async def _add_bonuses(self, bonuses_delta):
        self.bonus_count += bonuses_delta
        self.save()
        bonuses_notifications_muted = getattr(self, '_bonuses_notifications_muted', False)

        if not bonuses_notifications_muted:
            await self._notify_about_bonuses(bonuses_delta)

    async def _advertise(self):
        await asyncio.sleep(type(self).ADVERTISING_DELAY)
        # pylint: disable=attribute-defined-outside-init
        self._deferred_advertising = None
        searching_for_partner_count = Stranger.select() \
            .where(Stranger.looking_for_partner_from != None) \
            .count()

        if searching_for_partner_count <= 1:
            # Let's not advertise if there's nobody to talk with.
            return

        if StatsService.get_instance().get_stats().get_sex_ratio() >= 1:
            message = _(
                'The search is going on. {0} users are looking for partner -- change'
                ' your preferences (languages, partner\'s sex) using /setup command to talk'
                ' with them.\n'
                'Chat *lacks females!* Send the link to your friends and earn {1} bonuses'
                ' for every invited female and {2} bonus for each male (the more bonuses'
                ' you have -- the faster partner\'s search will be):',
                )
        else:
            message = _(
                'The search is going on. {0} users are looking for partner -- change your'
                ' preferences (languages, partner\'s sex) using /setup command to talk'
                ' with them.\n'
                'Chat *lacks males!* Send the link to your friends and earn {1} bonuses'
                ' for every invited male and {2} bonus for each female (the more bonuses'
                ' you have -- the faster partner\'s search will be):',
                )

        sender = self.get_sender()

        try:
            await sender.send_notification(
                message,
                searching_for_partner_count,
                type(self).REWARD_BIG,
                type(self).REWARD_SMALL,
                disable_notification=True,
                )
            await sender.send_notification(
                _(
                    'Do you want to talk with somebody, practice in foreign languages or you'
                    ' just want to have some fun? Rand Talk will help you!'
                    ' It\'s a bot matching you with a random stranger of desired sex'
                    ' speaking on your language. {0}',
                    ),
                self.get_invitation_link(),
                disable_notification=True,
                disable_web_page_preview=True,
                )
        except TelegramError as err:
            LOGGER.warning('Advertise. Can\'t notify the stranger. %s', err)

    def advertise_later(self):
        # pylint: disable=attribute-defined-outside-init
        self._deferred_advertising = asyncio.get_event_loop().create_task(self._advertise())

    async def end_talk(self):
        if self.looking_for_partner_from is not None:
            # If stranger is looking for partner
            self.looking_for_partner_from = None

            try:
                await self.get_sender().send_notification(_('Looking for partner was stopped.'))
            except TelegramError as err:
                LOGGER.warning('End chatting. Can\'t notify stranger %d: %s', self.id, err)
        elif self.get_partner() is not None:
            # If stranger is chatting now
            try:
                await self._notify_talk_ended(by_self=True)
            except StrangerError as err:
                LOGGER.warning('End chatting. Can\'t notify stranger %d: %s', self.id, err)

        await self.set_partner(None)

    def get_common_languages(self, partner):
        partner_languages = partner.get_languages()
        return [language for language in self.get_languages() if language in partner_languages]

    def get_invitation_link(self):
        start_args = self.get_start_args()
        return f'https://telegram.me/RandTalkBot?start={start_args}'

    def get_languages(self):
        try:
            return json.loads(self.languages)
        except ValueError:
            # If languages field was corrupted, return default language.
            return ['en']
        except TypeError:
            # If languages field wasn't set.
            return []

    def get_partner(self):
        try:
            return self._partner
        except AttributeError:
            talk = self.get_talk()
            # pylint: disable=attribute-defined-outside-init
            self._partner = None if talk is None else talk.get_partner(self)
            return self._partner

    def get_sender(self):
        return StrangerSenderService.get_instance().get_or_create_stranger_sender(self)

    def get_start_args(self):
        args = {
            'i': self.invitation,
            }
        serialized_args = json.dumps(args, separators=(',', ':'))
        serialized_args = base64.urlsafe_b64encode(serialized_args.encode('utf-8'))
        return serialized_args.decode('utf-8')

    def get_talk(self):
        try:
            return self._talk
        except AttributeError:
            from .talk import Talk
            # pylint: disable=attribute-defined-outside-init
            self._talk = Talk.get_talk(self)
            return self._talk

    def is_novice(self):
        return self.languages is None and \
            self.sex is None and \
            self.partner_sex is None

    def is_full(self):
        return self.languages is not None and \
            self.sex is not None and \
            self.partner_sex is not None

    async def kick(self):
        try:
            await self._notify_talk_ended(by_self=False)
        except StrangerError as err:
            LOGGER.warning('Kick. Can\'t notify stranger %d: %s', self.id, err)
        self._pay_for_talk()
        # pylint: disable=attribute-defined-outside-init
        self._talk = None
        # pylint: disable=attribute-defined-outside-init
        self._partner = None

    def mute_bonuses_notifications(self):
        # pylint: disable=attribute-defined-outside-init
        self._bonuses_notifications_muted = True
        asyncio.get_event_loop().create_task(self._unmute_bonuses_notifications(self.bonus_count))
        LOGGER.debug('Bonuses notifications were muted for %d', self.id)

    async def _unmute_bonuses_notifications(self, last_bonuses_count):
        await asyncio.sleep(type(self).UNMUTE_BONUSES_NOTIFICATIONS_DELAY)
        await self._notify_about_bonuses(self.bonus_count - last_bonuses_count)
        # pylint: disable=attribute-defined-outside-init
        self._bonuses_notifications_muted = False

    async def _notify_about_bonuses(self, bonuses_delta):
        sender = self.get_sender()
        try:
            if bonuses_delta == 1:
                await sender.send_notification(
                    _(
                        'You\'ve received one bonus for inviting a person to the bot. '
                        'Bonuses will help you to find partners quickly. Total bonuses count: {0}. '
                        'Congratulations!\n'
                        'To mute this notifications, use /mute\\_bonuses.'
                        ),
                    self.bonus_count,
                    )
            elif bonuses_delta > 1:
                await sender.send_notification(
                    _(
                        'You\'ve received {0} bonuses for inviting a person to the bot. '
                        'Bonuses will help you to find partners quickly. Total bonuses count: {1}. '
                        'Congratulations!\n'
                        'To mute this notifications, use /mute\\_bonuses.'
                        ),
                    bonuses_delta,
                    self.bonus_count,
                    )
        except TelegramError as err:
            LOGGER.info('Can\'t notify stranger %d about bonuses: %s', self.id, err)

    async def _notify_talk_ended(self, by_self):
        """Raises:
            StrangerError: If stranger we're changing has blocked the bot.
        """
        sender = self.get_sender()
        _ = sender._
        sentences = []

        if by_self:
            sentences.append(_('Chat was finished.'))
        else:
            sentences.append(_('Your partner has left chat.'))

        talk = self.get_talk()
        if talk is not None and talk.is_successful() and self == talk.partner1 and \
                self.bonus_count >= 1:
            if self.bonus_count - 1:
                bonuses_notification = _('You\'ve used one bonus. {0} bonus(es) left.').format(
                    self.bonus_count - 1,
                    )
            else:
                bonuses_notification = _('You\'ve used your last bonus.')
            sentences.append(bonuses_notification)

        sentences.append(_('Feel free to /begin a new talk.'))

        try:
            await sender.send_notification(' '.join(sentences))
        except TelegramError as err:
            raise StrangerError() from err

    async def notify_partner_found(self, partner):
        """Raises:
            StrangerError: If stranger we're changing has blocked the bot.
        """
        self.prevent_advertising()
        sender = self.get_sender()
        _ = sender._
        sentences = []

        common_languages = self.get_common_languages(partner)
        if len(self.get_languages()) > len(common_languages):
            # To make the bot speak on common language.
            sender.update_translation(partner)
            _ = sender._
            # If the stranger knows any language which another partner doesn't, we should notify him
            # especial way.
            if len(common_languages) == 1:
                languages_limitations = _('Use {0} please.').format(
                    get_languages_names(common_languages),
                    )
            else:
                languages_limitations = _('You can use the following languages: {0}.').format(
                    get_languages_names(common_languages),
                    )
        else:
            languages_limitations = None

        if self.get_partner() is None:
            sentences.append(_('Your partner is here.'))
        else:
            talk = self.get_talk()
            if talk.is_successful() and self == talk.partner1 and self.bonus_count >= 1:
                if self.bonus_count - 1:
                    bonuses_notification = _(
                        'You\'ve used one bonus with previous partner. {0} bonus(es) left.'
                        ).format(self.bonus_count - 1)
                else:
                    bonuses_notification = _('You\'ve used your last bonus with previous partner.')
                sentences.append(bonuses_notification)
            sentences.append(_('Here\'s another stranger.'))

        if languages_limitations:
            sentences.append(languages_limitations)

        if partner.looking_for_partner_from:
            looked_for_partner_for = datetime.datetime.utcnow() - partner.looking_for_partner_from
            if looked_for_partner_for >= type(self).LONG_WAITING_TIMEDELTA:
                # Notify Stranger if his partner did wait too much and could be asleep.
                if type(self).HOUR_TIMEDELTA <= looked_for_partner_for:
                    long_waiting_notification = _(
                        'Your partner\'s been looking for you for {0} hr. Say him \"Hello\" -- '
                        'if he doesn\'t respond to you, launch search again by /begin command.',
                        ).format(round(looked_for_partner_for.total_seconds() / 3600))
                else:
                    long_waiting_notification = _(
                        'Your partner\'s been looking for you for {0} min. Say him \"Hello\" -- '
                        'if he doesn\'t respond to you, launch search again by /begin command.',
                        ).format(round(looked_for_partner_for.total_seconds() / 60))
                sentences.append(long_waiting_notification)

        if len(sentences) < 2:
            sentences.append(_('Have a nice chat!'))

        try:
            await sender.send_notification(' '.join(sentences))
        except TelegramError as err:
            raise StrangerError(f'Can\'t notify stranger {self.id}') from err
        finally:
            # To reset languages.
            sender.update_translation()

    async def pay(self, delta, gratitude):
        self.bonus_count += delta
        self.save()
        sender = self.get_sender()
        try:
            await sender.send_notification(
                'You\'ve earned {0} bonuses. Total bonus amount: {1}. {2}',
                delta,
                self.bonus_count,
                gratitude,
                )
        except TelegramError as err:
            LOGGER.info('Pay. Can\'t notify stranger %d: %s', self.id, err)

    def _pay_for_talk(self):
        talk = self.get_talk()
        if talk is not None and talk.is_successful() and self == talk.partner1 and \
                self.bonus_count >= 1:
            self.bonus_count -= 1
            self.save()

    def prevent_advertising(self):
        try:
            if not self._deferred_advertising:
                return
        except AttributeError:
            return
        self._deferred_advertising.cancel()
        # pylint: disable=attribute-defined-outside-init
        self._deferred_advertising = None

    async def _reward_inviter(self):
        if self.was_invited_as is not None or self.invited_by_id is None:
            return

        talk = self.get_talk()
        threshold_messages_count = 1

        if talk is None or talk.partner1_sent != threshold_messages_count or \
                talk.partner2_sent != threshold_messages_count:
            return

        LOGGER.debug('Rewarding inviter of %d', self.id)
        self.was_invited_as = self.sex
        self.save()
        sex_ratio = StatsService.get_instance().get_stats().get_sex_ratio()

        if (self.sex == 'female' and sex_ratio >= 1) or (self.sex == 'male' and sex_ratio < 1):
            reward = type(self).REWARD_BIG
        else:
            reward = type(self).REWARD_SMALL

        # pylint: disable=no-member,protected-access
        await self.invited_by._add_bonuses(reward)

    async def send(self, message):
        """Raises:
            StrangerError: If can't send message because of unknown content type.
            TelegramError: If stranger has blocked the bot.
        """
        sender = self.get_sender()

        try:
            await sender.send(message)
        except StrangerSenderError as err:
            raise StrangerError('Can\'t send content') from err

    async def send_to_partner(self, message):
        """Raises:
            MissingPartnerError: If there's no partner for this stranger.
            StrangerError: If can't send content.
            TelegramError: If the partner has blocked the bot.
        """
        partner = self.get_partner()

        if partner is None:
            raise MissingPartnerError()

        try:
            await partner.send(message)
        except:
            raise
        else:
            self.get_talk().increment_sent(self)
            await self._reward_inviter()

    def set_languages(self, languages):
        """Raises:
            EmptyLanguagesError: If no languages were specified.
            StrangerError: If too much languages were specified.
        """
        if languages == ['same']:
            languages = self.get_languages()

        if not languages:
            raise EmptyLanguagesError()

        languages = json.dumps(languages)

        if len(languages) > LANGUAGES_MAX_LENGTH:
            raise StrangerError()

        self.languages = languages

    async def set_looking_for_partner(self):
        # Before setting `looking_for_partner_from`, check if it's already set
        # to prevent lowering priority.
        if self.looking_for_partner_from is None:
            self.looking_for_partner_from = datetime.datetime.utcnow()

        try:
            await self.get_sender().send_notification(
                _('Looking for a stranger for you.'),
                )
        except TelegramError as err:
            LOGGER.debug(
                'Set looking for partner. Can\'t notify stranger. %s',
                err,
                )
            self.looking_for_partner_from = None

        await self.set_partner(None)

    async def set_partner(self, partner):
        if self.get_partner() == partner:
            self.save()
            return

        if self._partner is not None:
            if self._partner.get_partner() == self:
                # If partner isn't talking with the stranger because of some
                # error, we shouldn't kick him.
                await self._partner.kick()

            self._pay_for_talk()

            if self._talk is not None:
                self._talk.end = datetime.datetime.utcnow()
                self._talk.save()

        if partner is None:
            # pylint: disable=attribute-defined-outside-init
            self._talk = None
            # pylint: disable=attribute-defined-outside-init
            self._partner = None
        else:
            from .talk import Talk
            # pylint: disable=attribute-defined-outside-init
            self._talk = Talk.create(
                partner1=self,
                partner2=partner,
                searched_since=partner.looking_for_partner_from,
                )
            # pylint: disable=attribute-defined-outside-init
            self._partner = partner

            if self.looking_for_partner_from is not None:
                self.looking_for_partner_from = None
                self.save()

            # pylint: disable=protected-access
            partner._talk = self._talk
            # pylint: disable=protected-access
            partner._partner = self
            partner.looking_for_partner_from = None
            partner.save()

    def set_sex(self, sex_name):
        """Raises:
            SexError
        """
        self.sex = Stranger._get_sex_code(sex_name)

    def set_partner_sex(self, partner_sex_name):
        """Raises:
            SexError
        """
        self.partner_sex = Stranger._get_sex_code(partner_sex_name)

    def speaks_on_language(self, language):
        return language in self.get_languages()
