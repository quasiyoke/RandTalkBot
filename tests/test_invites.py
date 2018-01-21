# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2018 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import base64
import datetime
import json
import logging
import asynctest
from telepot_testing import assert_sent_message, receive_message
from .helpers import assert_db, finalize, run, patch_telepot, setup_db

LOGGER = logging.getLogger('tests.test_invites')
STRANGER1_1_INVITER = {
    'id': 13,
    'bonus_count': 15,
    'invitation': '13inv-tion',
    'languages': '["en"]',
    'partner_sex': 'not_specified',
    'sex': 'not_specified',
    'telegram_id': 130,
    }
STRANGER1_1 = {
    'id': 11,
    'invitation': '11inv-tion',
    'invited_by_id': STRANGER1_1_INVITER['id'],
    'languages': '["en"]',
    'partner_sex': 'not_specified',
    'sex': 'not_specified',
    'telegram_id': 110,
    }
STRANGER1_2 = {
    'id': 12,
    'invitation': '12inv-tion',
    'languages': '["en"]',
    'partner_sex': 'not_specified',
    'sex': 'not_specified',
    'telegram_id': 120,
    }
TALK1 = {
    'id': 1,
    'partner1_id': STRANGER1_1['id'],
    'partner1_sent': 0,
    'partner2_id': STRANGER1_2['id'],
    'partner2_sent': 1,
    'searched_since': datetime.datetime(1970, 1, 1),
    }

def get_invitation_message(invitation=None, invitation_instance=None, invitation_json=None):
    if invitation_json is None:
        if invitation_instance is None:
            invitation_instance = {
                'i': invitation,
                }

        invitation_json = json.dumps(invitation_instance)

    invitation_code = str(
        base64.urlsafe_b64encode(invitation_json.encode('utf-8')),
        'utf-8',
        )
    LOGGER.debug('Invitation is %s, invitation code is %s', invitation, invitation_code)
    return f'/start {invitation_code}'

