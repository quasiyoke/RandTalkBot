# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""randtalkbot.randtalkbot: provides entry point main()."""

import asyncio
import logging
import logging.config
import os
import sys
from docopt import docopt
from .bot import Bot
from .configuration import Configuration, ConfigurationObtainingError
from .db import DB
from .errors import DBError
from .stats_service import StatsService
from .utils import __version__

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
    except ConfigurationObtainingError as err:
        sys.exit(f'Can\'t obtain configuration. {err}')

    logging.config.dictConfig(configuration.logging)

    try:
        db = DB(configuration)
    except DBError as err:
        LOGGER.exception('Can\'t construct DB')
        sys.exit(getattr(os, 'EX_CONFIG', 78))

    if arguments['install']:
        LOGGER.info('Installing RandTalkBot')

        try:
            db.install()
        except DBError as err:
            sys.exit(f'Can\'t install databases. {err}')
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
