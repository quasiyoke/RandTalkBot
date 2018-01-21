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
    'searched_since': datetime.datetime(1970, 1, 1),
    }
STRANGER4_1 = {
    'id': 41,
    'invitation': '41_invitation',
    'languages': '["en"]',
    'sex': 'female',
    'partner_sex': 'not_specified',
    'telegram_id': 410,
    }
STRANGER4_WAITED_LONG = {
    'id': 42,
    'invitation': '42_invitation',
    'languages': '["en"]',
    'looking_for_partner_from': datetime.datetime(1990, 1, 1),
    'sex': 'female',
    'partner_sex': 'not_specified',
    'telegram_id': 420,
    }
STRANGER4_WAITED_LONGEST = {
    'id': 43,
    'invitation': '43_invitation',
    'languages': '["en"]',
    'looking_for_partner_from': datetime.datetime(1970, 1, 1),
    'sex': 'female',
    'partner_sex': 'not_specified',
    'telegram_id': 430,
    }
STRANGER4_WAITED_LONGER = {
    'id': 44,
    'invitation': '44_invitation',
    'languages': '["en"]',
    'looking_for_partner_from': datetime.datetime(1980, 1, 1),
    'sex': 'female',
    'partner_sex': 'not_specified',
    'telegram_id': 440,
    }
TALK4_1 = {
    'id': 1,
    'partner1_id': STRANGER4_1['id'],
    'partner1_sent': 0,
    'partner2_id': STRANGER4_WAITED_LONGER['id'],
    'partner2_sent': 0,
    'searched_since': STRANGER4_WAITED_LONGER['looking_for_partner_from'],
    }
TALK4_2 = {
    'id': 1,
    'partner1_id': STRANGER4_1['id'],
    'partner1_sent': 0,
    'partner2_id': STRANGER4_WAITED_LONGEST['id'],
    'partner2_sent': 0,
    'searched_since': STRANGER4_WAITED_LONGEST['looking_for_partner_from'],
    }
STRANGER5_1 = {
    'id': 51,
    'invitation': '51_invitation',
    'languages': '["en"]',
    'sex': 'female',
    'partner_sex': 'male',
    'telegram_id': 510,
    }
STRANGER5_FEMALE_1 = {
    'id': 52,
    'invitation': '52_invitation',
    'languages': '["en"]',
    'looking_for_partner_from': datetime.datetime(2000, 1, 1),
    'sex': 'female',
    'partner_sex': 'not_specified',
    'telegram_id': 520,
    }
STRANGER5_MALE = {
    'id': 53,
    'invitation': '53_invitation',
    'languages': '["en"]',
    'looking_for_partner_from': datetime.datetime(2000, 1, 1),
    'sex': 'male',
    'partner_sex': 'female',
    'telegram_id': 530,
    }
STRANGER5_FEMALE_2 = {
    'id': 54,
    'invitation': '54_invitation',
    'languages': '["en"]',
    'looking_for_partner_from': datetime.datetime(2000, 1, 1),
    'sex': 'female',
    'partner_sex': 'not_specified',
    'telegram_id': 540,
    }
TALK5 = {
    'id': 1,
    'partner1_id': STRANGER5_1['id'],
    'partner1_sent': 0,
    'partner2_id': STRANGER5_MALE['id'],
    'partner2_sent': 0,
    'searched_since': STRANGER5_MALE['looking_for_partner_from'],
    }
STRANGER6_1 = {
    'id': 61,
    'invitation': '61_invitation',
    'languages': '["en"]',
    'sex': 'male',
    'partner_sex': 'not_specified',
    'telegram_id': 610,
    }
STRANGER6_LOOKING_FOR_MALE = {
    'id': 62,
    'invitation': '62_invitation',
    'languages': '["en"]',
    'looking_for_partner_from': datetime.datetime(2000, 1, 1),
    'sex': 'female',
    'partner_sex': 'male',
    'telegram_id': 620,
    }
