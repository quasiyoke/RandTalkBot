# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import datetime
import json
import logging
from .stranger_sender import StrangerSenderError
from .stranger_sender_service import StrangerSenderService
from peewee import *

SEX_CHOICES = (
    ('female', 'Female'),
    ('male', 'Male'),
    ('not_specified', 'Not specified'),
    )
SEX_NAMES = list(zip(*SEX_CHOICES))[1]
SEX_NAMES_TO_CODES = {item[1].lower(): item[0] for item in SEX_CHOICES}
WIZARD_MODE_CHOICES = (
    ('none', 'None'),
    ('setup_full', 'Setup full'),
    ('setup_missing', 'Setup missing'),
    )

database_proxy = Proxy()

class MissingPartnerError(Exception):
    pass

class SexError(Exception):
    pass

class StrangerError(Exception):
    pass

class Stranger(Model):
    languages = CharField(max_length=40, null=True)
    looking_for_partner_from = DateTimeField(null=True)
    partner = ForeignKeyField('self', null=True)
    partner_sex = CharField(choices=SEX_CHOICES, max_length=20, null=True)
    sex = CharField(choices=SEX_CHOICES, max_length=20, null=True)
    telegram_id = IntegerField(unique=True)
    wizard_mode = CharField(choices=WIZARD_MODE_CHOICES, default='none', max_length=20)
    wizard_step = CharField(max_length=20, null=True)

    class Meta:
        database = database_proxy
        indexes = (
            (('partner', 'looking_for_partner_from'), False),
            (('partner', 'sex', 'partner_sex', 'looking_for_partner_from'), False),
            )

    @asyncio.coroutine
    def end_chatting(self):
        sender = self.get_sender()
        # If stranger is chatting now
        if self.partner:
            yield from self.partner.kick()
            yield from sender.send_notification('Chat was finished. Feel free to /begin a new one.')
        # If stranger is looking for partner
        elif self.looking_for_partner_from:
            yield from sender.send_notification('Looking for partner was stopped.')
        self.partner = None
        self.looking_for_partner_from = None
        self.save()

    def get_languages_enumeration(self):
        if self.languages:
            languages = json.loads(self.languages)
        else:
            return '(none)'
        return ', '.join(languages)

    def get_sender(self):
        return StrangerSenderService.get_instance().get_or_create_stranger_sender(self.telegram_id)

    def is_empty(self):
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
        sender = self.get_sender()
        yield from sender.send_notification(
            'Your partner has left chat. Feel free to /begin a new conversation.',
            )
        self.save()

    @asyncio.coroutine
    def send(self, content_type, content_kwargs):
        '''
        @throws StrangerError if can't send content.
        '''
        sender = self.get_sender()
        try:
            yield from sender.send(content_type, content_kwargs)
        except StrangerSenderError as e:
            raise StrangerError('Can\'t send content: {0}'.format(e))

    @asyncio.coroutine
    def send_to_partner(self, content_type, content_kwargs):
        '''
        @throws StrangerError if can't send content.
        @throws MissingPartnerError if there's no partner for this stranger.
        '''
        if self.partner:
            yield from self.partner.send(content_type, content_kwargs)
        else:
            raise MissingPartnerError()

    def set_languages(self, languages):
        languages = json.dumps(languages)
        self.languages = languages
        self.save()

    @asyncio.coroutine
    def set_looking_for_partner(self):
        if self.partner:
            yield from self.partner.kick()
        self.partner = None
        # Before setting `looking_for_partner_from`, check if it's already set to prevent lowering priority.
        if not self.looking_for_partner_from:
            self.looking_for_partner_from = datetime.datetime.utcnow()
        yield from self.get_sender().send_notification('Looking for a stranger for you.')
        self.save()

    @asyncio.coroutine
    def set_partner(self, partner):
        sender = self.get_sender()
        if self.partner:
            yield from sender.send_notification('Here\'s another stranger. Have fun!')
        else:
            yield from sender.send_notification('Your partner is here. Have a nice chat!')
        self.partner = partner
        self.looking_for_partner_from = None
        self.save()

    def set_sex(self, sex):
        sex = sex.strip().lower()
        try:
            sex = SEX_NAMES_TO_CODES[sex]
        except KeyError:
            raise SexError('\"{0}\" is not a valid sex name.'.format(sex))
        self.sex = sex
        self.save()

    def set_partner_sex(self, partner_sex):
        partner_sex = partner_sex.strip().lower()
        try:
            partner_sex = SEX_NAMES_TO_CODES[partner_sex]
        except KeyError:
            raise SexError('\"{0}\" is not a valid sex name.'.format(sex))
        self.partner_sex = partner_sex
        self.save()

    def speaks_on_language(self, language):
        if self.languages:
            languages = json.loads(self.languages)
        else:
            return False
        return language in languages
