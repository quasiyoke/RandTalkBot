# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import asynctest
from randtalkbot.admin_handler import AdminHandler
from randtalkbot.stranger_handler import StrangerHandler
from randtalkbot.stranger_service import StrangerServiceError
from randtalkbot.stranger_setup_wizard import StrangerSetupWizard
from asynctest.mock import create_autospec, patch, Mock, CoroutineMock

class TestAdminHandler(asynctest.TestCase):
    @patch('randtalkbot.stranger_handler.StrangerSetupWizard', create_autospec(StrangerSetupWizard))
    @patch('randtalkbot.stranger_sender_service.StrangerSenderService._instance')
    def setUp(self, stranger_sender_service):
        from randtalkbot.stranger_handler import StrangerSetupWizard
        self.stranger = CoroutineMock()
        self.stranger_service = Mock()
        self.stranger_service.get_or_create_stranger.return_value = self.stranger
        StrangerSetupWizard.reset_mock()
        self.StrangerSetupWizard = StrangerSetupWizard
        self.stranger_setup_wizard = StrangerSetupWizard.return_value
        self.stranger_setup_wizard.handle = CoroutineMock()
        self.initial_msg = {
            'chat': {
                'id': 31416,
                },
            }
        self.sender = stranger_sender_service.get_or_create_stranger_sender.return_value
        self.admin_handler = AdminHandler(
            (Mock(), self.initial_msg, 31416),
            self.stranger_service,
            )
        self.stranger_sender_service = stranger_sender_service

    def test_handle_command__clear(self):
        stranger = CoroutineMock()
        self.stranger_service.get_stranger.return_value = stranger
        message = Mock()
        message.command = 'clear'
        message.command_args = '31416'
        yield from self.admin_handler.handle_command(message)
        self.stranger_service.get_stranger.assert_called_once_with(31416)
        stranger.end_chatting.assert_called_once_with()
        self.sender.send_notification.assert_called_once_with('Stranger was cleared.')

    def test_handle_command__clear_incorrect_telegram_id(self):
        message = Mock()
        message.command = 'clear'
        message.command_args = 'foo'
        yield from self.admin_handler.handle_command(message)
        self.stranger_service.get_stranger.assert_not_called()
        self.sender.send_notification.assert_called_once_with(
            'Please specify Telegram ID like this: /clear 31416',
            )

    def test_handle_command__clear_unknown_stranger(self):
        error = StrangerServiceError()
        self.stranger_service.get_stranger.side_effect = error
        message = Mock()
        message.command = 'clear'
        message.command_args = '31416'
        yield from self.admin_handler.handle_command(message)
        self.stranger_service.get_stranger.assert_called_once_with(31416)
        self.sender.send_notification.assert_called_once_with(
            'Stranger wasn\'t found: {0}',
            error,
            )

    @patch('randtalkbot.admin_handler.StrangerHandler.handle_command')
    @asyncio.coroutine
    def test_handle_command__other_command(self, handle_command):
        from randtalkbot.admin_handler import StrangerHandler
        message = Mock()
        message.command = 'foo_command'
        message.command_args = 'foo_args'
        yield from self.admin_handler.handle_command(message)
        handle_command.assert_called_once_with(message)
