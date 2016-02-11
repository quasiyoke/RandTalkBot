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
from .i18n import get_languages_names, get_translations
from .stranger_sender import StrangerSenderError
from .stranger_sender_service import StrangerSenderService
from peewee import *
from telepot import TelegramError

INVITATION_CHARS = string.ascii_letters + string.digits + string.punctuation
INVITATION_LENGTH = 10
LANGUAGES_MAX_LENGTH = 40
LOGGER = logging.getLogger('randtalkbot')

def _(s): return s

SEX_CHOICES = (
    ('female', _('Female')),
    ('male', _('Male')),
    ('not_specified', _('Not specified')),
    )
ADDITIONAL_SEX_NAMES_TO_CODES = {
    _('boy'): 'male',
    _('man'): 'male',
    'men': 'male',
    _('girl'): 'female',
    _('woman'): 'female',
}
SEX_NAMES_TO_CODES = {}
SEX_NAMES = list(zip(*SEX_CHOICES))[1]
for translation in get_translations():
    for sex, name in SEX_CHOICES:
        SEX_NAMES_TO_CODES[translation(name).lower()] = sex
    for name, sex in ADDITIONAL_SEX_NAMES_TO_CODES.items():
        SEX_NAMES_TO_CODES[translation(name).lower()] = sex
WIZARD_CHOICES = (
    ('none', 'None'),
    ('setup', 'Setup'),
    )

database_proxy = Proxy()

class EmptyLanguagesError(Exception):
    pass

class MissingPartnerError(Exception):
    pass

class SexError(Exception):
    def __init__(self, sex):
        super(SexError, self).__init__(
            'Unknown sex: \"{0}\" -- is not a valid sex name.'.format(sex),
            )
        self.name = sex

class StrangerError(Exception):
    pass

