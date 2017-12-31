    # RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from unittest.mock import create_autospec, patch, Mock
from randtalkbot.stranger_sender import StrangerSender
from randtalkbot.stranger_sender_service import StrangerSenderService, StrangerSenderServiceError

class TestStrangerSenderService(unittest.TestCase):
    def setUp(self):
        self.bot = Mock()
        self.stranger_sender_service = StrangerSenderService(self.bot)
        # Cached instance should be cleared for each test.
        StrangerSenderService._instance = None

    def test_init(self):
        self.assertEqual(self.stranger_sender_service._bot, self.bot)

    def test_get_instance__cached(self):
        StrangerSenderService._instance = self.stranger_sender_service
        self.assertEqual(StrangerSenderService.get_instance(), self.stranger_sender_service)

    def test_get_instance__not_cached_with_bot(self):
        self.assertIsInstance(StrangerSenderService.get_instance(self.bot), StrangerSenderService)

    def test_get_instance__not_cached_without_bot(self):
        with self.assertRaises(StrangerSenderServiceError):
            StrangerSenderService.get_instance()

    def test_get_cache_size(self):
        self.assertEqual(self.stranger_sender_service.get_cache_size(), 0)
        self.stranger_sender_service._stranger_senders = {
            0: 0,
            1: 1,
            }
        self.assertEqual(self.stranger_sender_service.get_cache_size(), 2)

    @patch('randtalkbot.stranger_sender_service.StrangerSender', create_autospec(StrangerSender))
    def test_get_or_create_stranger_sender__cached(self):
        from randtalkbot.stranger_sender_service import StrangerSender as stranger_sender_cls_mock
        stranger_sender = Mock()
        stranger = Mock()
        stranger.telegram_id = 31416
        self.stranger_sender_service._stranger_senders[31416] = stranger_sender
        self.assertEqual(
            self.stranger_sender_service.get_or_create_stranger_sender(stranger),
            stranger_sender,
            )
        self.assertFalse(stranger_sender_cls_mock.called)

    @patch('randtalkbot.stranger_sender_service.StrangerSender', create_autospec(StrangerSender))
    def test_get_or_create_stranger_sender__not_cached(self):
        from randtalkbot.stranger_sender_service import StrangerSender as stranger_sender_cls_mock
        stranger_sender = stranger_sender_cls_mock.return_value
        stranger = Mock()
        stranger.telegram_id = 31416
        self.assertEqual(
            self.stranger_sender_service.get_or_create_stranger_sender(stranger),
            stranger_sender,
            )
        stranger_sender_cls_mock.assert_called_once_with(self.bot, stranger)
        self.assertEqual(self.stranger_sender_service._stranger_senders[31416], stranger_sender)
