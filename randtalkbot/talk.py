# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import logging
from .errors import WrongStrangerError
from .stranger import Stranger
from .stranger_service import StrangerService
from peewee import *

LOGGER = logging.getLogger('randtalkbot.talk')

def _(s): return s

database_proxy = Proxy()

class Talk(Model):
    partner1 = ForeignKeyField(Stranger, related_name='talks_as_partner1')
    partner1_sent = IntegerField(default=0)
    partner2 = ForeignKeyField(Stranger, related_name='talks_as_partner2')
    partner2_sent = IntegerField(default=0)
    searched_since = DateTimeField()
    begin = DateTimeField(default=datetime.datetime.utcnow)
    end = DateTimeField(index=True, null=True)

    class Meta:
        database = database_proxy

    @classmethod
    def get_talk(cls, stranger):
        try:
            talk = cls.get(((cls.partner1 == stranger) | (cls.partner2 == stranger)) & (cls.end == None))
        except DoesNotExist:
            return None
        else:
            stranger_service = StrangerService.get_instance()
            talk.partner1 = stranger_service.get_cached_stranger(talk.partner1)
            talk.partner2 = stranger_service.get_cached_stranger(talk.partner2)
            return talk

    def get_partner(self, stranger):
        if stranger == self.partner1:
            return self.partner2
        elif stranger == self.partner2:
            return self.partner1
        else:
            raise WrongStrangerError()

    def get_sent(self, stranger):
        if stranger == self.partner1:
            return self.partner1_sent
        elif stranger == self.partner2:
            return self.partner2_sent
        else:
            raise WrongStrangerError()

    def increment_sent(self, stranger):
        if stranger == self.partner1:
            self.partner1_sent += 1
        elif stranger == self.partner2:
            self.partner2_sent += 1
        else:
            raise WrongStrangerError()
        self.save()
