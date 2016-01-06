# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''randtalkbot.randtalkbot: provides entry point main().'''

__version__ = '0.1'

from .bot import Bot
from docopt import docopt

doc = '''RandTalkBot

Usage:
  randtalkbot CONFIGURATION
  randtalkbot -h | --help | --version

Arguments:
  CONFIGURATION  Path to configuration.json file.
'''

def main():
    arguments = docopt(doc, version=__version__)
    print('Executing RandTalkBot v. {0}'.format(__version__))
    print(arguments['CONFIGURATION'])
    Bot()
