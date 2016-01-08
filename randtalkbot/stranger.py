# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import datetime
import logging

class MissingPartnerError(Exception):
    pass

class Stranger:
    def __init__(self, telegram_id, handler):
        self.telegram_id = telegram_id
        self._handler = handler
        self._is_chatting = False
        self._partner = None
        self.is_looking_for_partner = False
        self.looking_for_partner_from = None

    @asyncio.coroutine
    def end_chatting(self):
        if self._is_chatting:
            yield from self._partner.kick()
            yield from self._handler.send_notification('Chat was finished. Feel free to /begin a new one.')
        elif self.is_looking_for_partner:
            yield from self._handler.send_notification('Looking for partner was stopped.')
        self._is_chatting = False
        self._partner = None
        self.is_looking_for_partner = False
        self.looking_for_partner_from = None

    @asyncio.coroutine
    def kick(self):
        self._is_chatting = False
        self._partner = None
        yield from self._handler.send_notification('Your partner has left chat. Feel free to /begin a new conversation.')

    @asyncio.coroutine
    def set_partner(self, partner):
        if self._is_chatting:
            yield from self._handler.send_notification('Here\'s another stranger. Have fun!')
        else:
            yield from self._handler.send_notification('Your partner is here. Have a nice chat!')
        self._is_chatting = True
        self._partner = partner
        self.is_looking_for_partner = False
        self.looking_for_partner_from = None

    @asyncio.coroutine
    def send(self, content_type, content_kwargs):
        yield from self._handler.send(content_type, content_kwargs)

    @asyncio.coroutine
    def send_to_partner(self, content_type, content_kwargs):
        if self._is_chatting:
            yield from self._partner.send(content_type, content_kwargs)
        else:
            raise MissingPartnerError()

    @asyncio.coroutine
    def set_looking_for_partner(self):
        if self._is_chatting:
            yield from self._partner.kick()
        self._is_chatting = False
        self._partner = None
        self.is_looking_for_partner = True
        self.looking_for_partner_from = datetime.datetime.now()
        yield from self._handler.send_notification('Looking for a stranger for you.')
