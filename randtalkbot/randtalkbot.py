# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''randtalkbot.randtalkbot: provides entry point main().'''

import logging
import logging.config
import sys
from .bot import Bot
from .configuration import Configuration, ConfigurationObtainingError
from .stranger_sender_service import StrangerSenderService
from .stranger_service import StrangerService, StrangerServiceError
from .utils import __version__
from docopt import docopt
from randtalkbot import stranger, stranger_service

DOC = '''RandTalkBot

Usage:
  randtalkbot CONFIGURATION
  randtalkbot install CONFIGURATION
  randtalkbot -h | --help | --version

Arguments:
  CONFIGURATION  Path to configuration.json file.
'''
LOGGER = logging.getLogger('randtalkbot')

def main():
    arguments = docopt(DOC, version=__version__)
    logging.basicConfig(level=logging.DEBUG)

    try:
        configuration = Configuration(arguments['CONFIGURATION'])
    except ConfigurationObtainingError as e:
        LOGGER.error('Can\'t obtain configuration: %s', e)
        sys.exit('Can\'t obtain configuration: %s' % e)

    logging.config.dictConfig(configuration.logging)

    try:
        stranger_service = StrangerService(configuration)
    except StrangerServiceError as e:
        LOGGER.error('Can\'t construct StrangerService: %s', e)
        sys.exit('Can\'t construct StrangerService: %s' % e)

    if arguments['install']:
        LOGGER.info('Installing RandTalkBot.')
        try:
            stranger_service.install()
        except StrangerServiceError as e:
            LOGGER.error('Can\'t install StrangerService: %s', e)
            sys.exit('Can\'t install StrangerService: %s' % e)
    else:
        LOGGER.info('Executing RandTalkBot.')
        bot = Bot(configuration, stranger_service)
        try:
            bot.start_listening()
        except KeyboardInterrupt:
            LOGGER.info('Execution was finished by keyboard interrupt.')
