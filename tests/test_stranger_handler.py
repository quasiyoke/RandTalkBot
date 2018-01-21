# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
from unittest.mock import create_autospec
from asynctest.mock import call, patch, Mock, CoroutineMock
import asynctest
from telepot.exception import TelegramError
from randtalkbot.errors import StrangerError, StrangerServiceError, UnknownCommandError, \
    UnsupportedContentError
from randtalkbot.message import Message
from randtalkbot.stranger_handler import StrangerHandler


class TestStrangerHandler(asynctest.TestCase):
    @patch('randtalkbot.stranger_handler.StrangerSetupWizard')
    @patch('randtalkbot.stranger_sender_service.StrangerSenderService._instance')
    @patch('randtalkbot.stranger_handler.StrangerService', Mock())
    def setUp(self, stranger_sender_service, stranger_setup_wizard_cls_mock):
        from randtalkbot.stranger_handler import StrangerService as stranger_service_mock
        self.stranger = CoroutineMock()
        self.stranger.id = 31
        stranger_service = stranger_service_mock.get_instance.return_value
        stranger_service.get_or_create_stranger.return_value = self.stranger
        stranger_setup_wizard_cls_mock.reset_mock()
        self.StrangerSetupWizard = stranger_setup_wizard_cls_mock
        self.stranger_setup_wizard = stranger_setup_wizard_cls_mock.return_value
        self.stranger_setup_wizard.activate = CoroutineMock()
        self.stranger_setup_wizard.handle = CoroutineMock()
        self.stranger_setup_wizard.handle_command = CoroutineMock()
        self.initial_msg = {
            'from': {
                'id': 31416,
                },
            }
        self.sender = stranger_sender_service.get_or_create_stranger_sender.return_value
        self.sender.answer_inline_query = CoroutineMock()
        self.sender.send_notification = CoroutineMock()
        self.stranger_handler = StrangerHandler(
            (Mock(), self.initial_msg, 31416),
            event_space=None,
            timeout=1,
            )
        self.stranger_sender_service = stranger_sender_service
        self.message_cls = Message

    @patch('randtalkbot.stranger_handler.LOGGER', Mock())
    @patch('randtalkbot.stranger_handler.StrangerService', Mock())
    @patch('randtalkbot.stranger_handler.StrangerSetupWizard')
    @asynctest.ignore_loop
    def test_init__ok(self, stranger_setup_wizard_cls_mock):
        from randtalkbot.stranger_handler import StrangerService
        stranger_setup_wizard = stranger_setup_wizard_cls_mock.return_value
        stranger_service = StrangerService.get_instance.return_value
        stranger_service.get_or_create_stranger.return_value = self.stranger
        self.stranger_handler = StrangerHandler(
            (Mock(), self.initial_msg, 31416),
            event_space=None,
            timeout=1,
            )
        self.assertEqual(self.stranger_handler._from_id, 31416)
        self.assertEqual(self.stranger_handler._stranger, self.stranger)
        self.assertEqual(self.stranger_handler._stranger_setup_wizard, stranger_setup_wizard)
        stranger_service.get_or_create_stranger.assert_called_once_with(31416)
        self.stranger_sender_service.get_or_create_stranger_sender \
            .assert_called_once_with(self.stranger)
        self.StrangerSetupWizard.assert_called_once_with(self.stranger)

    @patch('randtalkbot.stranger_handler.LOGGER', Mock())
    @patch('randtalkbot.stranger_handler.StrangerService', Mock())
    @asynctest.ignore_loop
    def test_init__stranger_service_error(self):
        from randtalkbot.stranger_handler import StrangerService
        stranger_service = StrangerService.get_instance.return_value
        stranger_service.get_or_create_stranger.side_effect = StrangerServiceError()
        with self.assertRaises(SystemExit):
            self.stranger_handler = StrangerHandler(
                (Mock(), self.initial_msg, 31416),
                event_space=None,
                timeout=1,
                )
        self.assertEqual(self.stranger_handler._from_id, 31416)
        self.assertEqual(self.stranger_handler._stranger, self.stranger)
        self.assertEqual(self.stranger_handler._stranger_setup_wizard, self.stranger_setup_wizard)
        stranger_service.get_or_create_stranger.assert_called_once_with(31416)
        self.stranger_sender_service.get_or_create_stranger_sender \
            .assert_called_once_with(self.stranger)
        self.StrangerSetupWizard.assert_called_once_with(self.stranger)

    async def test_handle_command__ok(self):
        message = Mock()
        message.command = 'foo_command'
        self.stranger_handler._handle_command_foo_command = CoroutineMock()
        await self.stranger_handler.handle_command(message)
        self.stranger_handler._handle_command_foo_command.assert_called_once_with(message)

    async def test_handle_command__unknown_command(self):
        message = Mock()
        message.command = 'foo_command'
        with self.assertRaises(UnknownCommandError):
            await self.stranger_handler.handle_command(message)

    @patch('randtalkbot.stranger_handler.StrangerService', Mock())
    async def test_handle_command_begin__partner_obtaining_error(self):
        from randtalkbot.stranger_service import PartnerObtainingError
        from randtalkbot.stranger_handler import StrangerService
        stranger_service = StrangerService.get_instance.return_value
        stranger_service.match_partner.side_effect = PartnerObtainingError()
        message = Mock()
        await self.stranger_handler._handle_command_begin(message)
        self.stranger.advertise_later.assert_called_once_with()
        self.stranger.set_looking_for_partner.assert_called_once_with()

    @patch('randtalkbot.stranger_handler.StrangerService', Mock())
    @patch('randtalkbot.stranger_handler.LOGGER', Mock())
    async def test_handle_command_begin__stranger_service_error(self):
        from randtalkbot.stranger_handler import LOGGER as logger_mock
        from randtalkbot.stranger_handler import StrangerService as stranger_service_mock
        stranger_service = stranger_service_mock.get_instance.return_value
        error = StrangerServiceError()
        stranger_service.match_partner = CoroutineMock(side_effect=error)
        self.stranger.id = 31416
        self.stranger_handler._get_sender = Mock(return_value=self.sender)
        self.stranger_handler._get_stranger = Mock(return_value=self.stranger)
        message = Mock()
        await self.stranger_handler._handle_command_begin(message)
        logger_mock.warning.assert_called_once_with(
            'Can\'t set partner for %d. %s',
            31,
            error,
            )
        self.assertTrue(LOGGER.warning.called)

    async def test_handle_command__end(self):
        message = Mock()
        partner = Mock()
        self.stranger.get_partner = Mock(return_value=partner)
        await self.stranger_handler._handle_command_end(message)
        self.stranger.prevent_advertising.assert_called_once_with()
        self.stranger.end_talk.assert_called_once_with()

    @patch('randtalkbot.stranger_handler.__version__', '0.0.0')
    async def test_handle_command_help(self):
        message = Mock()
        await self.stranger_handler._handle_command_help(message)
        self.sender.send_notification.assert_called_once_with(
            '*Help*\n\nUse /begin to start looking for a conversational partner, once you\'re'
            ' matched you can use /end to finish the conversation. To choose your settings, apply'
            ' /setup.\n\n'
            'If you have any suggestions or require help, please contact @quasiyoke.'
            ' When asking questions, please provide this number: {0}.\n\n'
            'Subscribe to [our news](https://telegram.me/RandTalk).'
            ' You\'re welcome to inspect and improve [Rand Talk v. {1} source code]'
            '(https://github.com/quasiyoke/RandTalkBot) or to [give us 5 stars]'
            '(https://telegram.me/storebot?start=randtalkbot).',
            31416,
            '0.0.0',
            disable_web_page_preview=True,
            )

    @patch('randtalkbot.stranger_handler.LOGGER', Mock())
    async def test_handle_command_help__telegram_error(self):
        from randtalkbot.stranger_handler import LOGGER
        message = Mock()
        self.sender.send_notification.side_effect = TelegramError({}, '', 0)
        await self.stranger_handler._handle_command_help(message)
        self.assertTrue(LOGGER.warning.called)

    async def test_handle_command_mute_bonuses(self):
        message = Mock()
        await self.stranger_handler._handle_command_mute_bonuses(message)
        self.stranger.mute_bonuses_notifications.assert_called_once_with()
        self.sender.send_notification.assert_called_once_with(
            'Notifications about bonuses were muted for 1 hour',
            )

    @patch('randtalkbot.stranger_handler.LOGGER', Mock())
    async def test_handle_command_mute_bonuses__telegram_error(self):
        from randtalkbot.stranger_handler import LOGGER
        message = Mock()
        self.sender.send_notification.side_effect = TelegramError({}, '', 0)
        await self.stranger_handler._handle_command_mute_bonuses(message)
        self.assertTrue(LOGGER.warning.called)

    async def test_handle_command__setup(self):
        message = Mock()
        await self.stranger_handler._handle_command_setup(message)
        self.stranger.prevent_advertising.assert_called_once_with()
        self.stranger_setup_wizard.activate.assert_called_once_with()

    async def test_handle_command__start_no_invitation(self):
        message = Mock()
        message.command_args = ''
        self.stranger.wizard = 'none'
        self.stranger.invited_by = None
        await self.stranger_handler._handle_command_start(message)
        self.assertEqual(self.stranger.invited_by, None)
        self.sender.send_notification.assert_called_once_with(
            '*Manual*\n\nUse /begin to start looking for a conversational partner, once'
            ' you\'re matched you can use /end to end the conversation.'
            )

    async def test_handle_command__start_no_invitation_is_in_setup(self):
        message = Mock()
        message.command_args = ''
        self.stranger.wizard = 'setup'
        self.stranger.invited_by = None
        await self.stranger_handler._handle_command_start(message)
        self.assertEqual(self.stranger.invited_by, None)
        self.sender.send_notification.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    async def test_on_chat_message__not_private(self):
        from randtalkbot.stranger_handler import telepot
        telepot.glance.return_value = 'text', 'not_private', 31416
        await self.stranger_handler.on_chat_message('message')
        self.stranger.send_to_partner.assert_not_called()
        self.assertFalse(self.stranger_setup_wizard.handle.called)

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.Message', create_autospec(Message))
    @patch('randtalkbot.stranger_handler.StrangerHandler.handle_command')
    async def test_on_chat_message__text(self, handle_command_mock):
        from randtalkbot.stranger_handler import Message as message_cls_mock
        from randtalkbot.stranger_handler import telepot
        telepot.glance.return_value = 'text', 'private', 31416
        self.stranger_setup_wizard.handle.return_value = False
        message_json = {
            'text': 'message_text'
            }
        message = message_cls_mock.return_value
        message.command = None
        await self.stranger_handler.on_chat_message(message_json)
        self.stranger.send_to_partner.assert_called_once_with(message_cls_mock.return_value)
        self.stranger_setup_wizard.handle.assert_called_once_with(message)
        message_cls_mock.assert_called_once_with(message_json)
        handle_command_mock.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.Message', create_autospec(Message))
    @patch('randtalkbot.stranger_handler.StrangerHandler.handle_command')
    async def test_on_chat_message__text_no_partner(self, handle_command_mock):
        from randtalkbot.stranger_handler import Message as message_cls_mock
        from randtalkbot.stranger_handler import telepot
        from randtalkbot.errors import MissingPartnerError
        telepot.glance.return_value = 'text', 'private', 31416
        self.stranger_setup_wizard.handle.return_value = False
        message_json = {
            'text': 'message_text',
            }
        self.stranger.send_to_partner = CoroutineMock(side_effect=MissingPartnerError())
        message = message_cls_mock.return_value
        message.command = None
        await self.stranger_handler.on_chat_message(message_json)
        self.stranger.send_to_partner.assert_called_once_with(message)
        self.stranger_setup_wizard.handle.assert_called_once_with(message)
        message_cls_mock.assert_called_once_with(message_json)
        handle_command_mock.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler.handle_command')
    @patch('randtalkbot.stranger_handler.Message', create_autospec(Message))
    async def test_on_chat_message__command(self, handle_command_mock):
        from randtalkbot.stranger_handler import Message as message_cls_mock
        from randtalkbot.stranger_handler import telepot
        telepot.glance.return_value = 'text', 'private', 31416
        message_json = {
            'text': 'some_command_text'
            }
        message = Mock()
        message.command = 'foo_command'
        message_cls_mock.return_value = message
        self.stranger_setup_wizard.handle_command.return_value = False
        await self.stranger_handler.on_chat_message(message_json)
        self.stranger.send_to_partner.assert_not_called()
        message_cls_mock.assert_called_once_with(message_json)
        self.stranger_setup_wizard.handle_command.assert_called_once_with(message)
        handle_command_mock.assert_called_once_with(message)

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler.handle_command')
    @patch('randtalkbot.stranger_handler.Message', create_autospec(Message))
    async def test_on_chat_message__command_setup(self, handle_command_mock):
        from randtalkbot.stranger_handler import Message as message_cls_mock
        from randtalkbot.stranger_handler import telepot
        telepot.glance.return_value = 'text', 'private', 31416
        message_json = {
            'text': 'some_command_text'
            }
        message = Mock()
        message.command = 'foo_command'
        message_cls_mock.return_value = message
        self.stranger_setup_wizard.handle_command.return_value = True
        await self.stranger_handler.on_chat_message(message_json)
        self.stranger.send_to_partner.assert_not_called()
        message_cls_mock.assert_called_once_with(message_json)
        handle_command_mock.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.Message', create_autospec(Message))
    @patch('randtalkbot.stranger_handler.StrangerHandler.handle_command')
    async def test_on_chat_message__command_unknown(self, handle_command_mock):
        from randtalkbot.stranger_handler import Message as message_cls_mock
        from randtalkbot.stranger_handler import telepot
        telepot.glance.return_value = 'text', 'private', 31416
        self.stranger_setup_wizard.handle.return_value = False
        message_json = {
            'text': 'message_text',
            }
        message = message_cls_mock.return_value
        message.command = 'foo_command'
        handle_command_mock.side_effect = UnknownCommandError('foo_command')
        self.stranger_setup_wizard.handle_command.return_value = False
        await self.stranger_handler.on_chat_message(message_json)
        self.sender.send_notification.assert_called_once_with(
            'Unknown command. Look /help for the full list of commands.',
            )

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.Message', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler.handle_command')
    async def test_on_chat_message__not_supported_by_stranger_content(self, handle_command_mock):
        from randtalkbot.stranger_handler import Message as message_cls_mock
        from randtalkbot.stranger_handler import telepot
        telepot.glance.return_value = 'unsupported_content', 'private', 31416
        message_json = Mock()
        message = message_cls_mock.return_value
        message.command = None
        self.stranger.send_to_partner = CoroutineMock(side_effect=StrangerError())
        self.stranger_setup_wizard.handle.return_value = False
        await self.stranger_handler.on_chat_message(message_json)
        self.stranger.send_to_partner.assert_called_once_with(message)
        self.sender.send_notification.assert_called_once_with(
            'Messages of this type aren\'t supported.',
            )
        message_cls_mock.assert_called_once_with(message_json)
        handle_command_mock.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.Message', Mock(side_effect=UnsupportedContentError))
    @patch('randtalkbot.stranger_handler.StrangerHandler.handle_command')
    async def test_on_chat_message__not_supported_by_message_cls_content(self, handle_command_mock):
        from randtalkbot.stranger_handler import Message as message_cls_mock
        from randtalkbot.stranger_handler import telepot
        telepot.glance.return_value = 'unsupported_content', 'private', 31416
        message_json = Mock()
        message = message_cls_mock.return_value
        message.command = None
        self.stranger.send_to_partner = CoroutineMock()
        self.stranger_setup_wizard.handle.return_value = False
        await self.stranger_handler.on_chat_message(message_json)
        self.stranger.send_to_partner.assert_not_called()
        self.sender.send_notification.assert_called_once_with(
            'Messages of this type aren\'t supported.',
            )
        message_cls_mock.assert_called_once_with(message_json)
        handle_command_mock.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.Message', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler.handle_command')
    async def test_on_chat_message__setup(self, handle_command_mock):
        from randtalkbot.stranger_handler import Message as message_cls_mock
        from randtalkbot.stranger_handler import telepot
        telepot.glance.return_value = 'text', 'private', 31416
        # This means, message was handled by StrangerSetupWizard.
        self.stranger_setup_wizard.handle.return_value = True
        message_json = {
            'text': 'message_text',
            }
        message = message_cls_mock.return_value
        message.command = None
        self.stranger_setup_wizard.handle.return_value = True
        await self.stranger_handler.on_chat_message(message_json)
        self.stranger_setup_wizard.handle.assert_called_once_with(message)
        message_cls_mock.assert_called_once_with(message_json)
        handle_command_mock.assert_not_called()
