# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''randtalkbot.randtalkbot: provides entry point main().'''

import asyncio
import logging
import logging.config
import sys
from .bot import Bot
from .configuration import Configuration, ConfigurationObtainingError
from .db import DB
from .errors import DBError
from .stats_service import StatsService
from .stranger_sender_service import StrangerSenderService
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
        sys.exit('Can\'t obtain configuration. {}'.format(e))

    logging.config.dictConfig(configuration.logging)

    try:
        db = DB(configuration)
    except DBError as e:
        sys.exit('Can\'t construct DB. {}'.format(e))

    if arguments['install']:
        LOGGER.info('Installing RandTalkBot')
        try:
            db.install()
        except DBError as e:
            sys.exit('Can\'t install databases. {}'.format(e))
    else:
        LOGGER.info('Executing RandTalkBot')
        loop = asyncio.get_event_loop()

        stats_service = StatsService()
        loop.create_task(stats_service.run())

        bot = Bot(configuration)
        loop.create_task(bot.run())

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            LOGGER.info('Execution was finished by keyboard interrupt')