class Stranger(Model):
    bonus_count = IntegerField(default=0)
    invitation = CharField(max_length=INVITATION_LENGTH, unique=True)
    invited_by = ForeignKeyField('self', null=True, related_name='invited')
    languages = CharField(max_length=LANGUAGES_MAX_LENGTH, null=True)
    looking_for_partner_from = DateTimeField(null=True)
    partner = ForeignKeyField('self', null=True)
    partner_sex = CharField(choices=SEX_CHOICES, max_length=20, null=True)
    sex = CharField(choices=SEX_CHOICES, max_length=20, null=True)
    telegram_id = IntegerField(unique=True)
    wizard = CharField(choices=WIZARD_CHOICES, default='none', max_length=20)
    wizard_step = CharField(max_length=20, null=True)

    ADVERTISING_DELAY = 30
    HOUR_TIMEDELTA = datetime.timedelta(hours=1)
    LONG_WAITING_TIMEDELTA = datetime.timedelta(minutes=5)

    class Meta:
        database = database_proxy
        indexes = (
            (('partner', 'bonus_count', 'looking_for_partner_from'), False),
            (('partner', 'sex', 'partner_sex', 'bonus_count', 'looking_for_partner_from'), False),
            )

    @classmethod
    def get_invitation(self):
        return ''.join([random.choice(INVITATION_CHARS) for i in range(INVITATION_LENGTH)])

    @classmethod
    def _get_sex_code(self, sex_name):
        sex = sex_name.strip().lower()
        try:
            return SEX_NAMES_TO_CODES[sex]
        except KeyError:
            raise SexError(sex_name)

    @asyncio.coroutine
    def add_bonus(self):
        self.bonus_count += 1
        self.save()
        sender = self.get_sender()
        try:
            yield from sender.send_notification(
                _('You\'ve received one bonus for inviting a person to the bot. '
                    'Bonuses will help you to find partners quickly. Total bonus count: {0}. '
                    'Congratulations!'),
                self.bonus_count,
                )
        except TelegramError as e:
            LOGGER.warning('Add bonus. Can\'t notify stranger %d: %s', self.id, e)

    @asyncio.coroutine
    def _advertise(self):
        yield from asyncio.sleep(type(self).ADVERTISING_DELAY)
        self._deferred_advertising = None
        searching_for_partner_count = Stranger.select().where(Stranger.looking_for_partner_from != None) \
            .count()
        if searching_for_partner_count > 1:
            yield from self.get_sender().send_notification(
                _('You\'re still searching for partner among {0} people. You can talk with some of them right '
                    'now if you remove partner\'s sex restrictions or extend the list of languages you know '
                    'using /setup command.\nMore people -- more fun! Spread Rand Talk between your friends. '
                    'The more people will use your link -- the faster partner\'s search will be. Share the '
                    'following message in your chats:'),
                searching_for_partner_count,
                )
            yield from self.get_sender().send_notification(
                _('Do you want to talk with somebody, practice in foreign languages or you just want '
                    'to have some fun? Rand Talk will help you! It\'s a bot matching you with '
                    'a random stranger of desired sex speaking on your language. {0}'),
                'telegram.me/RandTalkBot?start=' + self.get_start_args(),
                )

    def advertise_later(self):
        self._deferred_advertising = asyncio.get_event_loop().create_task(self._advertise())

    @asyncio.coroutine
    def end_chatting(self):
        try:
            sender = self.get_sender()
            if self.looking_for_partner_from:
                # If stranger is looking for partner
                try:
                    yield from sender.send_notification(_('Looking for partner was stopped.'))
                except TelegramError as e:
                    LOGGER.warning('End chatting. Can\'t notify stranger %d: %s', self.id, e)
            elif self.partner:
                # If stranger is chatting now
                try:
                    yield from sender.send_notification(
                        _('Chat was finished. Feel free to /begin a new one.'),
                        )
                except TelegramError as e:
                    LOGGER.warning('End chatting. Can\'t notify stranger %d: %s', self.id, e)
                if self.partner.partner == self:
                    # If partner isn't taking with the stranger because of some error, we shouldn't kick him.
                    yield from self.partner.kick()
        finally:
            self.partner = None
            self.looking_for_partner_from = None
            self.save()

    def get_common_languages(self, partner):
        partner_languages = partner.get_languages()
        return [language for language in self.get_languages() if language in partner_languages]

    def get_languages(self):
        try:
            return json.loads(self.languages)
        except ValueError:
            # If languages field was corrupted, return default language.
            return ['en']
        except TypeError:
            # If languages field wasn't set.
            return []

    def get_sender(self):
        return StrangerSenderService.get_instance().get_or_create_stranger_sender(self)

    def get_start_args(self):
        args = {
            'i': self.invitation,
            }
        args = json.dumps(args, separators=(',', ':'))
        args = base64.urlsafe_b64encode(args.encode('utf-8'))
        return args.decode('utf-8')

    def is_novice(self):
        return self.languages is None and \
            self.sex is None and \
            self.partner_sex is None

    def is_full(self):
        return self.languages is not None and \
            self.sex is not None and \
            self.partner_sex is not None

    @asyncio.coroutine
    def kick(self):
        self.partner = None
        self.save()
        sender = self.get_sender()
        try:
            yield from sender.send_notification(
                _('Your partner has left chat. Feel free to /begin a new conversation.'),
                )
        except TelegramError as e:
            LOGGER.warning('Kick. Can\'t notify stranger %d: %s', self.id, e)

    def notify_partner_found(self, partner):
        '''
        @raise StrangerError If stranger we're changing has blocked the bot.
        '''
        self.prevent_advertising()
        sender = self.get_sender()
        notification_sentences = []

        common_languages = self.get_common_languages(partner)
        if len(self.get_languages()) > len(common_languages):
            # To make the bot speak on common language.
            sender.update_translation(partner)
            # If the stranger knows any language which another partner doesn't, we should notify him
            # especial way.
            if len(common_languages) == 1:
                languages_limitations = sender._(_('Use {0} please.')).format(
                    get_languages_names(common_languages),
                    )
            else:
                languages_limitations = sender._(_('You can use the following languages: {0}.')).format(
                    get_languages_names(common_languages),
                    )
        else:
            languages_limitations = None

        if self.partner:
            notification_sentences.append(sender._(_('Here\'s another stranger.')))
        else:
            notification_sentences.append(sender._(_('Your partner is here.')))

        if self.looking_for_partner_from and self.bonus_count >= 1:
            if self.bonus_count - 1:
                bonuses_notification = sender._(_('You\'ve used one bonus. {0} bonus(es) left.')).format(
                    self.bonus_count - 1,
                    )
            else:
                bonuses_notification = sender._(_('You\'ve used your last bonus.'))
            notification_sentences.append(bonuses_notification)

        if languages_limitations:
            notification_sentences.append(languages_limitations)

        if partner.looking_for_partner_from:
            looked_for_partner_for = datetime.datetime.utcnow() - partner.looking_for_partner_from
            if looked_for_partner_for >= type(self).LONG_WAITING_TIMEDELTA:
                # Notify Stranger if his partner did wait too much and could be asleep.
                if type(self).HOUR_TIMEDELTA <= looked_for_partner_for:
                    long_waiting_notification = sender._(
                        _('Your partner\'s been looking for you for {0} hr. Say him \"Hello\" -- '
                            'if he doesn\'t respond to you, launch search again by /begin command.'),
                        ).format(round(looked_for_partner_for.total_seconds() / 3600))
                else:
                    long_waiting_notification = sender._(
                        _('Your partner\'s been looking for you for {0} min. Say him \"Hello\" -- '
                            'if he doesn\'t respond to you, launch search again by /begin command.'),
                        ).format(round(looked_for_partner_for.total_seconds() / 60))
                notification_sentences.append(long_waiting_notification)

        if len(notification_sentences) == 1:
            notification_sentences.append(sender._(_('Have a nice chat!')))

        try:
            yield from sender.send_notification(' '.join(notification_sentences))
        except TelegramError as e:
            LOGGER.info('Notify stranger partner found. Can\'t notify stranger %d: %s', self.id, e)
            self.partner = None
            raise StrangerError(e)
        finally:
            # To reset languages.
            sender.update_translation()

    @asyncio.coroutine
    def pay(self, delta, gratitude):
        self.bonus_count += delta
        self.save()
        sender = self.get_sender()
        try:
            yield from sender.send_notification(
                'You\'ve earned {0} bonuses. Total bonus amount: {1}. {2}',
                delta,
                self.bonus_count,
                gratitude,
                )
        except TelegramError as e:
            LOGGER.info('Pay. Can\'t notify stranger %d: %s', self.id, e)

    def prevent_advertising(self):
        try:
            if not self._deferred_advertising:
                return
        except AttributeError:
            return
        self._deferred_advertising.cancel()
        self._deferred_advertising = None

    @asyncio.coroutine
    def send(self, message):
        '''
        @raises StrangerError if can't send message because of unknown content type.
        @raises TelegramError if stranger has blocked the bot.
        '''
        sender = self.get_sender()
        try:
            yield from sender.send(message)
        except StrangerSenderError as e:
            raise StrangerError('Can\'t send content: {0}'.format(e))

    @asyncio.coroutine
    def send_to_partner(self, message):
        '''
        @raises StrangerError if can't send content.
        @raises MissingPartnerError if there's no partner for this stranger.
        '''
        if self.partner:
            yield from self.partner.send(message)
        else:
            raise MissingPartnerError()

    def set_languages(self, languages):
        '''
        @EmptyLanguagesError if no languages were specified.
        @StrangerError if too much languages were specified.
        '''
        if languages == ['same']:
            languages = self.get_languages()
        if not len(languages):
            raise EmptyLanguagesError()
        languages = json.dumps(languages)
        if len(languages) > LANGUAGES_MAX_LENGTH:
            raise StrangerError()
        self.languages = languages

    @asyncio.coroutine
    def set_looking_for_partner(self):
        if self.partner:
            yield from self.partner.kick()
        self.partner = None
        # Before setting `looking_for_partner_from`, check if it's already set to prevent lowering
        # priority.
        if not self.looking_for_partner_from:
            self.looking_for_partner_from = datetime.datetime.utcnow()
        yield from self.get_sender().send_notification(
            _('Looking for a stranger for you.'),
            )
        self.save()

    @asyncio.coroutine
    def set_partner(self, partner):
        if self.looking_for_partner_from and self.bonus_count >= 1:
            self.bonus_count -= 1
        if self.partner and self.partner.partner == self:
            # If partner isn't talking with the stranger because of some error, we shouldn't kick him.
            yield from self.partner.kick()
        self.partner = partner
        self.looking_for_partner_from = None
        self.save()

    def set_sex(self, sex_name):
        '''
        @throws SexError
        '''
        self.sex = Stranger._get_sex_code(sex_name)

    def set_partner_sex(self, partner_sex_name):
        '''
        @throws SexError
        '''
        self.partner_sex = Stranger._get_sex_code(partner_sex_name)

    def speaks_on_language(self, language):
        return language in self.get_languages()
