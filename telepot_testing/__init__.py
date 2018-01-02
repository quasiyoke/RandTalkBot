# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2018 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from .aio import create_open, DelegatorBot
from .helpers import assert_sent_message, finalize, receive_message, UPDATES_TIMEOUT
