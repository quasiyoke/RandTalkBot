# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

class Stranger:
    def __init__(self, telegram_id):
        self.telegram_id = telegram_id
        self.is_chatting = False
