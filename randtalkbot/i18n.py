# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gettext
import logging
import pycountry
from collections import OrderedDict

SUPPORTED_LANGUAGES_NAMES_CHOICES = (
    ('en', 'English'),
    ('pt', 'Português'),
    ('it', 'Italiano'),
    ('ru', 'Русский'),
    )
LANGUAGES_CODES_TO_NAMES = \
    {item[0].lower(): item[1] for item in SUPPORTED_LANGUAGES_NAMES_CHOICES}
SUPPORTED_LANGUAGES_NAMES = list(zip(*SUPPORTED_LANGUAGES_NAMES_CHOICES))[1]
LANGUAGES_NAMES_TO_CODES = \
    {item[1].lower(): item[0] for item in SUPPORTED_LANGUAGES_NAMES_CHOICES}

for language in pycountry.languages:
    try:
        LANGUAGES_NAMES_TO_CODES[language.name.lower()] = language.iso639_1_code
        LANGUAGES_NAMES_TO_CODES[language.iso639_1_code] = language.iso639_1_code
        # Not override previosly specified native name.
        if language.iso639_1_code not in LANGUAGES_CODES_TO_NAMES:
            LANGUAGES_CODES_TO_NAMES[language.iso639_1_code] = language.name
    # If it has'n even simplest fields, that's not the languages we are interested in.
    except AttributeError:
        continue
    try:
        LANGUAGES_NAMES_TO_CODES[language.iso639_2T_code] = language.iso639_1_code
    except AttributeError:
        pass

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
        return LANGUAGES_NAMES_TO_CODES[name.lower()]
    except KeyError:
        raise LanguageNotFoundError(name)

def get_language_name(code):
    '''
    @throws LanguageNotFoundError
    '''
    try:
        return LANGUAGES_CODES_TO_NAMES[code]
    except KeyError:
        raise LanguageNotFoundError(code)

def get_languages_codes(names_str):
    '''
    @throws LanguageNotFoundError
    '''
    names = [name.strip() for name in names_str.split(',')]
    names = filter(bool, names)
    try:
        names = map(_get_language_code, names)
        names = _get_deduplicated(names)
    except LanguageNotFoundError as e:
        logging.info('Languages weren\'t parsed: \"%s\"', names_str)
        raise e
    return names
