# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import asynctest
from randtalkbot.stranger_handler import StrangerHandler, MissingCommandError, UnsupportedContentError
from randtalkbot.stranger_sender_service import StrangerSenderService
from randtalkbot.stranger_service import StrangerServiceError
from randtalkbot.stranger_setup_wizard import StrangerSetupWizard
from asynctest.mock import create_autospec, patch, Mock, CoroutineMock

class TestStrangerHandler(asynctest.TestCase):
    @patch('randtalkbot.stranger_sender_service.StrangerSenderService._instance')
    @patch('randtalkbot.stranger_handler.StrangerSetupWizard', create_autospec(StrangerSetupWizard))
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
                }
            }
        self.sender = stranger_sender_service.get_or_create_stranger_sender.return_value
        self.stranger_handler = StrangerHandler((Mock(), self.initial_msg, 31416), self.stranger_service)
        stranger_sender_service.get_or_create_stranger_sender.assert_called_once_with(31416)
        self.stranger_sender_service = stranger_sender_service

    @asynctest.ignore_loop
    def test_init(self):
        self.assertEqual(self.stranger_handler._chat_id, 31416)
        self.assertEqual(self.stranger_handler._stranger, self.stranger)
        self.assertEqual(self.stranger_handler._stranger_service, self.stranger_service)
        self.assertEqual(self.stranger_handler._stranger_setup_wizard, self.stranger_setup_wizard)
        self.stranger_service.get_or_create_stranger.assert_called_once_with(31416)
        self.stranger_sender_service.get_or_create_stranger_sender.assert_called_once_with(31416)
        self.StrangerSetupWizard.assert_called_once_with(self.stranger)

    @asynctest.ignore_loop
    def test_get_command(self):
        self.assertEqual(StrangerHandler._get_command('/begin chat'), 'begin')
        self.assertEqual(StrangerHandler._get_command('/start'), 'start')
        with self.assertRaises(MissingCommandError):
            StrangerHandler._get_command('/beginnnnnn')

    @asynctest.ignore_loop
    def test_get_content_kwargs__text(self):
        content_kwargs = StrangerHandler._get_content_kwargs(
            {'text': 'foo'},
            'text',
            )
        self.assertEqual(
            content_kwargs,
            {'text': 'foo'},
            )

    @asynctest.ignore_loop
    def test_get_content_kwargs__text_with_reply(self):
        with self.assertRaises(UnsupportedContentError):
            StrangerHandler._get_content_kwargs(
                {
                    'text': 'foo',
                    'reply_to_message': None
                    },
                'text',
                )

    @asynctest.ignore_loop
    def test_get_content_kwargs__invalid_text(self):
        with self.assertRaises(UnsupportedContentError):
            StrangerHandler._get_content_kwargs({}, 'text')

    @asynctest.ignore_loop
    def test_get_content_kwargs__photo(self):
        content_kwargs = StrangerHandler._get_content_kwargs(
            {
                'photo': [
                    {'file_id': 'foo'},
                    {'file_id': 'bar'},
                    ],
                },
            'photo',
            )
        self.assertEqual(
            content_kwargs,
            {'photo': 'bar'},
            )

    @asynctest.ignore_loop
    def test_get_content_kwargs__photo_with_caption(self):
        content_kwargs = StrangerHandler._get_content_kwargs(
            {
                'caption': 'baz',
                'photo': [
                    {'file_id': 'foo'},
                    {'file_id': 'bar'},
                    ],
                },
            'photo',
            )
        self.assertEqual(
            content_kwargs,
            {
                'caption': 'baz',
                'photo': 'bar',
                },
            )

    @asynctest.ignore_loop
    def test_get_content_kwargs__photo_with_reply(self):
        with self.assertRaises(UnsupportedContentError):
            StrangerHandler._get_content_kwargs(
                {
                    'reply_to_message': None,
                    'photo': [
                        {'file_id': 'foo'},
                        {'file_id': 'bar'},
                        ],
                    },
                'photo',
                )

    @asynctest.ignore_loop
    def test_get_content_kwargs__invalid_photo(self):
        with self.assertRaises(UnsupportedContentError):
            StrangerHandler._get_content_kwargs({}, 'photo')

    @asynctest.ignore_loop
    def test_get_content_kwargs__video(self):
        with self.assertRaises(UnsupportedContentError):
            StrangerHandler._get_content_kwargs({}, 'video')

    def test_handle_command__begin(self):
        partner = CoroutineMock()
        self.stranger_service.get_partner.return_value = partner
        yield from self.stranger_handler._handle_command('begin')
        self.stranger_service.get_partner.assert_called_once_with(self.stranger)
        self.stranger.set_partner.assert_called_once_with(partner)
        partner.set_partner.assert_called_once_with(self.stranger)

    def test_handle_command__begin_partner_obtaining_error(self):
        from randtalkbot.stranger_service import PartnerObtainingError
        partner = CoroutineMock()
        self.stranger_service.get_partner.side_effect = PartnerObtainingError()
        yield from self.stranger_handler._handle_command('begin')
        self.stranger_service.get_partner.assert_called_once_with(self.stranger)
        self.stranger.set_looking_for_partner.assert_called_once_with()

    def test_handle_command__end(self):
        yield from self.stranger_handler._handle_command('end')
        self.stranger.end_chatting.assert_called_once_with()

    @patch('randtalkbot.stranger_handler.HELP_PATTERN', 'help {0} {1}')
    @patch('randtalkbot.stranger_handler.__version__', '0.0.0')
    @asyncio.coroutine
    def test_handle_command__help(self):
        yield from self.stranger_handler._handle_command('help')
        self.sender.send_notification.assert_called_once_with('*Help*\n\nhelp 31416 0.0.0')

    def test_handle_command__setup(self):
        yield from self.stranger_handler._handle_command('setup')
        self.stranger_setup_wizard.activate.assert_called_once_with()

    @patch('randtalkbot.stranger_handler.MANUAL', 'some_manual')
    @asyncio.coroutine
    def test_handle_command__start(self):
        yield from self.stranger_handler._handle_command('start')
        self.sender.send_notification.assert_called_once_with('*Manual*\n\nsome_manual')

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @asyncio.coroutine
    def test_on_message__not_private(self):
        from randtalkbot.stranger_handler import telepot
        telepot.glance2.return_value = 'text', 'not_private', 31416
        self.stranger_handler.send_notification = CoroutineMock()
        yield from self.stranger_handler.on_message('message')
        telepot.glance2.assert_called_once_with('message')
        self.stranger_handler.send_notification.assert_not_called()
        self.stranger.send_to_partner.assert_not_called()
        self.assertFalse(self.stranger_setup_wizard.handle.called)

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch(
        'randtalkbot.stranger_handler.StrangerHandler._get_content_kwargs',
        Mock(side_effect=UnsupportedContentError()),
        )
    @asyncio.coroutine
    def test_on_message__video(self):
        from randtalkbot.stranger_handler import telepot
        telepot.glance2.return_value = 'video', 'private', 31416
        self.stranger_handler.send_notification = CoroutineMock()
        yield from self.stranger_handler.on_message('message')
        telepot.glance2.assert_called_once_with('message')
        self.sender.send_notification.assert_called_once_with(
            'Messages of this type aren\'t supported.',
            )
        self.stranger.send_to_partner.assert_not_called()
        self.assertFalse(self.stranger_setup_wizard.handle.called)
        StrangerHandler._get_content_kwargs.assert_called_once_with('message', 'video')

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch(
        'randtalkbot.stranger_handler.StrangerHandler._get_command',
        Mock(side_effect=MissingCommandError()),
        )
    @patch('randtalkbot.stranger_handler.StrangerHandler._get_content_kwargs', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler._handle_command')
    @asyncio.coroutine
    def test_on_message__text(self, handle_command_mock):
        from randtalkbot.stranger_handler import telepot
        telepot.glance2.return_value = 'text', 'private', 31416
        self.stranger_handler.send_notification = CoroutineMock()
        self.stranger_setup_wizard.handle.return_value = False
        message = {
            'text': 'message_text',
            }
        StrangerHandler._get_content_kwargs.return_value = 'content_kwargs'
        yield from self.stranger_handler.on_message(message)
        telepot.glance2.assert_called_once_with(message)
        self.stranger_handler.send_notification.assert_not_called()
        self.stranger.send_to_partner.assert_called_once_with('text', 'content_kwargs')
        self.stranger_setup_wizard.handle.assert_called_once_with('message_text')
        StrangerHandler._get_command.assert_called_once_with('message_text')
        StrangerHandler._get_content_kwargs.assert_called_once_with(message, 'text')
        handle_command_mock.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch(
        'randtalkbot.stranger_handler.StrangerHandler._get_command',
        Mock(side_effect=MissingCommandError()),
        )
    @patch('randtalkbot.stranger_handler.StrangerHandler._get_content_kwargs', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler._handle_command')
    @asyncio.coroutine
    def test_on_message__text_no_partner(self, handle_command_mock):
        from randtalkbot.stranger_handler import telepot
        from randtalkbot.stranger import MissingPartnerError
        telepot.glance2.return_value = 'text', 'private', 31416
        self.stranger_handler.send_notification = CoroutineMock()
        self.stranger_setup_wizard.handle.return_value = False
        message = {
            'text': 'message_text',
            }
        self.stranger.send_to_partner = CoroutineMock(side_effect=MissingPartnerError())
        StrangerHandler._get_content_kwargs.return_value = 'content_kwargs'
        yield from self.stranger_handler.on_message(message)
        telepot.glance2.assert_called_once_with(message)
        self.stranger_handler.send_notification.assert_not_called()
        self.stranger.send_to_partner.assert_called_once_with('text', 'content_kwargs')
        self.stranger_setup_wizard.handle.assert_called_once_with('message_text')
        StrangerHandler._get_command.assert_called_once_with('message_text')
        StrangerHandler._get_content_kwargs.assert_called_once_with(message, 'text')
        handle_command_mock.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler._get_command', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler._get_content_kwargs', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler._handle_command')
    @asyncio.coroutine
    def test_on_message__command(self, handle_command_mock):
        from randtalkbot.stranger_handler import telepot
        telepot.glance2.return_value = 'text', 'private', 31416
        self.stranger_handler.send_notification = CoroutineMock()
        self.stranger_setup_wizard.handle.return_value = False
        message = {
            'text': 'some_command',
            }
        StrangerHandler._get_command.return_value = 'some_command'
        yield from self.stranger_handler.on_message(message)
        telepot.glance2.assert_called_once_with(message)
        self.stranger_handler.send_notification.assert_not_called()
        self.stranger.send_to_partner.assert_not_called()
        self.stranger_setup_wizard.handle.assert_called_once_with('some_command')
        StrangerHandler._get_command.assert_called_once_with('some_command')
        StrangerHandler._get_content_kwargs.assert_called_once_with(message, 'text')
        handle_command_mock.assert_called_once_with('some_command')

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch(
        'randtalkbot.stranger_handler.StrangerHandler._get_command',
        Mock(side_effect=MissingCommandError()),
        )
    @patch('randtalkbot.stranger_handler.StrangerHandler._get_content_kwargs', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler._handle_command')
    @asyncio.coroutine
    def test_on_message__photo(self, handle_command_mock):
        from randtalkbot.stranger_handler import telepot
        telepot.glance2.return_value = 'photo', 'private', 31416
        self.stranger_handler.send_notification = CoroutineMock()
        message = {
            'photo': [
                {'file_id': 'foo'},
                {'file_id': 'bar'},
                ],
            }
        StrangerHandler._get_content_kwargs.return_value = 'content_kwargs'
        yield from self.stranger_handler.on_message(message)
        telepot.glance2.assert_called_once_with(message)
        self.stranger_handler.send_notification.assert_not_called()
        self.stranger.send_to_partner.assert_called_once_with('photo', 'content_kwargs')
        StrangerHandler._get_command.assert_not_called()
        StrangerHandler._get_content_kwargs.assert_called_once_with(message, 'photo')
        handle_command_mock.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch(
        'randtalkbot.stranger_handler.StrangerHandler._get_command',
        Mock(side_effect=MissingCommandError()),
        )
    @patch('randtalkbot.stranger_handler.StrangerHandler._get_content_kwargs', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler._handle_command')
    @asyncio.coroutine
    def test_on_message__photo_no_partner(self, handle_command_mock):
        from randtalkbot.stranger_handler import telepot
        from randtalkbot.stranger import MissingPartnerError
        telepot.glance2.return_value = 'photo', 'private', 31416
        self.stranger_handler.send_notification = CoroutineMock()
        message = {
            'photo': [
                {'file_id': 'foo'},
                {'file_id': 'bar'},
                ],
            }
        self.stranger.send_to_partner = CoroutineMock(side_effect=MissingPartnerError())
        StrangerHandler._get_content_kwargs.return_value = 'content_kwargs'
        yield from self.stranger_handler.on_message(message)
        telepot.glance2.assert_called_once_with(message)
        self.stranger_handler.send_notification.assert_not_called()
        self.stranger.send_to_partner.assert_called_once_with('photo', 'content_kwargs')
        StrangerHandler._get_command.assert_not_called()
        StrangerHandler._get_content_kwargs.assert_called_once_with(message, 'photo')
        handle_command_mock.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch(
        'randtalkbot.stranger_handler.StrangerHandler._get_command',
        Mock(side_effect=MissingCommandError()),
        )
    @patch('randtalkbot.stranger_handler.StrangerHandler._get_content_kwargs', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler._handle_command')
    @asyncio.coroutine
    def test_on_message__setup(self, handle_command_mock):
        from randtalkbot.stranger_handler import telepot
        telepot.glance2.return_value = 'text', 'private', 31416
        self.stranger_handler.send_notification = CoroutineMock()
        # This means, message was handled by StrangerSetupWizard.
        self.stranger_setup_wizard.handle.return_value = True
        message = {
            'text': 'message_text',
            }
        StrangerHandler._get_content_kwargs.return_value = 'content_kwargs'
        yield from self.stranger_handler.on_message(message)
        telepot.glance2.assert_called_once_with(message)
        self.stranger_handler.send_notification.assert_not_called()
        self.stranger.send_to_partner.assert_not_called()
        self.stranger_setup_wizard.handle.assert_called_once_with('message_text')
        StrangerHandler._get_command.assert_not_called()
        StrangerHandler._get_content_kwargs.assert_called_once_with(message, 'text')
        handle_command_mock.assert_not_called()
