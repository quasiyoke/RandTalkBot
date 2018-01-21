# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from .errors import StrangerSenderServiceError
from .stranger_sender import StrangerSender

LOGGER = logging.getLogger('randtalkbot.stranger_sender_service')


class StrangerSenderService:
    _instance = None

    def __init__(self, bot):
        self._bot = bot

    @classmethod
    def get_instance(cls):
        """Raises:
            StrangerSenderServiceError: If the instance wasn't initialized.

        Returns:
            StrangerSenderService

        """
        if cls._instance is None:
            raise StrangerSenderServiceError('Instance wasn\'t initialized')

        return cls._instance

    @classmethod
    def initialize(cls, bot):
        if cls._instance is not None:
            return

        cls._instance = cls(bot)

    def get_stranger_sender(self, stranger_id):
        return StrangerSender(self._bot, stranger_id)
