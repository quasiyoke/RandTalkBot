# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import codecs
import json
import logging
from pathlib import Path

LOGGER = logging.getLogger('randtalkbot.configuration')

class ConfigurationObtainingError(Exception):
    pass

def get_secret(name):
    """Tries to read Docker secret.

    Returns:
        secret (str): Secret value.

    """
    secret_path = Path('/run/secrets/') / name

    try:
        with open(secret_path, 'r') as file_descriptor:
            return file_descriptor.read() \
                .strip()
    except OSError as err:
        LOGGER.debug('Can\'t obtain secret %s through %s path. %s', name, secret_path, err)

class Configuration:
    def __init__(self, path):
        reader = codecs.getreader('utf-8')

        try:
            with open(path, 'rb') as file_descriptor:
                configuration_json = json.load(reader(file_descriptor))
        except OSError as err:
            reason = f'Troubles with opening \"{path}\"'
            LOGGER.exception(reason)
            raise ConfigurationObtainingError(reason) from err
        except ValueError as err:
            reason = f'Troubles with parsing \"{path}\"'
            LOGGER.exception(reason)
            raise ConfigurationObtainingError(reason) from err

        self.database_password = get_secret('db_password')
        self.token = get_secret('token')

        try:
            self.database_host = configuration_json['database']['host']
            self.database_name = configuration_json['database']['name']
            self.database_user = configuration_json['database']['user']

            if self.database_password is None:
                self.database_password = configuration_json['database']['password']

            self.logging = configuration_json['logging']

            if self.token is None:
                self.token = configuration_json['token']
        except (KeyError, TypeError) as err:
            reason = 'Troubles with obtaining parameters'
            LOGGER.exception(reason)
            raise ConfigurationObtainingError(reason) from err

        self.admins_telegram_ids = configuration_json.get('admins', [])
