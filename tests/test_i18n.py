# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from randtalkbot.i18n import get_language_name, get_languages_codes, LanguageNotFoundError
from unittest.mock import patch, Mock

class TestI18n(unittest.TestCase):
    def test_get_language_name__supported(self):
        self.assertEqual(get_language_name('ru'), 'Русский')

    def test_get_language_name__not_supported(self):
        self.assertEqual(get_language_name('de'), 'German')

    def test_get_language_name__unknown(self):
        with self.assertRaises(LanguageNotFoundError):
            get_language_name('foo')

    def test_get_languages_codes__ok(self):
        self.assertEqual(get_languages_codes('   Русский  ,GERMAN,, enGLIsh,  '), ['ru', 'de', 'en'])

    def test_get_languages_codes__duplicates(self):
        self.assertEqual(get_languages_codes('enGLIsh, English, de, rus'), ['en', 'de', 'ru'])

    def test_get_languages_codes__empty(self):
        self.assertEqual(get_languages_codes(''), [])

    @patch('randtalkbot.i18n.logging')
    def test_get_languages_codes__unknown(self, logging):
        with self.assertRaises(LanguageNotFoundError):
            get_languages_codes('Foo language')
        logging.info.assert_called_once()

    @patch('randtalkbot.i18n.logging')
    def test_get_languages_codes__has_no_iso639_1_code(self, logging):
        with self.assertRaises(LanguageNotFoundError):
            get_languages_codes('zza')
        logging.info.assert_called_once()
