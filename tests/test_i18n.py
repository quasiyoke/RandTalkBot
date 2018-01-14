# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from unittest.mock import call, patch
from randtalkbot.i18n import get_languages_names, get_languages_codes, get_translation, \
    LanguageNotFoundError

class TestI18n(unittest.TestCase):
    def test_get_languages_names__supported(self):
        self.assertEqual(get_languages_names(['ru']), 'Русский')

    def test_get_languages_names__not_supported(self):
        self.assertEqual(get_languages_names(['aa', 'ru']), 'Afar, Русский')

    def test_get_languages_names__unknown(self):
        with self.assertRaises(LanguageNotFoundError):
            get_languages_names('foo')

    def test_get_languages_codes__ok(self):
        self.assertEqual(get_languages_codes('   Русский  ,AFAR,, enGLIsh,  '), ['ru', 'aa', 'en'])

    def test_get_languages_codes__duplicates(self):
        self.assertEqual(
            get_languages_codes('enGLIsh, Afar, English, aa, rus'),
            ['en', 'aa', 'ru'],
            )

    def test_get_languages_codes__same(self):
        self.assertEqual(get_languages_codes('Не менять языки'), ['same'])

    def test_get_languages_codes__empty(self):
        self.assertEqual(get_languages_codes(''), [])

    def test_get_languages_codes__quotes(self):
        self.assertEqual(get_languages_codes('“«\"English, German\"”»'), ['en', 'de'])

    def test_get_languages_codes__unknown(self):
        with self.assertRaises(LanguageNotFoundError):
            get_languages_codes('Foo language')

    def test_get_languages_codes__has_no_iso639_1_code(self):
        with self.assertRaises(LanguageNotFoundError):
            get_languages_codes('zza')

    @patch('randtalkbot.i18n.gettext')
    @patch('randtalkbot.i18n.LOCALE_DIR', 'foo_locale_dir')
    def test_get_translation__no_languages(self, gettext):
        self.assertEqual(get_translation([]), gettext.translation.return_value.gettext)
        gettext.translation.assert_called_once_with(
            'randtalkbot',
            localedir='foo_locale_dir',
            languages=['en'],
            )

    @patch('randtalkbot.i18n.gettext')
    @patch('randtalkbot.i18n.LOCALE_DIR', 'foo_locale_dir')
    def test_get_translation__ok(self, gettext):
        self.assertEqual(get_translation(['foo']), gettext.translation.return_value.gettext)
        gettext.translation.assert_called_once_with(
            'randtalkbot',
            localedir='foo_locale_dir',
            languages=['foo'],
            )

    @patch('randtalkbot.i18n.gettext')
    @patch('randtalkbot.i18n.LOCALE_DIR', 'foo_locale_dir')
    def test_get_translation__not_supported_language(self, gettext):
        gettext.translation.side_effect = OSError
        with self.assertRaises(OSError):
            get_translation(['foo'])
        self.assertEqual(
            gettext.translation.call_args_list,
            [
                call(
                    'randtalkbot',
                    localedir='foo_locale_dir',
                    languages=['foo'],
                    ),
                call(
                    'randtalkbot',
                    localedir='foo_locale_dir',
                    languages=['en'],
                    ),
                ],
            )
