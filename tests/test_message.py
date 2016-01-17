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

    def test_init__text(self):
        self.message_json['text'] = 'foo'
        message = Message(self.message_json)
        self.assertEqual(
            message.sending_kwargs,
            {'text': 'foo'},
            )

    def test_init__text_with_reply(self):
        self.message_json['text'] = 'foo'
        self.message_json['reply_to_message'] = None
        with self.assertRaises(UnsupportedContentError):
            Message(self.message_json)

    @patch('randtalkbot.message.telepot')
    def test_init__text_invalid(self, telepot):
        telepot.glance2.return_value = 'text', 'private', 31416
        with self.assertRaises(UnsupportedContentError):
            Message(self.message_json)

    def test_init__invalid_json(self):
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
            {'photo': 'bar'},
            )

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
                'photo': 'bar',
                },
            )

    def test_init__photo_with_reply(self):
        self.message_json['photo'] = [
            {'file_id': 'foo'},
            {'file_id': 'bar'},
            ]
        self.message_json['reply_to_message'] = None
        with self.assertRaises(UnsupportedContentError):
            Message(self.message_json)

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

    def test_init__sticker_with_reply(self):
        self.message_json['sticker'] = self.sticker
        self.message_json['reply_to_message'] = None
        with self.assertRaises(UnsupportedContentError):
            Message(self.message_json)

    @patch('randtalkbot.message.telepot')
    def test_init__invalid_sticker(self, telepot):
        telepot.glance2.return_value = 'sticker', 'private', 31416
        with self.assertRaises(UnsupportedContentError):
            Message(self.message_json)

    @patch('randtalkbot.message.telepot')
    def test_init__unknown_content_type(self, telepot):
        telepot.glance2.return_value = 'foo_content_type', 'private', 31416
        with self.assertRaises(UnsupportedContentError):
            Message(self.message_json)
