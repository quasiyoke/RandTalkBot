# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gettext
import pycountry
from collections import OrderedDict

SUPPORTED_LANGUAGES_NAMES_CHOICES = (
    ('en', 'English'),
    ('pt', 'Português'),
    ('it', 'Italiano'),
    ('ru', 'Русский'),
    )
SUPPORTED_LANGUAGES_CODES_TO_NAMES = \
    {item[0].lower(): item[1] for item in SUPPORTED_LANGUAGES_NAMES_CHOICES}
SUPPORTED_LANGUAGES_NAMES = list(zip(*SUPPORTED_LANGUAGES_NAMES_CHOICES))[1]
SUPPORTED_LANGUAGES_NAMES_TO_CODES = \
    {item[1].lower(): item[0] for item in SUPPORTED_LANGUAGES_NAMES_CHOICES}

class LanguageNotFoundError(Exception):
    def __init__(self, name):
        super(LanguageNotFoundError, self).__init__('Language \"{0}\" wasn\'t found.'.format(name))
        self.name = name

def _get_deduplicated(a):
    '''
    Removes duplicates keeping list order.

    >>> _get_deduplicated(['ru', 'en', 'ru', ])
    ['ru', 'en', ]
    '''
    return list(OrderedDict.fromkeys(a))

def _get_language_code(name):
    '''
    @throws LanguageNotFoundError
    '''
    try:
        return SUPPORTED_LANGUAGES_NAMES_TO_CODES[name.lower()]
    except KeyError:
        pass
    language = None
    try:
        language = pycountry.languages.get(name=name)
    except KeyError: # If language wasn't found
        try:
            language = pycountry.languages.get(iso639_1_code=name)
        except KeyError: # If language wasn't found
            pass
    if language:
        try:
            return language.iso639_1_code
        except AttributeError: # If language hasn't ISO 639-1 code
            pass
    raise LanguageNotFoundError(name)

def get_language_name(code):
    '''
    @throws LanguageNotFoundError
    '''
    try:
        return SUPPORTED_LANGUAGES_CODES_TO_NAMES[code]
    except KeyError:
        pass
    try:
        language = pycountry.languages.get(iso639_1_code=code)
    except KeyError: # If language wasn't found
        pass
    else:
        try:
            return language.name
        except AttributeError: # If language name wasn't defined
            pass
    raise LanguageNotFoundError(code)

def get_languages_codes(names):
    '''
    @throws LanguageNotFoundError
    '''
    names = [name.strip() for name in names.split(',')]
    names = filter(bool, names)
    names = map(_get_language_code, names)
    names = _get_deduplicated(names)
    return names
