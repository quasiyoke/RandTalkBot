# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from randtalkbot.message import Message, UnsupportedContentError
from unittest.mock import create_autospec, patch, Mock

class TestMessage(unittest.TestCase):
    def setUp(self):
        self.message_json = {
            'from': {
                'id': 31416,
                'last_name': 'john_doe',
                'username': 'john_doe',
                'first_name': 'John Doe'
                },
            'date': 1453019994,
            'chat': {
                'id': 31416,
                'type': 'private',
                'last_name': 'john_doe',
                'username': 'john_doe',
                'first_name': 'John Doe',
                },
            'message_id': 27183,
            }
        self.sticker = {
            'height': 512,
            'thumb': {
                'height': 128,
                'width': 128,
                'file_id': 'AAQCABO-o1kqAARdN9Z7Y4p-PmA7AAIC',
                'file_size': 5672,
                },
            'width': 512,
            'file_id': 'BQADAgAD7gAD9HsZAAFCdfFWtd5o1gI',
            'file_size': 34348,
            }

    def test_decode_command_args__ok(self):
        message = Mock()
        message.command_args = 'eyJmb28iOiAiYmFyIn0='
        self.assertEqual(
            Message.decode_command_args(message),
            {"foo": "bar"},
            )

    def test_decode_command_args__b64decode_type_error(self):
        message = Mock()
        message.command_args = None
        with self.assertRaises(UnsupportedContentError):
            Message.decode_command_args(message)

    def test_decode_command_args__b64decode_incorrect_padding(self):
        message = Mock()
        message.command_args = 'NoonfowfVyZSwg'
        with self.assertRaises(UnsupportedContentError):
            Message.decode_command_args(message)

    def test_decode_command_args__b64decode_value_error(self):
        message = Mock()
        message.command_args = 'кириллица'
        with self.assertRaises(UnsupportedContentError):
            Message.decode_command_args(message)

    def test_decode_command_args__unicode_decode_error(self):
        message = Mock()
        message.command_args = '_w==' # b'\xff'
        with self.assertRaises(UnsupportedContentError):
            Message.decode_command_args(message)

    def test_decode_command_args__loading_json_error(self):
        message = Mock()
        message.command_args = 'Ww==' # b'['
        with self.assertRaises(UnsupportedContentError):
            Message.decode_command_args(message)

    def test_init__audio(self):
        self.message_json['audio'] = {
            'file_id': 'foo',
            }
        message = Message(self.message_json)
        self.assertEqual(
            message.sending_kwargs,
            {
                'audio': 'foo',
                'duration': None,
                'performer': None,
                'title': None,
                },
            )

    def test_init__audio_with_info(self):
        self.message_json['audio'] = {
            'duration': 85,
            'file_id': 'foo',
            'performer': 'Pink Floyd',
            'title': 'Another Brick In The Wall Part 3',
            }
        message = Message(self.message_json)
        self.assertEqual(
            message.sending_kwargs,
            {
                'audio': 'foo',
                'duration': 85,
                'performer': 'Pink Floyd',
                'title': 'Another Brick In The Wall Part 3',
                },
            )

    @patch('randtalkbot.message.telepot')
    def test_init__invalid_audio(self, telepot):
        telepot.glance2.return_value = 'audio', 'private', 31416
        with self.assertRaises(UnsupportedContentError):
            Message(self.message_json)

    @patch('randtalkbot.message.telepot')
    def test_init__command_with_args(self, telepot):
        telepot.glance2.return_value = 'text', 'private', 31416
        self.message_json['text'] = '/begin chat'
        message = Message(self.message_json)
        self.assertEqual(message.command, 'begin')
        self.assertEqual(message.command_args, 'chat')

    @patch('randtalkbot.message.telepot')
    def test_init__command_without_args(self, telepot):
        telepot.glance2.return_value = 'text', 'private', 31416
        self.message_json['text'] = '/start'
        message = Message(self.message_json)
        self.assertEqual(message.command, 'start')
        self.assertEqual(message.command_args, '')

    def test_init__document(self):
        self.message_json['document'] = {
            'file_id': 'foo',
            }
        message = Message(self.message_json)
        self.assertEqual(
            message.sending_kwargs,
            {
                'document': 'foo',
                },
            )

    @patch('randtalkbot.message.telepot')
    def test_init__invalid_document(self, telepot):
        telepot.glance2.return_value = 'document', 'private', 31416
        with self.assertRaises(UnsupportedContentError):
            Message(self.message_json)

    def test_init__location(self):
        self.message_json['location'] = {
            'latitude': 'foo',
            'longitude': 'bar',
            }
        message = Message(self.message_json)
        self.assertEqual(
            message.sending_kwargs,
            {
                'latitude': 'foo',
                'longitude': 'bar',
                },
            )

    @patch('randtalkbot.message.telepot')
    def test_init__invalid_location(self, telepot):
        self.message_json['location'] = {
            'latitude': 'foo',
            }
        telepot.glance2.return_value = 'location', 'private', 31416
        with self.assertRaises(UnsupportedContentError):
            Message(self.message_json)

    def test_init__photo(self):
        self.message_json['photo'] = [
            {'file_id': 'foo'},
            {'file_id': 'bar'},
            ]
        message = Message(self.message_json)
        self.assertEqual(
            message.sending_kwargs,
            {
                'caption': None,
                'photo': 'foo',
                },
            )
        self.assertEqual(message.text, None)

    def test_init__photo_with_caption(self):
        self.message_json['photo'] = [
            {'file_id': 'foo'},
            {'file_id': 'bar'},
            ]
        self.message_json['caption'] = 'baz'
        message = Message(self.message_json)
        self.assertEqual(
            message.sending_kwargs,
            {
                'caption': 'baz',
                'photo': 'foo',
                },
            )

    @patch('randtalkbot.message.telepot')
    def test_init__invalid_photo(self, telepot):
        telepot.glance2.return_value = 'photo', 'private', 31416
        with self.assertRaises(UnsupportedContentError):
            Message(self.message_json)

    def test_init__sticker(self):
        self.message_json['sticker'] = self.sticker
        message = Message(self.message_json)
        self.assertEqual(
            message.sending_kwargs,
            {'sticker': 'BQADAgAD7gAD9HsZAAFCdfFWtd5o1gI'},
            )

    @patch('randtalkbot.message.telepot')
    def test_init__invalid_sticker(self, telepot):
        telepot.glance2.return_value = 'sticker', 'private', 31416
        with self.assertRaises(UnsupportedContentError):
            Message(self.message_json)

    def test_init__text(self):
        self.message_json['text'] = 'foo'
        message = Message(self.message_json)
        self.assertEqual(
            message.sending_kwargs,
            {'text': 'foo'},
            )
        self.assertEqual(message.text, 'foo')

    @patch('randtalkbot.message.telepot')
    def test_init__text_without_command_has_empty_comand_field(self, telepot):
        telepot.glance2.return_value = 'text', 'private', 31416
        self.message_json['text'] = 'foo'
        message = Message(self.message_json)
        self.assertEqual(message.command, None)
        self.assertEqual(message.command_args, None)

    def test_init__video(self):
        self.message_json['video'] = {
            'file_id': 'foo',
            }
        message = Message(self.message_json)
        self.assertEqual(
            message.sending_kwargs,
            {
                'video': 'foo',
                'duration': None,
                'caption': None,
                },
            )

    def test_init__video_with_info(self):
        self.message_json['video'] = {
            'duration': 85,
            'file_id': 'foo',
            }
        self.message_json['caption'] = 'Pink Floyd'
        message = Message(self.message_json)
        self.assertEqual(
            message.sending_kwargs,
            {
                'video': 'foo',
                'duration': 85,
                'caption': 'Pink Floyd',
                },
            )

    @patch('randtalkbot.message.telepot')
    def test_init__invalid_video(self, telepot):
        telepot.glance2.return_value = 'video', 'private', 31416
        with self.assertRaises(UnsupportedContentError):
            Message(self.message_json)

    def test_init__voice(self):
        self.message_json['voice'] = {
            'file_id': 'foo',
            }
        message = Message(self.message_json)
        self.assertEqual(
            message.sending_kwargs,
            {
                'voice': 'foo',
                'duration': None,
                },
            )

    def test_init__voice_with_info(self):
        self.message_json['voice'] = {
            'duration': 85,
            'file_id': 'foo',
            }
        message = Message(self.message_json)
        self.assertEqual(
            message.sending_kwargs,
            {
                'voice': 'foo',
                'duration': 85,
                },
            )

    @patch('randtalkbot.message.telepot')
    def test_init__invalid_voice(self, telepot):
        telepot.glance2.return_value = 'voice', 'private', 31416
        with self.assertRaises(UnsupportedContentError):
            Message(self.message_json)

    @patch('randtalkbot.message.telepot')
    def test_init__message_with_reply(self, telepot):
        telepot.glance2.return_value = 'text', 'private', 31416
        self.message_json['reply_to_message'] = None
        with self.assertRaises(UnsupportedContentError):
            Message(self.message_json)

    @patch('randtalkbot.message.telepot')
    def test_init__message_with_forward(self, telepot):
        telepot.glance2.return_value = 'text', 'private', 31416
        self.message_json['forward_from'] = None
        with self.assertRaises(UnsupportedContentError):
            Message(self.message_json)

    def test_init__invalid_json(self):
        with self.assertRaises(UnsupportedContentError):
            Message(self.message_json)

    @patch('randtalkbot.message.telepot')
    def test_init__unknown_content_type(self, telepot):
        telepot.glance2.return_value = 'foo_content_type', 'private', 31416
        with self.assertRaises(UnsupportedContentError):
            Message(self.message_json)