STRANGER6_LOOKING_FOR_FEMALE = {
    'id': 63,
    'invitation': '63_invitation',
    'languages': '["en"]',
    'looking_for_partner_from': datetime.datetime(2000, 1, 1),
    'sex': 'female',
    'partner_sex': 'female',
    'telegram_id': 630,
    }
STRANGER6_LOOKING_FOR_NOT_SPECIFIED = {
    'id': 64,
    'invitation': '64_invitation',
    'languages': '["en"]',
    'looking_for_partner_from': datetime.datetime(2000, 1, 1),
    'sex': 'male',
    'partner_sex': 'not_specified',
    'telegram_id': 640,
    }
TALK6_1 = {
    'id': 1,
    'partner1_id': STRANGER6_1['id'],
    'partner1_sent': 0,
    'partner2_id': STRANGER6_LOOKING_FOR_MALE['id'],
    'partner2_sent': 0,
    'searched_since': STRANGER6_LOOKING_FOR_MALE['looking_for_partner_from'],
    }
TALK6_2 = {
    'id': 1,
    'partner1_id': STRANGER6_1['id'],
    'partner1_sent': 0,
    'partner2_id': STRANGER6_LOOKING_FOR_NOT_SPECIFIED['id'],
    'partner2_sent': 0,
    'searched_since': STRANGER6_LOOKING_FOR_NOT_SPECIFIED['looking_for_partner_from'],
    }
STRANGER7_1 = {
    'id': 71,
    'invitation': '71_invitation',
    'languages': '["fr", "fa", "ru"]',
    'sex': 'female',
    'partner_sex': 'not_specified',
    'telegram_id': 710,
    }
STRANGER7_SPEAKS_FR = {
    'id': 72,
    'invitation': '72_invitation',
    'languages': '["fr"]',
    'looking_for_partner_from': datetime.datetime(2000, 1, 1),
    'sex': 'female',
    'partner_sex': 'not_specified',
    'telegram_id': 720,
    }
STRANGER7_SPEAKS_RU = {
    'id': 73,
    'invitation': '73_invitation',
    'languages': '["ru"]',
    'looking_for_partner_from': datetime.datetime(2000, 1, 1),
    'sex': 'female',
    'partner_sex': 'not_specified',
    'telegram_id': 730,
    }
STRANGER7_SPEAKS_FA = {
    'id': 74,
    'invitation': '74_invitation',
    'languages': '["fa"]',
    'looking_for_partner_from': datetime.datetime(2000, 1, 1),
    'sex': 'female',
    'partner_sex': 'not_specified',
    'telegram_id': 740,
    }
TALK7_1 = {
    'id': 1,
    'partner1_id': STRANGER7_1['id'],
    'partner1_sent': 0,
    'partner2_id': STRANGER7_SPEAKS_FR['id'],
    'partner2_sent': 0,
    'searched_since': STRANGER7_SPEAKS_FR['looking_for_partner_from'],
    }
TALK7_2 = {
    'id': 1,
    'partner1_id': STRANGER7_1['id'],
    'partner1_sent': 0,
    'partner2_id': STRANGER7_SPEAKS_FA['id'],
    'partner2_sent': 0,
    'searched_since': STRANGER7_SPEAKS_FA['looking_for_partner_from'],
    }
STRANGER8_1 = {
    'id': 81,
    'invitation': '81_invitation',
    'languages': '["en"]',
    'sex': 'male',
    'partner_sex': 'not_specified',
    'telegram_id': 810,
    }
STRANGER8_SPEAKS_FR = {
    'id': 82,
    'invitation': '82_invitation',
    'languages': '["fr"]',
    'looking_for_partner_from': datetime.datetime(2000, 1, 1),
    'sex': 'female',
    'partner_sex': 'not_specified',
    'telegram_id': 820,
    }
STRANGER8_SPEAKS_RU = {
    'id': 83,
    'invitation': '83_invitation',
    'languages': '["ru"]',
    'looking_for_partner_from': datetime.datetime(2000, 1, 1),
    'sex': 'female',
    'partner_sex': 'not_specified',
    'telegram_id': 830,
    }
