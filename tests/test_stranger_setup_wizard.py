# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import asynctest
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
        self.stranger_sender_service.get_or_create_stranger_sender.assert_called_once_with(31416)

    def test_activate(self):
        self.stranger_setup_wizard._send_invitation = CoroutineMock()
        yield from self.stranger_setup_wizard.activate()
        self.assertEqual(self.stranger.wizard, 'setup')
        self.assertEqual(self.stranger.wizard_step, 'languages')
        self.stranger.save.assert_called_once_with()
        self.stranger_setup_wizard._send_invitation.assert_called_once_with()

    def test_deactivate(self):
        self.stranger_setup_wizard._send_invitation = CoroutineMock()
        yield from self.stranger_setup_wizard.deactivate()
        self.assertEqual(self.stranger.wizard, 'none')
        self.assertEqual(self.stranger.wizard_step, None)
        self.stranger.save.assert_called_once_with()
        self.sender.send_notification.assert_called_once_with(
            'Thank you. Use /begin to start looking for a conversational partner, ' + \
                'once you\'re matched you can use /end to end the conversation.',
            reply_markup={'hide_keyboard': True},
            )
        self.stranger_setup_wizard._send_invitation.assert_not_called()

    def test_handle__deactivated_novice(self):
        self.stranger.wizard = 'none'
        self.stranger.is_novice = Mock(return_value=True)
        self.stranger_setup_wizard.activate = CoroutineMock()
        self.assertTrue((yield from self.stranger_setup_wizard.handle('foo_text')))
        self.stranger_setup_wizard.activate.assert_called_once_with()

    def test_handle__deactivated_not_novice(self):
        self.stranger.wizard = 'none'
        self.stranger.is_novice = Mock(return_value=False)
        self.stranger_setup_wizard.activate = CoroutineMock()
        self.assertFalse((yield from self.stranger_setup_wizard.handle('foo_text')))
        self.stranger_setup_wizard.activate.assert_not_called()

    def test_handle__other_wizard(self):
        self.stranger.wizard = 'other_wizard'
        self.stranger_setup_wizard.activate = CoroutineMock()
        self.assertFalse((yield from self.stranger_setup_wizard.handle('foo_text')))
        self.stranger_setup_wizard.activate.assert_not_called()

    @patch('randtalkbot.stranger_setup_wizard.get_languages_codes', Mock())
    @asyncio.coroutine
    def test_handle__languages_ok(self):
        from randtalkbot.stranger_setup_wizard import get_languages_codes
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'languages'
        get_languages_codes.return_value = 'foo_languages_codes'
        self.stranger_setup_wizard._send_invitation = CoroutineMock()
        self.assertTrue((yield from self.stranger_setup_wizard.handle('foo_text')))
        get_languages_codes.assert_called_once_with('foo_text')
        self.stranger.set_languages.assert_called_once_with('foo_languages_codes')
        self.stranger_setup_wizard._send_invitation.assert_called_once_with()
        self.assertEqual(self.stranger.wizard_step, 'sex')
        self.stranger.save.assert_called_once_with()

    @patch('randtalkbot.stranger_setup_wizard.get_languages_codes', Mock())
    @asyncio.coroutine
    def test_handle__languages_language_not_found(self):
        from randtalkbot.stranger_setup_wizard import get_languages_codes
        from randtalkbot.i18n import LanguageNotFoundError
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'languages'
        get_languages_codes.side_effect = LanguageNotFoundError('foo_lang')
        self.stranger_setup_wizard._send_invitation = CoroutineMock()
        self.assertTrue((yield from self.stranger_setup_wizard.handle('foo_text')))
        get_languages_codes.assert_called_once_with('foo_text')
        self.stranger.set_languages.assert_not_called()
        self.stranger_setup_wizard._send_invitation.assert_called_once_with()
        self.sender.send_notification.assert_called_once_with('Language "foo_lang" wasn\'t found.')

    @patch('randtalkbot.stranger_setup_wizard.get_languages_codes', Mock())
    @asyncio.coroutine
    def test_handle__languages_empty_languages_error(self):
        from randtalkbot.stranger_setup_wizard import get_languages_codes
        from randtalkbot.stranger import EmptyLanguagesError
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'languages'
        get_languages_codes.side_effect = EmptyLanguagesError()
        self.stranger_setup_wizard._send_invitation = CoroutineMock()
        self.assertTrue((yield from self.stranger_setup_wizard.handle('foo_text')))
        get_languages_codes.assert_called_once_with('foo_text')
        self.stranger.set_languages.assert_not_called()
        self.stranger_setup_wizard._send_invitation.assert_called_once_with()
        self.sender.send_notification.assert_called_once_with('Please specify at least one language.')

    def test_handle__sex_ok(self):
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'sex'
        self.stranger_setup_wizard._send_invitation = CoroutineMock()
        self.stranger.sex = 'some_sex'
        self.assertTrue((yield from self.stranger_setup_wizard.handle('foo_text')))
        self.stranger.set_sex.assert_called_once_with('foo_text')
        self.stranger_setup_wizard._send_invitation.assert_called_once_with()
        self.assertEqual(self.stranger.wizard_step, 'partner_sex')
        self.stranger.save.assert_called_once_with()

    def test_handle__sex_not_specified(self):
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'sex'
        self.stranger_setup_wizard._send_invitation = CoroutineMock()
        self.stranger_setup_wizard.deactivate = CoroutineMock()
        self.stranger.sex = 'not_specified'
        self.assertTrue((yield from self.stranger_setup_wizard.handle('foo_text')))
        self.stranger.set_sex.assert_called_once_with('foo_text')
        self.stranger_setup_wizard.deactivate.assert_called_once_with()
        self.stranger_setup_wizard._send_invitation.assert_not_called()
        self.stranger.save.assert_not_called()

    def test_handle__sex_sex_error(self):
        from randtalkbot.stranger import SexError
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'sex'
        self.stranger_setup_wizard._send_invitation = CoroutineMock()
        self.stranger.set_sex.side_effect = SexError('foo_sex')
        self.assertTrue((yield from self.stranger_setup_wizard.handle('foo_text')))
        self.stranger.set_sex.assert_called_once_with('foo_text')
        self.stranger_setup_wizard._send_invitation.assert_called_once_with()
        self.sender.send_notification.assert_called_once_with(
            'Unknown sex: "foo_sex" -- is not a valid sex name.',
            )

    def test_handle__partner_sex_ok(self):
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'partner_sex'
        self.stranger_setup_wizard._send_invitation = CoroutineMock()
        self.stranger_setup_wizard.deactivate = CoroutineMock()
        self.stranger.partner_sex = 'some_partner_sex'
        self.assertTrue((yield from self.stranger_setup_wizard.handle('foo_text')))
        self.stranger.set_partner_sex.assert_called_once_with('foo_text')
        self.stranger_setup_wizard.deactivate.assert_called_once_with()
        self.stranger_setup_wizard._send_invitation.assert_not_called()
        self.assertEqual(self.stranger.wizard_step, 'partner_sex')
        self.stranger.save.assert_not_called()

    def test_handle__partner_sex_sex_error(self):
        from randtalkbot.stranger import SexError
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'partner_sex'
        self.stranger_setup_wizard._send_invitation = CoroutineMock()
        self.stranger.set_partner_sex.side_effect = SexError('foo_sex')
        self.assertTrue((yield from self.stranger_setup_wizard.handle('foo_text')))
        self.stranger.set_partner_sex.assert_called_once_with('foo_text')
        self.stranger_setup_wizard._send_invitation.assert_called_once_with()
        self.sender.send_notification.assert_called_once_with(
            'Unknown sex: "foo_sex" -- is not a valid sex name.',
            )

    @patch('randtalkbot.stranger_setup_wizard.logging', Mock())
    @asyncio.coroutine
    def test_handle__unknown_wizard_step(self):
        from randtalkbot.stranger_setup_wizard import logging
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'unknown_step'
        self.stranger_setup_wizard._send_invitation = CoroutineMock()
        self.assertTrue((yield from self.stranger_setup_wizard.handle('foo_text')))
        self.stranger_setup_wizard._send_invitation.assert_not_called()
        self.sender.send_notification.assert_not_called()
        logging.warning.assert_called_once()

    def test_send_invitation__languages(self):
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'languages'
        yield from self.stranger_setup_wizard._send_invitation()
        self.sender.send_notification.assert_called_once_with(
            'Enumerate the languages you speak like this: \"English, Italian\" -- ' + \
                'in order of your speaking convenience or just pick one at special keyboard.',
            reply_markup={'keyboard': [('English', 'Português'), ('Italiano', 'Русский')]},
            )

    def test_send_invitation__sex(self):
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'sex'
        yield from self.stranger_setup_wizard._send_invitation()
        self.sender.send_notification.assert_called_once_with(
            'Set up your sex. If you pick "Not Specified" you can\'t choose your partner\'s sex.',
            reply_markup={'keyboard': [('Female', 'Male'), ('Not specified',)]},
            )

    def test_send_invitation__partner_sex(self):
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'partner_sex'
        yield from self.stranger_setup_wizard._send_invitation()
        self.sender.send_notification.assert_called_once_with(
            'Choose your partner\'s sex',
            reply_markup={'keyboard': [('Female', 'Male'), ('Not specified',)]},
            )

    def test_send_invitation__other_step(self):
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'foo_step'
        yield from self.stranger_setup_wizard._send_invitation()
        self.sender.send_notification.assert_not_called()
