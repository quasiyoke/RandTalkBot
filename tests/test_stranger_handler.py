# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import asynctest
import datetime
from asynctest.mock import call, create_autospec, patch, Mock, CoroutineMock
from randtalkbot.errors import MissingCommandError, StrangerError, UnknownCommandError
from randtalkbot.message import Message, UnsupportedContentError
from randtalkbot.stranger_handler import StrangerHandler
from randtalkbot.stranger_sender_service import StrangerSenderService
from randtalkbot.stranger_service import StrangerServiceError
from randtalkbot.stranger_setup_wizard import StrangerSetupWizard
from telepot import TelegramError

class TestStrangerHandler(asynctest.TestCase):
    @patch('randtalkbot.stranger_handler.StrangerSetupWizard', create_autospec(StrangerSetupWizard))
    @patch('randtalkbot.stranger_sender_service.StrangerSenderService._instance')
    def setUp(self, stranger_sender_service):
        from randtalkbot.stranger_handler import Message
        from randtalkbot.stranger_handler import StrangerSetupWizard
        self.stranger = CoroutineMock()
        self.stranger_service = Mock()
        self.stranger_service.get_or_create_stranger.return_value = self.stranger
        StrangerSetupWizard.reset_mock()
        self.StrangerSetupWizard = StrangerSetupWizard
        self.stranger_setup_wizard = StrangerSetupWizard.return_value
        self.stranger_setup_wizard.handle = CoroutineMock()
        self.stranger_setup_wizard.handle_command = CoroutineMock()
        self.initial_msg = {
            'from': {
                'id': 31416,
                },
            }
        self.sender = stranger_sender_service.get_or_create_stranger_sender.return_value
        self.stranger_handler = StrangerHandler(
            (Mock(), self.initial_msg, 31416),
            self.stranger_service,
            )
        self.stranger_sender_service = stranger_sender_service
        self.message_cls = Message

    @asynctest.ignore_loop
    def test_init__ok(self):
        self.assertEqual(self.stranger_handler._from_id, 31416)
        self.assertEqual(self.stranger_handler._stranger, self.stranger)
        self.assertEqual(self.stranger_handler._stranger_service, self.stranger_service)
        self.assertEqual(self.stranger_handler._stranger_setup_wizard, self.stranger_setup_wizard)
        self.stranger_service.get_or_create_stranger.assert_called_once_with(31416)
        self.stranger_sender_service.get_or_create_stranger_sender.assert_called_once_with(self.stranger)
        self.StrangerSetupWizard.assert_called_once_with(self.stranger)

    @patch('randtalkbot.stranger_handler.LOGGER', Mock())
    @asynctest.ignore_loop
    def test_init__stranger_service_error(self):
        self.stranger_service.reset_mock()
        self.stranger_service.get_or_create_stranger.side_effect = StrangerServiceError()
        with self.assertRaises(SystemExit):
            self.stranger_handler = StrangerHandler(
                (Mock(), self.initial_msg, 31416),
                self.stranger_service,
                )
        self.assertEqual(self.stranger_handler._from_id, 31416)
        self.assertEqual(self.stranger_handler._stranger, self.stranger)
        self.assertEqual(self.stranger_handler._stranger_service, self.stranger_service)
        self.assertEqual(self.stranger_handler._stranger_setup_wizard, self.stranger_setup_wizard)
        self.stranger_service.get_or_create_stranger.assert_called_once_with(31416)
        self.stranger_sender_service.get_or_create_stranger_sender.assert_called_once_with(self.stranger)
        self.StrangerSetupWizard.assert_called_once_with(self.stranger)

    @patch('randtalkbot.stranger_handler.datetime', Mock())
    @asyncio.coroutine
    def test_handle_command_begin(self):
        from randtalkbot.stranger_handler import datetime as datetime_mock
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(1970, 1, 1)
        partner = CoroutineMock()
        partner.looking_for_partner_from = datetime.datetime(1970, 1, 1)
        self.stranger_service.get_partner.return_value = partner
        message = Mock()
        message.command = 'begin'
        yield from self.stranger_handler.handle_command(message)
        self.stranger.prevent_advertising.assert_called_once_with()
        self.stranger_service.get_partner.assert_called_once_with(self.stranger)
        self.stranger.notify_partner_found.assert_called_once_with(partner)
        partner.set_partner.assert_called_once_with(self.stranger)
        self.stranger.set_partner.assert_called_once_with(partner)
        partner.notify_partner_found.assert_called_once_with(self.stranger)

    @patch('randtalkbot.stranger_handler.LOGGER', Mock())
    @asyncio.coroutine
    def test_handle_command_begin__stranger_has_blocked_the_bot(self):
        partner = CoroutineMock()
        self.stranger_service.get_partner.return_value = partner
        self.stranger.notify_partner_found.side_effect = StrangerError()
        message = Mock()
        message.command = 'begin'
        yield from self.stranger_handler.handle_command(message)
        self.stranger_service.get_partner.assert_called_once_with(self.stranger)
        self.stranger.notify_partner_found.assert_called_once_with(partner)
        partner.set_partner.assert_not_called()
        self.stranger.set_partner.assert_not_called()
        partner.notify_partner_found.assert_called_once_with(self.stranger)

    @patch('randtalkbot.stranger_handler.datetime', Mock())
    @asyncio.coroutine
    def test_handle_command_begin__first_partner_has_blocked_the_bot(self):
        from randtalkbot.stranger_handler import datetime as datetime_mock
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(1970, 1, 1)
        partner = CoroutineMock()
        partner.looking_for_partner_from = datetime.datetime(1970, 1, 1)
        self.stranger_service.get_partner.return_value = partner
        partner.notify_partner_found.side_effect = [StrangerError(), None]
        message = Mock()
        message.command = 'begin'
        yield from self.stranger_handler.handle_command(message)
        self.assertEqual(
            self.stranger_service.get_partner.call_args_list,
            [
                call(self.stranger),
                call(self.stranger),
                ],
            )
        self.assertEqual(
            partner.notify_partner_found.call_args_list,
            [
                call(self.stranger),
                call(self.stranger),
                ],
            )
        self.stranger.notify_partner_found.assert_called_once_with(partner)

    def test_handle_command_begin__partner_obtaining_error(self):
        from randtalkbot.stranger_service import PartnerObtainingError
        partner = CoroutineMock()
        self.stranger_service.get_partner.side_effect = PartnerObtainingError()
        message = Mock()
        message.command = 'begin'
        yield from self.stranger_handler.handle_command(message)
        self.stranger_service.get_partner.assert_called_once_with(self.stranger)
        self.stranger.advertise_later.assert_called_once_with()
        self.stranger.set_looking_for_partner.assert_called_once_with()

    @patch('randtalkbot.stranger_handler.LOGGER', Mock())
    @asyncio.coroutine
    def test_handle_command_begin__stranger_service_error(self):
        from randtalkbot.stranger_handler import LOGGER
        from randtalkbot.stranger_service import StrangerServiceError
        partner = CoroutineMock()
        self.stranger_service.get_partner.side_effect = StrangerServiceError()
        self.stranger.id = 31416
        message = Mock()
        message.command = 'begin'
        yield from self.stranger_handler.handle_command(message)
        LOGGER.error.assert_called_once_with(
            'Problems with handling /begin command for %d: %s',
            31416,
            '',
            )
        self.sender.send_notification.assert_called_once_with(
            'Internal error. Admins are already notified about that.',
            )

    @patch('randtalkbot.stranger_handler.LOGGER', Mock())
    @asyncio.coroutine
    def test_handle_command_begin__telegram_error(self):
        from randtalkbot.stranger_handler import LOGGER
        from randtalkbot.stranger_service import StrangerServiceError
        partner = CoroutineMock()
        self.stranger_service.get_partner.side_effect = StrangerServiceError()
        self.stranger.id = 31416
        message = Mock()
        message.command = 'begin'
        self.sender.send_notification.side_effect = TelegramError('', 0)
        yield from self.stranger_handler.handle_command(message)
        LOGGER.error.assert_called_once_with(
            'Problems with handling /begin command for %d: %s',
            31416,
            '',
            )
        self.assertTrue(LOGGER.warning.called)

    def test_handle_command__end(self):
        message = Mock()
        message.command = 'end'
        yield from self.stranger_handler.handle_command(message)
        self.stranger.prevent_advertising.assert_called_once_with()
        self.stranger.end_chatting.assert_called_once_with()

    @patch('randtalkbot.stranger_handler.__version__', '0.0.0')
    @asyncio.coroutine
    def test_handle_command_help(self):
        message = Mock()
        message.command = 'help'
        yield from self.stranger_handler.handle_command(message)
        self.sender.send_notification.assert_called_once_with(
            '*Help*\n\nUse /begin to start looking for a conversational partner, once you\'re matched '
                'you can use /end to finish the conversation. To choose your settings, apply /setup.\n\n'
                'If you have any suggestions or require help, please contact @quasiyoke. '
                'When asking questions, please provide this number: {0}.\n\n'
                'Subscribe to [our news](https://telegram.me/RandTalkChannel). '
                'You\'re welcome to inspect and improve [Rand Talk v. {1} source code]'
                '(https://github.com/quasiyoke/RandTalkBot) or to [give us 5 stars]'
                '(https://telegram.me/storebot?start=randtalkbot).',
            31416,
            '0.0.0',
            )

    @patch('randtalkbot.stranger_handler.LOGGER', Mock())
    @asyncio.coroutine
    def test_handle_command_help__telegram_error(self):
        from randtalkbot.stranger_handler import LOGGER
        message = Mock()
        message.command = 'help'
        self.sender.send_notification.side_effect = TelegramError('', 0)
        yield from self.stranger_handler.handle_command(message)
        self.assertTrue(LOGGER.warning.called)

    def test_handle_command_mute_bonuses(self):
        message = Mock()
        message.command = 'mute_bonuses'
        yield from self.stranger_handler.handle_command(message)
        self.stranger.mute_bonuses_notifications.assert_called_once_with()
        self.sender.send_notification.assert_called_once_with(
            'Notifications about bonuses were muted for 1 hour',
            )

    @patch('randtalkbot.stranger_handler.LOGGER', Mock())
    @asyncio.coroutine
    def test_handle_command_mute_bonuses__telegram_error(self):
        from randtalkbot.stranger_handler import LOGGER
        message = Mock()
        message.command = 'mute_bonuses'
        self.sender.send_notification.side_effect = TelegramError('', 0)
        yield from self.stranger_handler.handle_command(message)
        self.assertTrue(LOGGER.warning.called)

    def test_handle_command__setup(self):
        message = Mock()
        message.command = 'setup'
        yield from self.stranger_handler.handle_command(message)
        self.stranger.prevent_advertising.assert_called_once_with()
        self.stranger_setup_wizard.activate.assert_called_once_with()

    def test_handle_command__start_has_invitation(self):
        message = Mock()
        message.command = 'start'
        message.command_args = 'foo_args'
        message.decode_command_args.return_value = {'i': 'foo_invitation'}
        invited_by = CoroutineMock()
        self.stranger_service.get_stranger_by_invitation.return_value = invited_by
        self.stranger.wizard = 'none'
        self.stranger.invited_by = None
        yield from self.stranger_handler.handle_command(message)
        self.stranger_service.get_stranger_by_invitation.assert_called_once_with('foo_invitation')
        self.assertEqual(self.stranger.invited_by, invited_by)
        self.stranger.save.assert_called_once_with()
        self.sender.send_notification.assert_called_once_with(
            '*Manual*\n\nUse /begin to start looking for a conversational partner, once '
                'you\'re matched you can use /end to end the conversation.'
            )

    def test_handle_command__start_has_invitation_and_already_invited_by(self):
        message = Mock()
        message.command = 'start'
        message.command_args = 'foo_args'
        message.decode_command_args.return_value = {'i': 'foo_invitation'}
        new_invited_by = CoroutineMock()
        self.stranger_service.get_stranger_by_invitation.return_value = new_invited_by
        self.stranger.wizard = 'none'
        invited_by = CoroutineMock()
        self.stranger.invited_by = invited_by
        yield from self.stranger_handler.handle_command(message)
        self.stranger_service.get_stranger_by_invitation.assert_not_called()
        self.assertEqual(self.stranger.invited_by, invited_by)
        self.sender.send_notification.assert_called_once_with(
            '*Manual*\n\nUse /begin to start looking for a conversational partner, once '
                'you\'re matched you can use /end to end the conversation.'
            )

    def test_handle_command__start_has_invited_himself(self):
        message = Mock()
        message.command = 'start'
        message.command_args = 'foo_args'
        message.decode_command_args.return_value = {'i': 'foo_invitation'}
        self.stranger.wizard = 'none'
        self.stranger.invited_by = None
        self.stranger.invitation = 'foo_invitation'
        yield from self.stranger_handler.handle_command(message)
        self.stranger_service.get_stranger_by_invitation.assert_not_called()
        self.assertEqual(self.stranger.invited_by, None)
        self.assertEqual(
            self.sender.send_notification.call_args_list,
            [
                call('Don\'t try to fool me. Forward message with the link to your friends and '
                    'receive well-earned bonuses that will help you to find partner quickly.'),
                call('*Manual*\n\nUse /begin to start looking for a conversational partner, once '
                    'you\'re matched you can use /end to end the conversation.'),
                ],
            )

    def test_handle_command__start_has_invalid_invitation(self):
        message = Mock()
        message.command = 'start'
        message.command_args = 'foo_args'
        message.decode_command_args.side_effect = UnsupportedContentError()
        self.stranger.wizard = 'none'
        self.stranger.invited_by = None
        yield from self.stranger_handler.handle_command(message)
        self.stranger_service.get_stranger_by_invitation.assert_not_called()
        self.assertEqual(self.stranger.invited_by, None)
        self.sender.send_notification.assert_called_once_with(
            '*Manual*\n\nUse /begin to start looking for a conversational partner, once '
                'you\'re matched you can use /end to end the conversation.'
            )

    def test_handle_command__start_has_invalid_invitation_json_keys(self):
        message = Mock()
        message.command = 'start'
        message.command_args = 'foo_args'
        message.decode_command_args.return_value = {'foo': 'bar'}
        self.stranger.wizard = 'none'
        self.stranger.invited_by = None
        yield from self.stranger_handler.handle_command(message)
        self.stranger_service.get_stranger_by_invitation.assert_not_called()
        self.assertEqual(self.stranger.invited_by, None)
        self.sender.send_notification.assert_called_once_with(
            '*Manual*\n\nUse /begin to start looking for a conversational partner, once '
                'you\'re matched you can use /end to end the conversation.'
            )

    def test_handle_command__start_has_invalid_invitation_json_type(self):
        message = Mock()
        message.command = 'start'
        message.command_args = 'foo_args'
        message.decode_command_args.return_value = [1, 2, 3]
        self.stranger.wizard = 'none'
        self.stranger.invited_by = None
        yield from self.stranger_handler.handle_command(message)
        self.stranger_service.get_stranger_by_invitation.assert_not_called()
        self.assertEqual(self.stranger.invited_by, None)
        self.sender.send_notification.assert_called_once_with(
            '*Manual*\n\nUse /begin to start looking for a conversational partner, once '
                'you\'re matched you can use /end to end the conversation.'
            )

    def test_handle_command__start_has_invalid_invitation_stranger_service_error(self):
        message = Mock()
        message.command = 'start'
        message.command_args = 'foo_args'
        message.decode_command_args.return_value = {'i': 'foo_invitation'}
        self.stranger_service.get_stranger_by_invitation.side_effect = StrangerServiceError()
        self.stranger.wizard = 'none'
        self.stranger.invited_by = None
        yield from self.stranger_handler.handle_command(message)
        self.stranger_service.get_stranger_by_invitation.assert_called_once_with('foo_invitation')
        self.assertEqual(self.stranger.invited_by, None)
        self.sender.send_notification.assert_called_once_with(
            '*Manual*\n\nUse /begin to start looking for a conversational partner, once '
                'you\'re matched you can use /end to end the conversation.'
            )

    def test_handle_command__start_no_invitation(self):
        message = Mock()
        message.command = 'start'
        message.command_args = ''
        self.stranger.wizard = 'none'
        self.stranger.invited_by = None
        yield from self.stranger_handler.handle_command(message)
        self.assertEqual(self.stranger.invited_by, None)
        self.sender.send_notification.assert_called_once_with(
            '*Manual*\n\nUse /begin to start looking for a conversational partner, once '
                'you\'re matched you can use /end to end the conversation.'
            )

    def test_handle_command__start_no_invitation_is_in_setup(self):
        message = Mock()
        message.command = 'start'
        message.command_args = ''
        self.stranger.wizard = 'setup'
        self.stranger.invited_by = None
        yield from self.stranger_handler.handle_command(message)
        self.assertEqual(self.stranger.invited_by, None)
        self.sender.send_notification.assert_not_called()

    def test_handle_command__unknown_command(self):
        message = Mock()
        message.command = 'foo_command'
        with self.assertRaises(UnknownCommandError):
            yield from self.stranger_handler.handle_command(message)

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @asyncio.coroutine
    def test_on_chat_message__not_private(self):
        from randtalkbot.stranger_handler import telepot
        telepot.glance.return_value = 'text', 'not_private', 31416
        yield from self.stranger_handler.on_chat_message('message')
        self.stranger.send_to_partner.assert_not_called()
        self.assertFalse(self.stranger_setup_wizard.handle.called)

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.Message', create_autospec(Message))
    @patch('randtalkbot.stranger_handler.StrangerHandler.handle_command')
    @asyncio.coroutine
    def test_on_chat_message__text(self, handle_command_mock):
        from randtalkbot.stranger_handler import Message
        from randtalkbot.stranger_handler import telepot
        telepot.glance.return_value = 'text', 'private', 31416
        self.stranger_setup_wizard.handle.return_value = False
        message_json = {
            'text': 'message_text'
            }
        message = Message.return_value
        message.command = None
        yield from self.stranger_handler.on_chat_message(message_json)
        self.stranger.send_to_partner.assert_called_once_with(Message.return_value)
        self.stranger_setup_wizard.handle.assert_called_once_with(message)
        Message.assert_called_once_with(message_json)
        handle_command_mock.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.Message', create_autospec(Message))
    @patch('randtalkbot.stranger_handler.StrangerHandler.handle_command')
    @asyncio.coroutine
    def test_on_chat_message__text_no_partner(self, handle_command_mock):
        from randtalkbot.stranger_handler import Message
        from randtalkbot.stranger_handler import telepot
        from randtalkbot.errors import MissingPartnerError
        telepot.glance.return_value = 'text', 'private', 31416
        self.stranger_setup_wizard.handle.return_value = False
        message_json = {
            'text': 'message_text',
            }
        self.stranger.send_to_partner = CoroutineMock(side_effect=MissingPartnerError())
        message = Message.return_value
        message.command = None
        yield from self.stranger_handler.on_chat_message(message_json)
        self.stranger.send_to_partner.assert_called_once_with(message)
        self.stranger_setup_wizard.handle.assert_called_once_with(message)
        Message.assert_called_once_with(message_json)
        handle_command_mock.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.Message', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler.handle_command')
    @asyncio.coroutine
    def test_on_chat_message__text_stranger_error(self, handle_command_mock):
        from randtalkbot.stranger_handler import Message
        from randtalkbot.stranger_handler import telepot
        from randtalkbot.stranger_handler import StrangerError
        telepot.glance.return_value = 'text', 'private', 31416
        self.stranger_setup_wizard.handle.return_value = False
        message_json = {
            'text': 'message_text',
            }
        Message.return_value.command = None
        self.stranger.send_to_partner = CoroutineMock(side_effect=StrangerError())
        yield from self.stranger_handler.on_chat_message(message_json)
        self.stranger.send_to_partner.assert_called_once_with(Message.return_value)
        self.sender.send_notification.assert_called_once_with(
            'Messages of this type aren\'t supported.',
            )
        Message.assert_called_once_with(message_json)
        handle_command_mock.assert_not_called()

    @patch('randtalkbot.stranger_handler.LOGGER', Mock())
    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.Message', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler.handle_command')
    @asyncio.coroutine
    def test_on_chat_message__text_stranger_has_blocked_the_bot(self, handle_command_mock):
        from randtalkbot.stranger_handler import LOGGER
        from randtalkbot.stranger_handler import Message
        from randtalkbot.stranger_handler import telepot
        from randtalkbot.stranger_handler import StrangerError
        telepot.glance.return_value = 'text', 'private', 31416
        self.stranger_setup_wizard.handle.return_value = False
        message_json = {
            'text': 'message_text',
            }
        Message.return_value.command = None
        self.stranger.id = 31416
        self.stranger.partner.id = 27183
        self.stranger.send_to_partner = CoroutineMock(side_effect=TelegramError('foo_description', 123))
        yield from self.stranger_handler.on_chat_message(message_json)
        LOGGER.warning(
            'Send text. Can\'t send to partned: %d -> %d',
            31416,
            27183
            )
        self.sender.send_notification.assert_called_once_with(
            'Your partner has blocked me! How did you do that?!',
            )

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler.handle_command')
    @patch('randtalkbot.stranger_handler.Message', create_autospec(Message))
    @asyncio.coroutine
    def test_on_chat_message__command(self, handle_command_mock):
        from randtalkbot.stranger_handler import Message
        from randtalkbot.stranger_handler import telepot
        telepot.glance.return_value = 'text', 'private', 31416
        message_json = {
            'text': 'some_command_text'
            }
        message = Mock()
        message.command = 'foo_command'
        Message.return_value = message
        self.stranger_setup_wizard.handle_command.return_value = False
        yield from self.stranger_handler.on_chat_message(message_json)
        self.stranger.send_to_partner.assert_not_called()
        Message.assert_called_once_with(message_json)
        self.stranger_setup_wizard.handle_command.assert_called_once_with(message)
        handle_command_mock.assert_called_once_with(message)

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler.handle_command')
    @patch('randtalkbot.stranger_handler.Message', create_autospec(Message))
    @asyncio.coroutine
    def test_on_chat_message__command_setup(self, handle_command_mock):
        from randtalkbot.stranger_handler import Message
        from randtalkbot.stranger_handler import telepot
        telepot.glance.return_value = 'text', 'private', 31416
        message_json = {
            'text': 'some_command_text'
            }
        message = Mock()
        message.command = 'foo_command'
        Message.return_value = message
        self.stranger_setup_wizard.handle_command.return_value = True
        yield from self.stranger_handler.on_chat_message(message_json)
        self.stranger.send_to_partner.assert_not_called()
        Message.assert_called_once_with(message_json)
        handle_command_mock.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.Message', create_autospec(Message))
    @patch('randtalkbot.stranger_handler.StrangerHandler.handle_command')
    @asyncio.coroutine
    def test_on_chat_message__command_unknown(self, handle_command_mock):
        from randtalkbot.stranger_handler import Message
        from randtalkbot.stranger_handler import telepot
        telepot.glance.return_value = 'text', 'private', 31416
        self.stranger_setup_wizard.handle.return_value = False
        message_json = {
            'text': 'message_text',
            }
        message = Message.return_value
        message.command = 'foo_command'
        handle_command_mock.side_effect = UnknownCommandError('foo_command')
        self.stranger_setup_wizard.handle_command.return_value = False
        yield from self.stranger_handler.on_chat_message(message_json)
        self.sender.send_notification.assert_called_once_with(
            'Unknown command. Look /help for the full list of commands.',
            )

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.Message', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler.handle_command')
    @asyncio.coroutine
    def test_on_chat_message__not_supported_by_stranger_content(self, handle_command_mock):
        from randtalkbot.stranger_handler import Message
        from randtalkbot.stranger_handler import telepot
        from randtalkbot.stranger_handler import StrangerError
        telepot.glance.return_value = 'unsupported_content', 'private', 31416
        message_json = Mock()
        message = Message.return_value
        message.command = None
        self.stranger.send_to_partner = CoroutineMock(side_effect=StrangerError())
        self.stranger_setup_wizard.handle.return_value = False
        yield from self.stranger_handler.on_chat_message(message_json)
        self.stranger.send_to_partner.assert_called_once_with(message)
        self.sender.send_notification.assert_called_once_with(
            'Messages of this type aren\'t supported.',
            )
        Message.assert_called_once_with(message_json)
        handle_command_mock.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.Message', Mock(side_effect=UnsupportedContentError))
    @patch('randtalkbot.stranger_handler.StrangerHandler.handle_command')
    @asyncio.coroutine
    def test_on_chat_message__not_supported_by_message_cls_content(self, handle_command_mock):
        from randtalkbot.stranger_handler import Message
        from randtalkbot.stranger_handler import telepot
        from randtalkbot.stranger_handler import StrangerError
        telepot.glance.return_value = 'unsupported_content', 'private', 31416
        message_json = Mock()
        message = Message.return_value
        message.command = None
        self.stranger.send_to_partner = CoroutineMock()
        self.stranger_setup_wizard.handle.return_value = False
        yield from self.stranger_handler.on_chat_message(message_json)
        self.stranger.send_to_partner.assert_not_called()
        self.sender.send_notification.assert_called_once_with(
            'Messages of this type aren\'t supported.',
            )
        Message.assert_called_once_with(message_json)
        handle_command_mock.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.Message', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler.handle_command')
    @asyncio.coroutine
    def test_on_chat_message__setup(self, handle_command_mock):
        from randtalkbot.stranger_handler import Message
        from randtalkbot.stranger_handler import telepot
        telepot.glance.return_value = 'text', 'private', 31416
        # This means, message was handled by StrangerSetupWizard.
        self.stranger_setup_wizard.handle.return_value = True
        message_json = {
            'text': 'message_text',
            }
        message = Message.return_value
        message.command = None
        self.stranger_setup_wizard.handle.return_value = True
        yield from self.stranger_handler.on_chat_message(message_json)
        self.stranger_setup_wizard.handle.assert_called_once_with(message)
        Message.assert_called_once_with(message_json)
        handle_command_mock.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @asyncio.coroutine
    def test_on_inline_query(self):
        from randtalkbot.stranger_handler import telepot
        telepot.glance.return_value = 31416, 27183, 'foo_query_string'
        message_json = 'foo_message'
        self.stranger.get_invitation_link = Mock()
        yield from self.stranger_handler.on_inline_query(message_json)
        self.sender.answer_inline_query.assert_called_once_with(
            31416,
            [{
                'type': 'article',
                'id': 'invitation_link',
                'title': 'Rand Talk Invitation Link',
                'description': 'The more friends\'ll use your link -- the faster the search will be',
                'thumb_url': 'http://randtalk.ml/static/img/logo-500x500.png',
                'message_text': (
                    'Do you want to talk with somebody, practice in foreign languages or you just want '
                        'to have some fun? Rand Talk will help you! It\'s a bot matching you with '
                        'a random stranger of desired sex speaking on your language. {0}',
                    self.stranger.get_invitation_link.return_value,
                    ),
                'parse_mode': 'Markdown',
                }],
            )
