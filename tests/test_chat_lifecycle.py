# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2018 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import logging
import asynctest
from asynctest.mock import patch, CoroutineMock
from telepot_testing import assert_sent_message, receive_message
from .helpers import assert_db, finalize, run, patch_telepot, setup_db

LOGGER = logging.getLogger('tests.test_chat_lifecycle')
STRANGER1_1 = {
    'id': 11,
    'invitation': 'foo_invitation',
    'languages': '["en"]',
    'partner_sex': 'not_specified',
    'sex': 'not_specified',
    'telegram_id': 110,
    }
STRANGER1_2 = {
    'id': 12,
    'invitation': 'bar_invitation',
    'languages': '["en"]',
    'partner_sex': 'not_specified',
    'sex': 'not_specified',
    'telegram_id': 120,
    }
STRANGER2_1 = {
    'id': 21,
    'invitation': '21_invitation',
    'languages': '["en"]',
    'looking_for_partner_from': datetime.datetime(1970, 1, 1),
    'partner_sex': 'female',
    'sex': 'not_specified',
    'telegram_id': 210,
    }
STRANGER3_1 = {
    'id': 31,
    'bonus_count': 12,
    'invitation': '31_invitation',
    'languages': '["en"]',
    'partner_sex': 'not_specified',
    'sex': 'not_specified',
    'telegram_id': 310,
    }
STRANGER3_2 = {
    'id': 32,
    'invitation': '32_invitation',
    'languages': '["en"]',
    'partner_sex': 'not_specified',
    'sex': 'not_specified',
    'telegram_id': 320,
    }
TALK3 = {
    'id': 1,
    'partner1_id': STRANGER3_1['id'],
    'partner1_sent': 0,
    'partner2_id': STRANGER3_2['id'],
    'partner2_sent': 1,
    'searched_since': datetime.datetime(1970, 1, 1)
    }

async def test_unsuccessful_search(ratio, text):
    from randtalkbot.stranger import asyncio as asyncio_mock
    setup_db({
        'strangers': [STRANGER1_1, STRANGER1_2, STRANGER2_1],
        'talks': [TALK3],
        })

    with patch('randtalkbot.stranger.StatsService'):
        from randtalkbot.stranger import StatsService as stats_service_mock
        stats_service_mock.get_instance \
            .return_value \
            .get_stats \
            .return_value \
            .get_sex_ratio \
            .return_value = ratio

        with patch('randtalkbot.stranger.asyncio.sleep', CoroutineMock()):
            receive_message(STRANGER1_1['telegram_id'], '/begin')
            await assert_sent_message(
                STRANGER1_1['telegram_id'],
                '*Rand Talk:* Looking for a stranger for you 🤔',
                )
            asyncio_mock.sleep.assert_called_once_with(30)

    assert_db({
        'strangers': [
            {
                'id': STRANGER1_1['id'],
                'looking_for_partner_from': datetime.datetime.utcnow()
                },
            ],
        })
    await assert_sent_message(STRANGER1_1['telegram_id'], text, disable_notification=True)
    await assert_sent_message(
        STRANGER1_1['telegram_id'],
        '*Rand Talk:* Do[\u2009](http://randtalk.ml/static/img/logo-125x125.png) you want'
        ' to talk with somebody, practice in foreign languages or you just'
        ' want to have some fun? Rand Talk will help you! It\'s a bot matching you'
        ' with a random stranger of desired sex speaking on your language. [Check it out!]'
        '(https://telegram.me/RandTalkBot?start=eyJpIjoiZm9vX2ludml0YXRpb24ifQ==)',
        disable_notification=True,
        )

