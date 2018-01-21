# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2018 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import logging
import re
import asynctest
from asynctest.mock import patch, CoroutineMock
from telepot_testing import assert_sent_message, assert_sent_inline_query_response, receive_message, receive_inline_query
from .helpers import assert_db, finalize, run, patch_telepot, setup_db

LOGGER = logging.getLogger('tests.test_inline_queries')
STRANGER1_1 = {
    'id': 11,
    'invitation': 'foo_invitation',
    'languages': '["en"]',
    'partner_sex': 'not_specified',
    'sex': 'not_specified',
    'telegram_id': 110,
    }

class TestInlineQueries(asynctest.TestCase):
    @patch_telepot
    def setUp(self):
        run(self)

    def tearDown(self):
        finalize(self)

    async def test_on_inline_query(self):
        setup_db({
            'strangers': [STRANGER1_1],
            })
        query_id = 31416
        receive_inline_query(STRANGER1_1['telegram_id'], query_id, 'hello')
        await assert_sent_inline_query_response(
            query_id,
            [{
                'id': 'invitation_link',
                'description': 'The more friends\'ll use your link — the faster search'
                    ' at Rand Talk will be',
                'message_text': 'Do[\u2009'
                    '](http://randtalk.ml/static/img/logo-125x125.png) you want to talk with'
                    ' somebody, practice in foreign languages or you just want to have some fun?'
                    ' Rand Talk will help you! It\'s a bot matching you with a random stranger'
                    ' of desired sex speaking on your language.'
                    ' [Check it out!]'
                    '(https://telegram.me/RandTalkBot?start=eyJpIjoiZm9vX2ludml0YXRpb24ifQ==)',
                'parse_mode': 'Markdown',
                'thumb_url': 'http://randtalk.ml/static/img/logo-500x500.png',
                'title': 'Rand Talk Invitation Link',
                'type': 'article',
                }],
            is_personal=True,
            )
        assert_db({
            'strangers': [STRANGER1_1],
            })
