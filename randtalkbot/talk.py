# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import logging
from peewee import DateTimeField, DoesNotExist, ForeignKeyField, IntegerField, Model, Proxy
from .errors import WrongStrangerError
from .stranger import Stranger
from .stranger_service import StrangerService

LOGGER = logging.getLogger('randtalkbot.talk')
DATABASE_PROXY = Proxy()


def _(string_instance):
    return string_instance


class Talk(Model):
    partner1 = ForeignKeyField(Stranger, related_name='talks_as_partner1')
    partner1_sent = IntegerField(default=0)
    partner2 = ForeignKeyField(Stranger, related_name='talks_as_partner2')
    partner2_sent = IntegerField(default=0)
    searched_since = DateTimeField()
    begin = DateTimeField(default=datetime.datetime.utcnow)
    end = DateTimeField(index=True, null=True)

    class Meta:
        database = DATABASE_PROXY

    @classmethod
    def delete_old(cls, before):
        cls.delete().where(Talk.end < before).execute()

    @classmethod
    def get_ended_talks(cls, after=None):
        talks = cls.select()
        if after is None:
            talks = talks.where(Talk.end != None)
        else:
            talks = talks.where(Talk.end >= after)
        return talks

    @classmethod
    def get_last_partners_ids(cls, stranger_id):
        """Args:
            stranger_id (int)

        Yields:
            int: IDs of last partners.

        """
        talks = cls.select() \
            .where((cls.partner1_id == stranger_id) | (cls.partner2_id == stranger_id))

        for talk in talks:
            yield talk.get_partner_id(stranger_id)

    @classmethod
    def get_not_ended_talks(cls, after=None):
        # pylint: disable=singleton-comparison
        talks = cls.select().where(cls.end == None)
        if after is not None:
            talks = talks.where(Talk.begin >= after)
        return talks

    @classmethod
    def get_talk_by_partner_id(cls, stranger_id):
        try:
            # pylint: disable=singleton-comparison
            talk = cls.get(
                ((cls.partner1_id == stranger_id) | (cls.partner2_id == stranger_id)) &
                (cls.end == None),
                )
        except DoesNotExist:
            return None
        else:
            return talk

    def get_partner_id(self, stranger_id):
        """Raises:
            WrongStrangerError: If given stranger isn't a partner in the talk.
        """
        if stranger_id == self.partner1_id:
            return self.partner2_id
        elif stranger_id == self.partner2_id:
            return self.partner1_id
        else:
            LOGGER.error('Stranger %s isn\'t a partner in the talk %d', stranger_id, self.id)
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

    def is_successful(self):
        return self.partner1_sent and self.partner2_sent
