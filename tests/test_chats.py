# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2018 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import asynctest
from telepot_testing import assert_sent_message, receive_message
from .helpers import assert_db, finalize, run, patch_telepot, setup_db

STRANGER1_1 = {
    'id': 1,
    'invitation': 'foo',
    'languages': '["en"]',
    'partner_sex': 'not_specified',
    'sex': 'not_specified',
    'telegram_id': 123,
    }
STRANGER1_2 = {
    'id': 2,
    'invitation': 'bar',
    'languages': '["en"]',
    'partner_sex': 'not_specified',
    'sex': 'not_specified',
    'telegram_id': 345,
    }
TALK1 = {
    'id': 1,
    'partner1_id': STRANGER1_1['id'],
    'partner1_sent': 12,
    'partner2_id': STRANGER1_2['id'],
    'partner2_sent': 44,
    'searched_since': datetime.datetime(1970, 1, 1)
    }

class TestChats(asynctest.TestCase):
    @patch_telepot
    def setUp(self):
        run(self)

    def tearDown(self):
        finalize(self)

    async def test_message_from_partner1_to_partner2_was_sent(self):
        setup_db({
            'strangers': [STRANGER1_1, STRANGER1_2],
            'talks': [TALK1],
            })
        receive_message(STRANGER1_1['telegram_id'], 'Hello')
        await assert_sent_message(STRANGER1_2['telegram_id'], 'Hello')
        assert_db({
            'talks': [
                {
                    'id': TALK1['id'],
                    'partner1_sent': TALK1['partner1_sent'] + 1,
                    },
                ],
            })

    async def test_message_from_partner2_to_partner1_was_sent(self):
        setup_db({
            'strangers': [STRANGER1_1, STRANGER1_2],
            'talks': [TALK1],
            })
        receive_message(STRANGER1_2['telegram_id'], 'Hi')
        await assert_sent_message(STRANGER1_1['telegram_id'], 'Hi')
        assert_db({
            'talks': [
                {
                    'id': TALK1['id'],
                    'partner2_sent': TALK1['partner2_sent'] + 1,
                    },
                ],
            })
