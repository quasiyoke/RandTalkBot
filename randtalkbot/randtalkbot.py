# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''randtalkbot.randtalkbot: provides entry point main().'''

__version__ = '0.1'

import logging
import sys
from .bot import Bot
from .configuration import Configuration, ConfigurationObtainingError
from .stranger_service import StrangerService
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
    logging.basicConfig(level=logging.INFO)
    logging.info('Executing RandTalkBot v. {0}'.format(__version__))

    try:
        configuration = Configuration(arguments['CONFIGURATION'])
    except ConfigurationObtainingError as e:
        logging.error('Can\'t obtain configuration: %s', e)
        sys.exit('Can\'t obtain configuration: {0}'.format(e))

    stranger_service = StrangerService()

    bot = Bot(configuration, stranger_service)
    try:
        bot.start_listening()
    except KeyboardInterrupt:
        logging.info('Execution was finished by keyboard interrupt.')
