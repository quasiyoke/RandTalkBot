# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from os import path

__version__ = '1.3'
RANDTALKBOT_DIR = path.abspath(path.dirname(__file__))
LOCALE_DIR = path.join(RANDTALKBOT_DIR, 'locale')
