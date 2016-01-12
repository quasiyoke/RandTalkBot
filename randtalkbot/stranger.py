# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import datetime
import logging
from .stranger_sender import StrangerSenderError
from .stranger_sender_service import StrangerSenderService
from peewee import *

database_proxy = Proxy()

class MissingPartnerError(Exception):
    pass

class StrangerError(Exception):
    pass

class Stranger(Model):
    telegram_id = IntegerField(unique=True)
    partner = ForeignKeyField('self', null=True)
    looking_for_partner_from = DateTimeField(null=True)

    class Meta:
        database = database_proxy
        indexes = (
            (('partner', 'looking_for_partner_from'), False),
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

    def get_sender(self):
        return StrangerSenderService.get_instance().get_or_create_stranger_sender(self.telegram_id)

    @asyncio.coroutine
    def kick(self):
        self.partner = None
        sender = self.get_sender()
        yield from sender.send_notification(
            'Your partner has left chat. Feel free to /begin a new conversation.',
            )
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