STRANGER8_SPEAKS_FA = {
    'id': 84,
    'invitation': '84_invitation',
    'languages': '["fa"]',
    'looking_for_partner_from': datetime.datetime(2000, 1, 1),
    'sex': 'female',
    'partner_sex': 'not_specified',
    'telegram_id': 840,
    }
TALK8_1 = {
    'id': 1,
    'partner1_id': STRANGER8_1['id'],
    'partner1_sent': 0,
    'partner2_id': STRANGER8_SPEAKS_FR['id'],
    'partner2_sent': 0,
    'searched_since': STRANGER8_SPEAKS_FR['looking_for_partner_from'],
    }
TALK8_2 = {
    'id': 1,
    'partner1_id': STRANGER8_1['id'],
    'partner1_sent': 0,
    'partner2_id': STRANGER8_SPEAKS_FA['id'],
    'partner2_sent': 0,
    'searched_since': STRANGER8_SPEAKS_FA['looking_for_partner_from'],
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

    async def test_successful_search__matches_stranger_looking_for_proper_sex_1(self):
        setup_db({
            'strangers': [STRANGER6_1, STRANGER6_LOOKING_FOR_MALE, STRANGER6_LOOKING_FOR_FEMALE],
            })
        receive_message(STRANGER6_1['telegram_id'], '/begin')
        assert_db({
            'talks': [TALK6_1],
            })
        await assert_sent_message(
            STRANGER6_LOOKING_FOR_MALE['telegram_id'],
            '*Rand Talk:* Your partner is here. Have a nice chat 🤗',
            )
        await assert_sent_message(
            STRANGER6_1['telegram_id'],
            re.compile(
                r'\*Rand Talk:\* Your partner is here\. Your partner\'s been looking for you for'
                r' \d+ hr\. Say him “Hello” — if he doesn\'t respond to you, launch search again'
                r' by /begin command\.',
                ),
            )

    async def test_successful_search__matches_stranger_looking_for_proper_sex_2(self):
        setup_db({
            'strangers': [
                STRANGER6_1,
                STRANGER6_LOOKING_FOR_FEMALE,
                STRANGER6_LOOKING_FOR_NOT_SPECIFIED
                ],
            })
        receive_message(STRANGER6_1['telegram_id'], '/begin')
        assert_db({
            'talks': [TALK6_1],
            })
        await assert_sent_message(
            STRANGER6_LOOKING_FOR_NOT_SPECIFIED['telegram_id'],
            '*Rand Talk:* Your partner is here. Have a nice chat 🤗',
            )
        await assert_sent_message(
            STRANGER6_1['telegram_id'],
            re.compile(
                r'\*Rand Talk:\* Your partner is here\. Your partner\'s been looking for you for'
                r' \d+ hr\. Say him “Hello” — if he doesn\'t respond to you, launch search again'
                r' by /begin command\.',
                ),
            )

    async def test_successful_search__matches_stranger_speaking_on_preferred_language_1(self):
        setup_db({
            'strangers': [STRANGER7_1, STRANGER7_SPEAKS_FR, STRANGER7_SPEAKS_RU],
            })
        receive_message(STRANGER7_1['telegram_id'], '/begin')
        assert_db({
            'talks': [TALK7_1],
            })
        await assert_sent_message(
            STRANGER7_SPEAKS_FR['telegram_id'],
            '*Rand Talk:* Your partner is here. Have a nice chat 🤗',
            )
        await assert_sent_message(
            STRANGER7_1['telegram_id'],
            re.compile(
                r'\*Rand Talk:\* Your partner is here\. Use French please\. Your partner\'s been'
                r' looking for you for \d+ hr\. Say him “Hello” — if he doesn\'t respond to you,'
                r' launch search again by /begin command\.',
                ),
            )

    async def test_successful_search__matches_stranger_speaking_on_preferred_language_2(self):
        setup_db({
            'strangers': [STRANGER7_1, STRANGER7_SPEAKS_RU, STRANGER7_SPEAKS_FA],
            })
        receive_message(STRANGER7_1['telegram_id'], '/begin')
        assert_db({
            'talks': [TALK7_2],
            })
        await assert_sent_message(
            STRANGER7_SPEAKS_FA['telegram_id'],
            '*Rand Talk:* Your partner is here. Have a nice chat 🤗',
            )
        await assert_sent_message(
            STRANGER7_1['telegram_id'],
            re.compile(
                r'\*Rand Talk:\* Your partner is here\. Use فارسی please\. Your partner\'s been'
                r' looking for you for \d+ hr\. Say him “Hello” — if he doesn\'t respond to you,'
                r' launch search again by /begin command\.',
                ),
            )

    async def test_successful_search__matches_stranger_with_proper_sex_1(self):
        setup_db({
            'strangers': [STRANGER5_1, STRANGER5_FEMALE_1, STRANGER5_MALE],
            })
        receive_message(STRANGER5_1['telegram_id'], '/begin')
        assert_db({
            'talks': [TALK5],
            })
        await assert_sent_message(
            STRANGER5_MALE['telegram_id'],
            '*Rand Talk:* Your partner is here. Have a nice chat 🤗',
            )
        await assert_sent_message(
            STRANGER5_1['telegram_id'],
            re.compile(
                r'\*Rand Talk:\* Your partner is here\. Your partner\'s been looking for you for'
                r' \d+ hr\. Say him “Hello” — if he doesn\'t respond to you, launch search again'
                r' by /begin command\.',
                ),
            )

    async def test_successful_search__matches_stranger_with_proper_sex_2(self):
        setup_db({
            'strangers': [STRANGER5_1, STRANGER5_MALE, STRANGER5_FEMALE_2],
            })
        receive_message(STRANGER5_1['telegram_id'], '/begin')
        assert_db({
            'talks': [TALK5],
            })
        await assert_sent_message(
            STRANGER5_MALE['telegram_id'],
            '*Rand Talk:* Your partner is here. Have a nice chat 🤗',
            )
        await assert_sent_message(
            STRANGER5_1['telegram_id'],
            re.compile(
                r'\*Rand Talk:\* Your partner is here\. Your partner\'s been looking for you for'
                r' \d+ hr\. Say him “Hello” — if he doesn\'t respond to you, launch search again'
                r' by /begin command\.',
                ),
            )

    async def test_successful_search__matches_the_longest_waiting_stranger_1(self):
        setup_db({
            'strangers': [STRANGER4_1, STRANGER4_WAITED_LONG, STRANGER4_WAITED_LONGER],
            })
        receive_message(STRANGER4_1['telegram_id'], '/begin')
        assert_db({
            'talks': [TALK4_1],
            })
        await assert_sent_message(
            STRANGER4_WAITED_LONGER['telegram_id'],
            '*Rand Talk:* Your partner is here. Have a nice chat 🤗',
            )
        await assert_sent_message(
            STRANGER4_1['telegram_id'],
            re.compile(
                r'\*Rand Talk:\* Your partner is here\. Your partner\'s been looking for you for'
                r' \d+ hr\. Say him “Hello” — if he doesn\'t respond to you, launch search again'
                r' by /begin command\.',
                ),
            )

    async def test_successful_search__matches_the_longest_waiting_stranger_2(self):
        setup_db({
            'strangers': [STRANGER4_1, STRANGER4_WAITED_LONGER, STRANGER4_WAITED_LONGEST],
            })
        receive_message(STRANGER4_1['telegram_id'], '/begin')
        assert_db({
            'talks': [TALK4_2],
            })
        await assert_sent_message(
            STRANGER4_WAITED_LONGEST['telegram_id'],
            '*Rand Talk:* Your partner is here. Have a nice chat 🤗',
            )
        await assert_sent_message(
            STRANGER4_1['telegram_id'],
            re.compile(
                r'\*Rand Talk:\* Your partner is here\. Your partner\'s been looking for you for'
                r' \d+ hr\. Say him “Hello” — if he doesn\'t respond to you, launch search again'
                r' by /begin command\.',
                ),
            )

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
