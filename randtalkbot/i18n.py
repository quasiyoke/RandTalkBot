# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from collections import OrderedDict
import gettext
import logging
import os
import pycountry
from .utils import LOCALE_DIR

LOGGER = logging.getLogger('randtalkbot.i18n')
QUOTES = '\"\'“”«»'

class LanguageNotFoundError(Exception):
    def __init__(self, name):
        super(LanguageNotFoundError, self).__init__('Language \"{0}\" wasn\'t found.'.format(name))
        self.name = name

def _get_deduplicated(list_instance):
    """Removes duplicates keeping list order.

    >>> _get_deduplicated(['ru', 'en', 'ru', ])
    ['ru', 'en', ]
    """
    return list(OrderedDict.fromkeys(list_instance))

def _get_language_code(name):
    """Raises:
        LanguageNotFoundError: If unable to recognize the language.

    Returns:
        str: Language code.
    """
    try:
        return LANGUAGES_NAMES_TO_CODES[name.lower()]
    except KeyError:
        raise LanguageNotFoundError(name)

def _get_language_name(code):
    """Raises:
        LanguageNotFoundError: If unable to recognize the language.

    Returns:
        str: Language name.
    """
    try:
        return LANGUAGES_CODES_TO_NAMES[code]
    except KeyError:
        raise LanguageNotFoundError(code)

def get_languages_names(codes):
    """Raises:
        LanguageNotFoundError: If unable to recognize some language.

    Returns:
        str: Comma-separated list of languages' names.
    """
    names = map(_get_language_name, codes)
    return ', '.join(names)

def get_languages_codes(names):
    """Raises:
        LanguageNotFoundError: If unable to recognize some language.

    Returns:
        list<str>: Deduplicated list of languages' codes.
    """
    names = ''.join([c for c in names if c not in QUOTES])

    if names.strip().lower() in SAME_LANGUAGE_NAMES:
        return ['same']

    names = [name.strip() for name in names.split(',')]
    compact_names = filter(bool, names)
    languages_codes = map(_get_language_code, compact_names)
    unique_languages_codes = _get_deduplicated(languages_codes)
    return unique_languages_codes

def get_translation(languages):
    if not languages:
        languages = ['en']

    try:
        translation_instance = gettext.translation(
            'randtalkbot',
            localedir=LOCALE_DIR,
            languages=languages,
            )
    except OSError:
        translation_instance = gettext.translation(
            'randtalkbot',
            localedir=LOCALE_DIR,
            languages=['en'],
            )

    return translation_instance.gettext

def get_translations():
    for filename in os.listdir(LOCALE_DIR):
        if os.path.isdir(os.path.join(LOCALE_DIR, filename)):
            yield get_translation([filename])

SUPPORTED_LANGUAGES_NAMES_CHOICES = (
    ('en', 'English'),
    ('ru', 'Русский'),
    ('fa', 'فارسی'),
    ('it', 'Italiano'),
    ('fr', 'French'),
    ('de', 'Deutsch'),
    ('es', 'Español'),
    ('pt', 'Português'),
    )
LANGUAGES_CODES_TO_NAMES = \
    {item[0].lower(): item[1] for item in SUPPORTED_LANGUAGES_NAMES_CHOICES}
SUPPORTED_LANGUAGES_NAMES = list(zip(*SUPPORTED_LANGUAGES_NAMES_CHOICES))[1]
LANGUAGES_NAMES_TO_CODES = \
    {item[1].lower(): item[0] for item in SUPPORTED_LANGUAGES_NAMES_CHOICES}
SAME_LANGUAGE_NAMES = []
for translation in get_translations():
    SAME_LANGUAGE_NAMES.append(translation('Leave the language unchanged').lower())
    SAME_LANGUAGE_NAMES.append(translation('Leave the languages unchanged').lower())

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
