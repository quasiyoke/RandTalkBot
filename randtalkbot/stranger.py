# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
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

    class Meta:
        database = database_proxy
        indexes = (
            (('partner', 'looking_for_partner_from'), False),
            (('partner', 'sex', 'partner_sex', 'looking_for_partner_from'), False),
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
                _('You\'ve received one bonus for inviting a person to the bot. You can use it to find '
                    'a partner quickly. Total bonus count: {0}. Congratulations!'),
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
                _('You\'re still searching for partner among {0} people. You can talk with some of them if you '
                    'remove partner\'s sex restrictions or extend the list of languages you know using /setup '
                    'command. You can share the link to the bot between your friends: telegram.me/RandTalkBot '
                    'or [vote for Rand Talk](https://telegram.me/storebot?start=randtalkbot). More people '
                    '-- more fun!'),
                searching_for_partner_count,
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
        return set(self.get_languages()).intersection(partner.get_languages())

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
    def send_notification_about_another_partner(self, partner):
        '''
        Notifies the stranger about retrieving a partner in case when (s)he DID HAS one.

        @raise TelegramError if stranger has blocked the bot.
        '''
        sender = self.get_sender()
        common_languages = self.get_common_languages(partner)
        if set(self.get_languages()) > common_languages:
            # If the stranger knows any language which another partner doesn't, we should notify him
            # especial way.
            if len(common_languages) == 1:
                yield from sender.send_notification(
                    _('Here\'s another stranger. Use {0} please.'),
                    get_languages_names(common_languages),
                    )
            else:
                yield from sender.send_notification(
                    _('Here\'s another stranger. You can use the following languages: {0}.'),
                    get_languages_names(common_languages),
                    )
        else:
            yield from sender.send_notification(_('Here\'s another stranger. Have fun!'))

    @asyncio.coroutine
    def send_notification_about_retrieving_partner(self, partner):
        '''
        Notifies the stranger about retrieving a partner in case when (s)he DIDN'T HAS one.

        @raise TelegramError if stranger has blocked the bot.
        '''
        sender = self.get_sender()
        common_languages = self.get_common_languages(partner)
        if set(self.get_languages()) > common_languages:
            # If the stranger knows any language which another partner doesn't, we should notify him
            # especial way.
            if len(common_languages) == 1:
                yield from sender.send_notification(
                    _('Your partner is here. Use {0} please.'),
                    get_languages_names(common_languages),
                    )
            else:
                yield from sender.send_notification(
                    _('Your partner is here. You can use the following languages: {0}.'),
                    get_languages_names(common_languages),
                    )
        else:
            yield from sender.send_notification(_('Your partner is here. Have a nice chat!'))

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
        '''
        @raise StrangerError If stranger we're changing has blocked the bot.
        '''
        self.looking_for_partner_from = None
        self.prevent_advertising()
        try:
            if self.partner:
                if self.partner.partner == self:
                    # If partner isn't talking with the stranger because of some error, we shouldn't kick him.
                    yield from self.partner.kick()
                try:
                    yield from self.send_notification_about_another_partner(partner)
                except TelegramError as e:
                    LOGGER.warning('Set partner. Can\'t notify stranger %d: %s', self.id, e)
                    self.partner = None
                    raise StrangerError(e)
            else:
                try:
                    yield from self.send_notification_about_retrieving_partner(partner)
                except TelegramError as e:
                    LOGGER.warning('Set partner. Can\'t notify stranger %d: %s', self.id, e)
                    raise StrangerError(e)
            self.partner = partner
        finally:
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
