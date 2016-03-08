# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import asynctest
from randtalkbot.errors import *
from randtalkbot.stranger_handler import *
from randtalkbot.stranger_sender_service import *
from randtalkbot.stranger_service import StrangerServiceError
from randtalkbot.stranger_setup_wizard import StrangerSetupWizard
from asynctest.mock import create_autospec, patch, Mock, CoroutineMock

class TestStrangerSetupWizard(asynctest.TestCase):
    @patch('randtalkbot.stranger_sender_service.StrangerSenderService._instance')
    def setUp(self, stranger_sender_service):
        self.stranger = Mock()
        self.stranger.telegram_id = 31416
        self.sender = stranger_sender_service.get_or_create_stranger_sender.return_value
        self.stranger_setup_wizard = StrangerSetupWizard(self.stranger)
        self.stranger_sender_service = stranger_sender_service

    @asynctest.ignore_loop
    def test_init(self):
        self.stranger_sender_service.get_or_create_stranger_sender.assert_called_once_with(self.stranger)

    def test_activate(self):
        self.stranger_setup_wizard._prompt = CoroutineMock()
        yield from self.stranger_setup_wizard.activate()
        self.assertEqual(self.stranger.wizard, 'setup')
        self.assertEqual(self.stranger.wizard_step, 'languages')
        self.stranger.save.assert_called_once_with()
        self.stranger_setup_wizard._prompt.assert_called_once_with()

    def test_deactivate(self):
        self.stranger_setup_wizard._prompt = CoroutineMock()
        yield from self.stranger_setup_wizard.deactivate()
        self.assertEqual(self.stranger.wizard, 'none')
        self.assertEqual(self.stranger.wizard_step, None)
        self.stranger.save.assert_called_once_with()
        self.sender.send_notification.assert_called_once_with(
            'Thank you. Use /begin to start looking for a conversational partner, ' + \
                'once you\'re matched you can use /end to end the conversation.',
            reply_markup={'hide_keyboard': True},
            )
        self.stranger_setup_wizard._prompt.assert_not_called()

    def test_handle__deactivated_novice(self):
        self.stranger.wizard = 'none'
        self.stranger.is_novice = Mock(return_value=True)
        self.stranger_setup_wizard.activate = CoroutineMock()
        message = Mock()
        message.text = 'foo_text'
        self.assertTrue((yield from self.stranger_setup_wizard.handle(message)))
        self.stranger_setup_wizard.activate.assert_called_once_with()

    def test_handle__deactivated_not_novice(self):
        self.stranger.wizard = 'none'
        self.stranger.is_novice = Mock(return_value=False)
        self.stranger_setup_wizard.activate = CoroutineMock()
        message = Mock()
        message.text = 'foo_text'
        self.assertFalse((yield from self.stranger_setup_wizard.handle(message)))
        self.stranger_setup_wizard.activate.assert_not_called()

    def test_handle__other_wizard(self):
        self.stranger.wizard = 'other_wizard'
        self.stranger_setup_wizard.activate = CoroutineMock()
        message = Mock()
        message.text = 'foo_text'
        self.assertFalse((yield from self.stranger_setup_wizard.handle(message)))
        self.stranger_setup_wizard.activate.assert_not_called()

    @patch('randtalkbot.stranger_setup_wizard.get_languages_codes', Mock())
    @asyncio.coroutine
    def test_handle__languages_ok(self):
        from randtalkbot.stranger_setup_wizard import get_languages_codes
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'languages'
        get_languages_codes.return_value = 'foo_languages_codes'
        self.stranger_setup_wizard._prompt = CoroutineMock()
        message = Mock()
        message.text = 'foo_text'
        self.assertTrue((yield from self.stranger_setup_wizard.handle(message)))
        get_languages_codes.assert_called_once_with('foo_text')
        self.stranger.set_languages.assert_called_once_with('foo_languages_codes')
        self.stranger_setup_wizard._prompt.assert_called_once_with()
        self.assertEqual(self.stranger.wizard_step, 'sex')
        self.stranger.save.assert_called_once_with()
        self.sender.update_translation.assert_called_once_with()

    @patch('randtalkbot.stranger_setup_wizard.get_languages_codes', Mock())
    @asyncio.coroutine
    def test_handle__languages_empty_languages_error(self):
        from randtalkbot.stranger_setup_wizard import get_languages_codes
        from randtalkbot.errors import EmptyLanguagesError
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'languages'
        get_languages_codes.side_effect = EmptyLanguagesError()
        self.stranger_setup_wizard._prompt = CoroutineMock()
        message = Mock()
        message.text = 'foo_text'
        self.assertTrue((yield from self.stranger_setup_wizard.handle(message)))
        get_languages_codes.assert_called_once_with('foo_text')
        self.stranger.set_languages.assert_not_called()
        self.stranger_setup_wizard._prompt.assert_called_once_with()
        self.sender.send_notification.assert_called_once_with('Please specify at least one language.')

    @patch('randtalkbot.stranger_setup_wizard.get_languages_codes', Mock())
    @asyncio.coroutine
    def test_handle__languages_language_not_found(self):
        from randtalkbot.stranger_setup_wizard import get_languages_codes
        from randtalkbot.i18n import LanguageNotFoundError
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'languages'
        get_languages_codes.side_effect = LanguageNotFoundError('foo_lang')
        self.stranger_setup_wizard._prompt = CoroutineMock()
        message = Mock()
        message.text = 'foo_text'
        self.assertTrue((yield from self.stranger_setup_wizard.handle(message)))
        get_languages_codes.assert_called_once_with('foo_text')
        self.stranger.set_languages.assert_not_called()
        self.stranger_setup_wizard._prompt.assert_called_once_with()
        self.sender.send_notification.assert_called_once_with(
            'Language "{0}" wasn\'t found.',
            'foo_lang',
            )

    @patch('randtalkbot.stranger_setup_wizard.LOGGER', Mock())
    @patch('randtalkbot.stranger_setup_wizard.get_languages_codes', Mock())
    @asyncio.coroutine
    def test_handle__languages_too_much(self):
        from randtalkbot.stranger_setup_wizard import get_languages_codes
        from randtalkbot.stranger_setup_wizard import LOGGER
        from randtalkbot.errors import StrangerError
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'languages'
        get_languages_codes.return_value = 'languages_codes'
        self.stranger.set_languages.side_effect = StrangerError()
        self.stranger_setup_wizard._prompt = CoroutineMock()
        message = Mock()
        message.text = 'foo_text'
        self.assertTrue((yield from self.stranger_setup_wizard.handle(message)))
        self.stranger.set_languages.assert_called_once_with('languages_codes')
        self.stranger_setup_wizard._prompt.assert_called_once_with()
        self.sender.send_notification.assert_called_once_with(
            'Too much languages were specified. Please shorten your list to 6 languages.',
            )
        LOGGER.info.assert_called_once_with('Too much languages were specified: \"%s\"', 'foo_text')

    def test_handle__sex_ok(self):
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'sex'
        self.stranger_setup_wizard._prompt = CoroutineMock()
        self.stranger.sex = 'some_sex'
        message = Mock()
        message.text = 'foo_text'
        self.assertTrue((yield from self.stranger_setup_wizard.handle(message)))
        self.stranger.set_sex.assert_called_once_with('foo_text')
        self.stranger_setup_wizard._prompt.assert_called_once_with()
        self.assertEqual(self.stranger.wizard_step, 'partner_sex')
        self.stranger.save.assert_called_once_with()

    def test_handle__sex_not_specified(self):
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'sex'
        self.stranger_setup_wizard._prompt = CoroutineMock()
        self.stranger_setup_wizard.deactivate = CoroutineMock()
        self.stranger.sex = 'not_specified'
        message = Mock()
        message.text = 'foo_text'
        self.assertTrue((yield from self.stranger_setup_wizard.handle(message)))
        self.stranger.set_sex.assert_called_once_with('foo_text')
        self.stranger_setup_wizard.deactivate.assert_called_once_with()
        self.stranger_setup_wizard._prompt.assert_not_called()
        self.stranger.save.assert_not_called()

    def test_handle__sex_sex_error(self):
        from randtalkbot.errors import SexError
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'sex'
        self.stranger_setup_wizard._prompt = CoroutineMock()
        self.stranger.set_sex.side_effect = SexError('foo_sex')
        message = Mock()
        message.text = 'foo_text'
        self.assertTrue((yield from self.stranger_setup_wizard.handle(message)))
        self.stranger.set_sex.assert_called_once_with('foo_text')
        self.stranger_setup_wizard._prompt.assert_called_once_with()
        self.sender.send_notification.assert_called_once_with(
            'Unknown sex: "{0}" -- is not a valid sex name.',
            'foo_sex',
            )

    def test_handle__partner_sex_ok(self):
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'partner_sex'
        self.stranger_setup_wizard._prompt = CoroutineMock()
        self.stranger_setup_wizard.deactivate = CoroutineMock()
        self.stranger.partner_sex = 'some_partner_sex'
        message = Mock()
        message.text = 'foo_text'
        self.assertTrue((yield from self.stranger_setup_wizard.handle(message)))
        self.stranger.set_partner_sex.assert_called_once_with('foo_text')
        self.stranger_setup_wizard.deactivate.assert_called_once_with()
        self.stranger_setup_wizard._prompt.assert_not_called()
        self.assertEqual(self.stranger.wizard_step, 'partner_sex')
        self.stranger.save.assert_not_called()

    def test_handle__partner_sex_sex_error(self):
        from randtalkbot.errors import SexError
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'partner_sex'
        self.stranger_setup_wizard._prompt = CoroutineMock()
        self.stranger.set_partner_sex.side_effect = SexError('foo_sex')
        message = Mock()
        message.text = 'foo_text'
        self.assertTrue((yield from self.stranger_setup_wizard.handle(message)))
        self.stranger.set_partner_sex.assert_called_once_with('foo_text')
        self.stranger_setup_wizard._prompt.assert_called_once_with()
        self.sender.send_notification.assert_called_once_with(
            'Unknown sex: "{0}" -- is not a valid sex name.',
            'foo_sex',
            )

    @patch('randtalkbot.stranger_setup_wizard.LOGGER', Mock())
    @asyncio.coroutine
    def test_handle__unknown_wizard_step(self):
        from randtalkbot.stranger_setup_wizard import LOGGER
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'unknown_step'
        self.stranger_setup_wizard._prompt = CoroutineMock()
        message = Mock()
        message.text = 'foo_text'
        self.assertTrue((yield from self.stranger_setup_wizard.handle(message)))
        self.stranger_setup_wizard._prompt.assert_not_called()
        self.sender.send_notification.assert_not_called()
        LOGGER.warning.assert_called_once_with('Undknown wizard_step value was found: "%s"', 'unknown_step')

    def test_handle_command__not_activated_handled(self):
        self.stranger.wizard = 'none'
        message = Mock()
        message.command = 'begin'
        self.stranger_setup_wizard.handle = CoroutineMock(return_value=True)
        self.assertTrue((yield from self.stranger_setup_wizard.handle_command(message)))
        self.stranger_setup_wizard.handle.assert_called_once_with(message)

    def test_handle_command__not_activated_not_handled(self):
        self.stranger.wizard = 'none'
        message = Mock()
        message.command = 'begin'
        self.stranger_setup_wizard.handle = CoroutineMock(return_value=False)
        self.assertFalse((yield from self.stranger_setup_wizard.handle_command(message)))
        self.stranger_setup_wizard.handle.assert_called_once_with(message)

    def test_handle_command__not_activated_command_start(self):
        self.stranger.wizard = 'none'
        message = Mock()
        message.command = 'start'
        self.stranger_setup_wizard.handle = CoroutineMock(return_value=True)
        self.assertFalse((yield from self.stranger_setup_wizard.handle_command(message)))
        self.stranger_setup_wizard.handle.assert_called_once_with(message)

    def test_handle_command__full_stranger(self):
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'sex'
        self.stranger.is_full.return_value = True
        self.stranger_setup_wizard._prompt = CoroutineMock()
        self.stranger_setup_wizard.deactivate = CoroutineMock()
        message = Mock()
        message.command = 'begin'
        self.assertFalse((yield from self.stranger_setup_wizard.handle_command(message)))
        self.stranger.is_full.assert_called_once_with()
        self.stranger_setup_wizard._prompt.assert_not_called()
        self.stranger_setup_wizard.deactivate.assert_called_once_with()

    def test_handle_command__not_full_stranger(self):
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'sex'
        self.stranger.is_full.return_value = False
        self.stranger_setup_wizard._prompt = CoroutineMock()
        message = Mock()
        message.command = 'begin'
        self.assertTrue((yield from self.stranger_setup_wizard.handle_command(message)))
        self.sender.send_notification.assert_called_once_with(
            'Finish setup process please. After that you can start using bot.',
            )
        self.stranger_setup_wizard._prompt.assert_called_once_with()

    @patch(
        'randtalkbot.stranger_setup_wizard.SUPPORTED_LANGUAGES_NAMES',
        ('English', 'Português', 'Italiano', 'Русский', ),
        )
    @asyncio.coroutine
    def test_prompt__no_languages(self):
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'languages'
        self.stranger.get_languages.return_value = []
        yield from self.stranger_setup_wizard._prompt()
        self.sender.send_notification.assert_called_once_with(
            'Enumerate the languages you speak like this: "English, Italian" -- in descending ' + \
                'order of your speaking convenience or just pick one at special keyboard.',
            '',
            reply_markup={'keyboard': [('English', 'Português'), ('Italiano', 'Русский')]},
            )

    @patch(
        'randtalkbot.stranger_setup_wizard.SUPPORTED_LANGUAGES_NAMES',
        ('English', 'Português', 'Italiano', 'Русский', ),
        )
    @asyncio.coroutine
    def test_prompt__one_language(self):
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'languages'
        self.stranger.get_languages.return_value = ['pt']
        yield from self.stranger_setup_wizard._prompt()
        self.sender.send_notification.assert_called_once_with(
            'Your current language is {0}. Enumerate the languages you speak like this: '
                '"English, Italian" -- in descending order of your speaking convenience '
                'or just pick one at special keyboard.',
            'Português',
            reply_markup={
                'keyboard': [
                    ('English', 'Português'),
                    ('Italiano', 'Русский'),
                    ['Leave the language unchanged'],
                    ]
                },
            )

    @patch(
        'randtalkbot.stranger_setup_wizard.SUPPORTED_LANGUAGES_NAMES',
        ('English', 'Português', 'Italiano', 'Русский', ),
        )
    @asyncio.coroutine
    def test_prompt__many_language(self):
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'languages'
        self.stranger.get_languages.return_value = ['pt', 'de', 'en']
        yield from self.stranger_setup_wizard._prompt()
        self.sender.send_notification.assert_called_once_with(
            'Your current languages are: {0}. Enumerate the languages you speak the same way '
                '-- in descending order of your speaking convenience or just pick one '
                'at special keyboard.',
            'Português, Deutsch, English',
            reply_markup={
                'keyboard': [
                    ('English', 'Português'),
                    ('Italiano', 'Русский'),
                    ['Leave the languages unchanged'],
                    ]
                },
            )

    @patch(
        'randtalkbot.stranger_setup_wizard.get_languages_names',
        Mock(side_effect=LanguageNotFoundError('')),
        )
    @patch(
        'randtalkbot.stranger_setup_wizard.SUPPORTED_LANGUAGES_NAMES',
        ('English', 'Português', 'Italiano', 'Русский', ),
        )
    @patch('randtalkbot.stranger_setup_wizard.LOGGER', Mock())
    @asyncio.coroutine
    def test_prompt__unknown_languages(self):
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'languages'
        self.stranger.get_languages.return_value = []
        yield from self.stranger_setup_wizard._prompt()
        self.sender.send_notification.assert_called_once_with(
            'Enumerate the languages you speak like this: "English, Italian" -- in descending ' + \
                'order of your speaking convenience or just pick one at special keyboard.',
            '',
            reply_markup={'keyboard': [('English', 'Português'), ('Italiano', 'Русский')]},
            )

    def test_prompt__sex(self):
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'sex'
        yield from self.stranger_setup_wizard._prompt()
        self.sender.send_notification.assert_called_once_with(
            'Set up your sex. If you pick "Not Specified" you can\'t choose your partner\'s sex.',
            reply_markup={'keyboard': [('Female', 'Male'), ('Not specified',)]},
            )

    def test_prompt__partner_sex(self):
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'partner_sex'
        yield from self.stranger_setup_wizard._prompt()
        self.sender.send_notification.assert_called_once_with(
            'Choose your partner\'s sex',
            reply_markup={'keyboard': [('Female', 'Male'), ('Not specified',)]},
            )

    def test_prompt__other_step(self):
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'foo_step'
        yield from self.stranger_setup_wizard._prompt()
        self.sender.send_notification.assert_not_called()
