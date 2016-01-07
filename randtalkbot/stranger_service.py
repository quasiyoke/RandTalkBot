# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from .stranger import Stranger

class StrangerObtainingError(Exception):
    pass

class StrangerService:
    def __init__(self):
        self._strangers = {}

    def get_stranger(self, telegram_id):
        try:
            return self._strangers[telegram_id]
        except KeyError:
            raise StrangerObtainingError('Stranger with such telegram_id wasn\'t found')

    def get_or_create_stranger(self, telegram_id):
        try:
            return self._strangers[telegram_id]
        except KeyError:
            stranger = Stranger(telegram_id)
            self._strangers[telegram_id] = stranger
            return stranger