class TestInvites(asynctest.TestCase):
    @patch_telepot
    def setUp(self):
        run(self)

    def tearDown(self):
        finalize(self)

    async def test_stranger_was_rewarded_for_invite(self):
        setup_db({
            'strangers': [STRANGER1_1_INVITER, STRANGER1_1, STRANGER1_2],
            'talks': [TALK1],
            })
        receive_message(STRANGER1_1['telegram_id'], 'Hello')
        expected_bonuses_count = STRANGER1_1_INVITER['bonus_count'] + 1
        await assert_sent_message(STRANGER1_2['telegram_id'], 'Hello')
        await assert_sent_message(
            STRANGER1_1_INVITER['telegram_id'],
            '*Rand Talk:* You\'ve received one bonus for inviting a person to the bot. Bonuses'
            ' will help you to find partners quickly. Total bonuses count:'
            f' {expected_bonuses_count}. Congratulations! 🤑\n'
            'To mute this notifications, use /mute\\_bonuses.',
            )
        assert_db({
            'strangers': [
                {
                    'id': STRANGER1_1['id'],
                    'was_invited_as': STRANGER1_1['sex'],
                    },
                {
                    'id': STRANGER1_1_INVITER['id'],
                    'bonus_count': expected_bonuses_count,
                    },
                ],
            })

    async def skipped_test_muting_bonuses(self): # Stop skipping this test, it's useful!
        setup_db({
            'strangers': [STRANGER1_1_INVITER, STRANGER1_1, STRANGER1_2],
            'talks': [TALK1],
            })
        receive_message(STRANGER1_1_INVITER['telegram_id'], '/mute_bonuses')
        await assert_sent_message(
            STRANGER1_1_INVITER['telegram_id'],
            '*Rand Talk:* Notifications about bonuses were muted for 1 hour 🤐',
            )
        receive_message(STRANGER1_1['telegram_id'], 'Hello')
        await assert_sent_message(STRANGER1_2['telegram_id'], 'Hello')

    async def test_start_by_invitation(self):
        setup_db({
            'strangers': [STRANGER1_1_INVITER, STRANGER1_2],
            })
        receive_message(
            STRANGER1_2['telegram_id'],
            get_invitation_message(invitation=STRANGER1_1_INVITER['invitation']),
            )
        await assert_sent_message(
            STRANGER1_2['telegram_id'],
            '*Rand Talk:* *Manual*\n\n'
            'Use /begin to start looking for a conversational partner, once you\'re matched you'
            ' can use /end to finish the conversation.',
            )
        assert_db({
            'strangers': [
                {
                    'id': STRANGER1_2['id'],
                    'invited_by_id': STRANGER1_1_INVITER['id'],
                    },
                ],
            })

    async def test_start_by_invitation_repeatedly(self):
        setup_db({
            'strangers': [STRANGER1_1_INVITER, STRANGER1_1],
            })
        receive_message(
            STRANGER1_1['telegram_id'],
            get_invitation_message(invitation=STRANGER1_1_INVITER['invitation']),
            )
        await assert_sent_message(
            STRANGER1_1['telegram_id'],
            '*Rand Talk:* *Manual*\n\n'
            'Use /begin to start looking for a conversational partner, once you\'re matched you'
            ' can use /end to finish the conversation.',
            )
        assert_db({
            'strangers': [STRANGER1_1_INVITER, STRANGER1_1],
            })

    async def test_start_by_unknown_invitation(self):
        setup_db({
            'strangers': [STRANGER1_2],
            })
        receive_message(
            STRANGER1_2['telegram_id'],
            get_invitation_message(invitation=STRANGER1_1_INVITER['invitation']),
            )
        await assert_sent_message(
            STRANGER1_2['telegram_id'],
            '*Rand Talk:* *Manual*\n\n'
            'Use /begin to start looking for a conversational partner, once you\'re matched you'
            ' can use /end to finish the conversation.',
            )
        assert_db({
            'strangers': [STRANGER1_2],
            })

    async def test_start_by_wrong_invitation__invalid_instance(self):
        setup_db({
            'strangers': [STRANGER1_2],
            })
        receive_message(
            STRANGER1_2['telegram_id'],
            get_invitation_message(invitation_instance=1),
            )
        await assert_sent_message(
            STRANGER1_2['telegram_id'],
            '*Rand Talk:* *Manual*\n\n'
            'Use /begin to start looking for a conversational partner, once you\'re matched you'
            ' can use /end to finish the conversation.',
            )
        assert_db({
            'strangers': [STRANGER1_2],
            })

    async def test_start_by_wrong_invitation__invalid_dict_keys(self):
        setup_db({
            'strangers': [STRANGER1_2],
            })
        receive_message(
            STRANGER1_2['telegram_id'],
            get_invitation_message(
                invitation_instance={'foo': 'bar'},
                ),
            )
        await assert_sent_message(
            STRANGER1_2['telegram_id'],
            '*Rand Talk:* *Manual*\n\n'
            'Use /begin to start looking for a conversational partner, once you\'re matched you'
            ' can use /end to finish the conversation.',
            )
        assert_db({
            'strangers': [STRANGER1_2],
            })

    async def test_start_by_wrong_invitation__invalid_json(self):
        setup_db({
            'strangers': [STRANGER1_2],
            })
        receive_message(
            STRANGER1_2['telegram_id'],
            get_invitation_message(
                invitation_json='{\"foo\"',
                ),
            )
        await assert_sent_message(
            STRANGER1_2['telegram_id'],
            '*Rand Talk:* *Manual*\n\n'
            'Use /begin to start looking for a conversational partner, once you\'re matched you'
            ' can use /end to finish the conversation.',
            )
        assert_db({
            'strangers': [STRANGER1_2],
            })

    async def test_invite_himself(self):
        setup_db({
            'strangers': [STRANGER1_1_INVITER],
            })
        receive_message(
            STRANGER1_1_INVITER['telegram_id'],
            get_invitation_message(invitation=STRANGER1_1_INVITER['invitation']),
            )
        await assert_sent_message(
            STRANGER1_1_INVITER['telegram_id'],
            '*Rand Talk:* Don\'t try to fool me. 😉 Forward message with the link to your friends'
            ' and receive well-earned bonuses that will help you to find partner quickly.',
            )
        await assert_sent_message(
            STRANGER1_1_INVITER['telegram_id'],
            '*Rand Talk:* *Manual*\n\n'
            'Use /begin to start looking for a conversational partner, once you\'re matched you'
            ' can use /end to finish the conversation.',
            )
        assert_db({
            'strangers': [STRANGER1_1_INVITER],
            })

