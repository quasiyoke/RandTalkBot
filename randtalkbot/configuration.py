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
            self.token = configuration_json['token']
        except KeyError as e:
            logging.error('Troubles with obtaining parameters: %s', e)
            raise ConfigurationObtainingError('Troubles with obtaining parameters \"{0}\"'.format(e))
