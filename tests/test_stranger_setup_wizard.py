# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asynctest
from asynctest.mock import patch, Mock, CoroutineMock
from telepot.exception import TelegramError
from randtalkbot.errors import EmptyLanguagesError, SexError
from randtalkbot.i18n import LanguageNotFoundError
from randtalkbot.stranger_setup_wizard import StrangerSetupWizard


class TestStrangerSetupWizard(asynctest.TestCase):
    def setUp(self):
        self.stranger = Mock()
        self.stranger.id = 31
        self.stranger.telegram_id = 31416
        self.sender = CoroutineMock()
        self.stranger_setup_wizard = StrangerSetupWizard(self.stranger.id)

    @patch('randtalkbot.stranger_setup_wizard.LOGGER', Mock())
    async def test_deactivate__telegram_error(self):
        from randtalkbot.stranger_setup_wizard import LOGGER as logger_mock
        self.sender.send_notification.side_effect = TelegramError({}, '', 0)
        self.stranger_setup_wizard._get_sender = Mock(return_value=self.sender)
        self.stranger_setup_wizard._get_stranger = Mock(return_value=self.stranger)
        await self.stranger_setup_wizard.deactivate()
        self.assertTrue(logger_mock.warning.called)

    async def test_handle__other_wizard(self):
        self.stranger.wizard = 'other_wizard'
        self.stranger_setup_wizard._get_stranger = Mock(return_value=self.stranger)
        self.stranger_setup_wizard.activate = CoroutineMock()
        message = Mock()
        message.text = 'foo_text'
        self.assertFalse((await self.stranger_setup_wizard.handle(message)))
        self.stranger_setup_wizard.activate.assert_not_called()

    @patch('randtalkbot.stranger_setup_wizard.LOGGER', Mock())
    async def test_handle__unknown_wizard_step(self):
        from randtalkbot.stranger_setup_wizard import LOGGER as logger_mock
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'unknown_step'
        self.stranger_setup_wizard._get_stranger = Mock(return_value=self.stranger)
        self.stranger_setup_wizard._prompt = CoroutineMock()
        message = Mock()
        message.text = 'foo_text'
        self.assertTrue((await self.stranger_setup_wizard.handle(message)))
        self.stranger_setup_wizard._prompt.assert_not_called()
        self.sender.send_notification.assert_not_called()
        logger_mock.warning \
            .assert_called_once_with('Undknown wizard_step value was found: "%s"', 'unknown_step')

    @patch('randtalkbot.stranger_setup_wizard.LOGGER', Mock())
    @patch('randtalkbot.stranger_setup_wizard.get_languages_codes', Mock())
    async def test_handle__telegram_error(self):
        from randtalkbot.stranger_setup_wizard import LOGGER as logger_mock
        from randtalkbot.stranger_setup_wizard import get_languages_codes
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'languages'
        get_languages_codes.side_effect = EmptyLanguagesError()
        self.stranger_setup_wizard._get_sender = Mock(return_value=self.sender)
        self.stranger_setup_wizard._get_stranger = Mock(return_value=self.stranger)
        self.stranger_setup_wizard._prompt = CoroutineMock()
        message = Mock()
        message.text = 'foo_text'
        self.sender.send_notification.side_effect = TelegramError({}, '', 0)
        self.assertTrue((await self.stranger_setup_wizard.handle(message)))
        self.assertTrue(logger_mock.warning.called)

    @patch('randtalkbot.stranger_setup_wizard.LOGGER', Mock())
    async def test_handle_command__telegram_error(self):
        from randtalkbot.stranger_setup_wizard import LOGGER as logger_mock
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'sex'
        self.stranger.is_full.return_value = False
        self.stranger_setup_wizard._get_sender = Mock(return_value=self.sender)
        self.stranger_setup_wizard._get_stranger = Mock(return_value=self.stranger)
        self.stranger_setup_wizard._prompt = CoroutineMock()
        message = Mock()
        message.command = 'begin'
        self.sender.send_notification.side_effect = TelegramError({}, '', 0)
        self.assertTrue((await self.stranger_setup_wizard.handle_command(message)))
        self.assertTrue(logger_mock.warning.called)

    @patch('randtalkbot.stranger_setup_wizard.LOGGER', Mock())
    async def test_prompt__unknown_step(self):
        from randtalkbot.stranger_setup_wizard import LOGGER as logger_mock
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'foo_step'
        self.stranger_setup_wizard._get_sender = Mock(return_value=self.sender)
        self.stranger_setup_wizard._get_stranger = Mock(return_value=self.stranger)
        await self.stranger_setup_wizard._prompt()
        self.sender.send_notification.assert_not_called()
        self.assertTrue(logger_mock.warning.called)

    @patch('randtalkbot.stranger_setup_wizard.LOGGER', Mock())
    async def test_prompt__telegram_error(self):
        from randtalkbot.stranger_setup_wizard import LOGGER as logger_mock
        from randtalkbot.stranger_setup_wizard import StrangerService as stranger_service_mock
        from randtalkbot.stranger_setup_wizard import StrangerSenderService as \
            stranger_sender_service_mock
        self.stranger.wizard = 'setup'
        self.stranger.wizard_step = 'languages'
        self.stranger.get_languages.return_value = []
        self.stranger_setup_wizard._get_sender = Mock(return_value=self.sender)
        self.stranger_setup_wizard._get_stranger = Mock(return_value=self.stranger)
        self.sender.send_notification.side_effect = TelegramError({}, '', 0)
        await self.stranger_setup_wizard._prompt()
        self.assertTrue(logger_mock.warning.called)
