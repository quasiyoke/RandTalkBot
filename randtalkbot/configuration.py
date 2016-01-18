# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import codecs
import json
import logging

class ConfigurationObtainingError(Exception):
    pass

class Configuration:
    def __init__(self, path):
        reader = codecs.getreader('utf-8')
        try:
            with open(path, 'rb') as f:
                configuration_json = json.load(reader(f))
        except OSError as e:
            logging.error('Troubles with opening \"%s\": %s', path, e)
            raise ConfigurationObtainingError('Troubles with opening \"{0}\"'.format(path))
        except ValueError as e:
            logging.error('Troubles with parsing \"%s\": %s', path, e)
            raise ConfigurationObtainingError('Troubles with parsing \"{0}\"'.format(path))

        try:
            self.database_host = configuration_json['database']['host']
            self.database_name = configuration_json['database']['name']
            self.database_user = configuration_json['database']['user']
            self.database_password = configuration_json['database']['password']
            self.token = configuration_json['token']
        except KeyError as e:
            logging.error('Troubles with obtaining parameters: %s', e)
            raise ConfigurationObtainingError('Troubles with obtaining parameters \"{0}\"'.format(e))
        self.admins_telegram_ids = configuration_json.get('admins', [])
        self.debug = configuration_json.get('debug', False)
