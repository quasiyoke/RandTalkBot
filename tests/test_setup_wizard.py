# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2018 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import asynctest
from telepot_testing import assert_sent_message, receive_message
from .helpers import assert_db, finalize, run, patch_telepot, setup_db

LOGGER = logging.getLogger('tests.test_setup_wizard')

async def assert_language_prompt(stranger, message, leave_language_unchanged=False):
    keyboard = [
        ['English', 'Русский'],
        ['فارسی', 'Italiano'],
        ['French', 'Deutsch'],
        ['Español', 'Português']
        ]

    if leave_language_unchanged:
        keyboard.append(['Leave the language unchanged'])

    await assert_sent_message(
        stranger['telegram_id'],
        message,
        reply_markup={
            'keyboard': keyboard,
            'one_time_keyboard': True,
            },
        )
    stranger.update({
        'wizard': 'setup',
        'wizard_step': 'languages',
        })
    assert_db({
        'strangers': [stranger],
        })

class TestSetupWizard(asynctest.TestCase):
    @patch_telepot
    def setUp(self):
        run(self)

    def tearDown(self):
        finalize(self)

    async def test_first_message(self):
        stranger = {
            'id': 1,
            'languages': None,
            'sex': None,
            'partner_sex': None,
            'telegram_id': 110,
            }
        receive_message(stranger['telegram_id'], '/start')
        await assert_language_prompt(
            stranger,
            '*Rand Talk:* Enumerate the languages you speak like this: “English,'
            ' Italian” — in descending order of your speaking convenience or just'
            ' pick one at special keyboard.',
            )

    async def test_language(self):
        stranger = {
            'id': 1,
            'invitation': '11_invitation',
            'languages': None,
            'partner_sex': None,
            'sex': None,
            'telegram_id': 110,
            'wizard': 'setup',
            'wizard_step': 'languages',
            }
        setup_db({
            'strangers': [stranger],
            })
        receive_message(stranger['telegram_id'], 'English')
        await assert_sent_message(
            stranger['telegram_id'],
            '*Rand Talk:* Set up your sex. If you pick “Not Specified” you can\'t'
            ' choose your partner\'s sex.',
            reply_markup={
                'keyboard': [
                    ['Female', 'Male'],
                    ['Not specified'],
                    ],
                'one_time_keyboard': True,
                },
            )
        assert_db({
            'strangers': [
                {
                    'id': stranger['id'],
                    'languages': '["en"]',
                    'wizard_step': 'sex',
                    },
                ],
            })

    async def test_sex(self):
        stranger = {
            'id': 1,
            'invitation': '11_invitation',
            'languages': '["en"]',
            'partner_sex': None,
            'sex': None,
            'telegram_id': 110,
            'wizard': 'setup',
            'wizard_step': 'sex',
            }
        setup_db({
            'strangers': [stranger],
            })
        receive_message(stranger['telegram_id'], 'Female')
        await assert_sent_message(
            stranger['telegram_id'],
            '*Rand Talk:* Choose your partner\'s sex',
            reply_markup={
                'keyboard': [
                    ['Female', 'Male'],
                    ['Not specified'],
                    ],
                'one_time_keyboard': True,
                },
            )
        assert_db({
            'strangers': [
                {
                    'id': stranger['id'],
                    'sex': 'female',
                    'wizard_step': 'partner_sex',
                    },
                ],
            })

    async def test_partners_sex(self):
        stranger = {
            'id': 1,
            'invitation': '11_invitation',
            'languages': '["en"]',
            'partner_sex': None,
            'sex': 'female',
            'telegram_id': 110,
            'wizard': 'setup',
            'wizard_step': 'partner_sex',
            }
        setup_db({
            'strangers': [stranger],
            })
        receive_message(stranger['telegram_id'], 'Male')
        await assert_sent_message(
            stranger['telegram_id'],
            '*Rand Talk:* Thanks for info. 😋 Use /begin to start looking for a'
            ' conversational partner, once you\'re matched you can use /end to'
            ' finish the conversation.',
            reply_markup={
                'hide_keyboard': True,
                },
            )
        assert_db({
            'strangers': [
                {
                    'id': stranger['id'],
                    'partner_sex': 'male',
                    'wizard': 'none',
                    'wizard_step': None,
                    },
                ],
            })

    async def test_restart_setup(self):
        stranger = {
            'id': 1,
            'invitation': '11_invitation',
            'languages': '["en"]',
            'partner_sex': 'male',
            'sex': 'female',
            'telegram_id': 110,
            'wizard': 'none',
            'wizard_step': None,
            }
        setup_db({
            'strangers': [stranger],
            })
        receive_message(stranger['telegram_id'], '/setup')
        await assert_language_prompt(
            stranger,
            '*Rand Talk:* Your current language is English. Enumerate the languages you speak like'
            ' this: “English, Italian” — in descending order of your speaking convenience or just'
            ' pick one at special keyboard.',
            leave_language_unchanged=True,
            )