class TestChatLifecycle(asynctest.TestCase):
    @patch_telepot
    def setUp(self):
        run(self)

    def tearDown(self):
        finalize(self)

    async def test_end_chat__no_bonuses(self):
        setup_db({
            'strangers': [STRANGER3_1, STRANGER3_2],
            'talks': [TALK3],
            })
        receive_message(STRANGER3_1['telegram_id'], '/end')
        await assert_sent_message(
            STRANGER3_1['telegram_id'],
            '*Rand Talk:* Chat was finished. Feel free to /begin a new one.',
            )
        await assert_sent_message(
            STRANGER3_2['telegram_id'],
            '*Rand Talk:* Your partner has left chat. 😿 Feel free to /begin a new one.',
            )
        assert_db({
            'talks': [
                {
                    'id': TALK3['id'],
                    'end': datetime.datetime.utcnow(),
                    },
                ],
            })

    async def test_end_chat__one_bonus_was_spent(self):
        expected_bonus_count = STRANGER3_1['bonus_count'] - 1
        talk3_spending_bonus = {
            'id': 1,
            'partner1_id': STRANGER3_1['id'],
            'partner1_sent': 1,
            'partner2_id': STRANGER3_2['id'],
            'partner2_sent': 1,
            'searched_since': datetime.datetime(1970, 1, 1)
            }
        setup_db({
            'strangers': [STRANGER3_1, STRANGER3_2],
            'talks': [talk3_spending_bonus],
            })
        receive_message(STRANGER3_1['telegram_id'], '/end')
        await assert_sent_message(
            STRANGER3_1['telegram_id'],
            f'*Rand Talk:* Chat was finished. You\'ve used one bonus. {expected_bonus_count}'
            ' bonus(es) left. Feel free to /begin a new one.',
            )
        await assert_sent_message(
            STRANGER3_2['telegram_id'],
            '*Rand Talk:* Your partner has left chat. 😿 Feel free to /begin a new one.',
            )
        assert_db({
            'strangers': [
                {
                    'id': STRANGER3_1['id'],
                    'bonus_count': expected_bonus_count,
                    },
                ],
            'talks': [
                {
                    'id': talk3_spending_bonus['id'],
                    'end': datetime.datetime.utcnow(),
                    },
                ],
            })

    async def test_end_chat__last_bonus_was_spent(self):
        stranger3_1_last_bonus = {
            'id': 31,
            'bonus_count': 1,
            'invitation': '31_invitation',
            'languages': '["en"]',
            'partner_sex': 'not_specified',
            'sex': 'not_specified',
            'telegram_id': 310,
            }
        talk3_spending_last_bonus = {
            'id': 1,
            'partner1_id': stranger3_1_last_bonus['id'],
            'partner1_sent': 1,
            'partner2_id': STRANGER3_2['id'],
            'partner2_sent': 1,
            'searched_since': datetime.datetime(1970, 1, 1)
            }
        setup_db({
            'strangers': [stranger3_1_last_bonus, STRANGER3_2],
            'talks': [talk3_spending_last_bonus],
            })
        receive_message(stranger3_1_last_bonus['telegram_id'], '/end')
        await assert_sent_message(
            stranger3_1_last_bonus['telegram_id'],
            '*Rand Talk:* Chat was finished. You\'ve used your last bonus. Feel free'
            ' to /begin a new one.',
            )
        await assert_sent_message(
            STRANGER3_2['telegram_id'],
            '*Rand Talk:* Your partner has left chat. 😿 Feel free to /begin a new one.',
            )
        assert_db({
            'strangers': [
                {
                    'id': stranger3_1_last_bonus['id'],
                    'bonus_count': 0,
                    },
                ],
            'talks': [
                {
                    'id': talk3_spending_last_bonus['id'],
                    'end': datetime.datetime.utcnow(),
                    },
                ],
            })

    async def test_end_search(self):
        stranger = STRANGER2_1
        setup_db({
            'strangers': [stranger],
            })
        receive_message(stranger['telegram_id'], '/end')
        await assert_sent_message(
            stranger['telegram_id'],
            '*Rand Talk:* Looking for partner was stopped',
            )
        assert_db({
            'strangers': [
                {
                    'id': stranger['id'],
                    'looking_for_partner_from': None,
                    },
                ],
            })

    async def test_nonsense_end(self):
        stranger = STRANGER2_1
        setup_db({
            'strangers': [stranger],
            })
        receive_message(stranger['telegram_id'], '/end')
        assert_db({
            'strangers': [stranger],
            })

    async def test_unsuccessful_search__chat_lacks_females(self):
        text = \
            '*Rand Talk:* The search is going on. 2 users are looking for partner — change your' \
            ' preferences (languages, partner\'s sex) using /setup command to talk with' \
            ' them.\n' \
            'Chat *lacks females!* Send the link to your friends and earn 3 bonuses for' \
            ' every invited female and 1 bonus for each male (the more bonuses you' \
            ' have → the faster partner\'s search will be):'
        await test_unsuccessful_search(1.1, text)

    async def test_unsuccessful_search__chat_lacks_males(self):
        text = \
            '*Rand Talk:* The search is going on. 2 users are looking for partner — change your' \
            ' preferences (languages, partner\'s sex) using /setup command to talk with' \
            ' them.\n' \
            'Chat *lacks males!* Send the link to your friends and earn 3 bonuses for' \
            ' every invited male and 1 bonus for each female (the more bonuses you' \
            ' have → the faster partner\'s search will be):'
        await test_unsuccessful_search(.9, text)
