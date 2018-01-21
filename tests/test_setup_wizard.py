# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2018 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import re
import asynctest
from telepot_testing import assert_sent_message, receive_message
from .helpers import assert_db, finalize, run, patch_telepot, setup_db

LOGGER = logging.getLogger('tests.test_setup_wizard')
STRANGER_LANGUAGES = {
    'id': 1,
    'invitation': '11_invitation',
    'languages': None,
    'partner_sex': None,
    'sex': None,
    'telegram_id': 110,
    'wizard': 'setup',
    'wizard_step': 'languages',
    }
STRANGER_SEX = {
    'id': 1,
    'invitation': '11_invitation',
    'languages': '["en"]',
    'partner_sex': None,
    'sex': None,
    'telegram_id': 110,
    'wizard': 'setup',
    'wizard_step': 'sex',
    }
STRANGER_PARTNER_SEX = {
    'id': 1,
    'invitation': '11_invitation',
    'languages': '["en"]',
    'partner_sex': None,
    'sex': 'female',
    'telegram_id': 110,
    'wizard': 'setup',
    'wizard_step': 'partner_sex',
    }

async def assert_language_prompt(
    stranger,
    message,
    leave_language_unchanged=False,
    leave_languages_unchanged=False,
    ):
    keyboard = [
        ['English', 'Русский'],
        ['فارسی', 'Italiano'],
        ['French', 'Deutsch'],
        ['Español', 'Português'],
        ]

    if leave_language_unchanged:
        keyboard.append(['Leave the language unchanged'])

    if leave_languages_unchanged:
        keyboard.append(['Leave the languages unchanged'])

    await assert_sent_message(
        stranger['telegram_id'],
        message,
        reply_markup={
            'keyboard': keyboard,
            'one_time_keyboard': True,
            },
        )
    expected_stranger = stranger.copy()
    expected_stranger.update({
        'wizard': 'setup',
        'wizard_step': 'languages',
        })
    assert_db({
        'strangers': [expected_stranger],
        })

async def assert_sex_prompt(stranger):
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

async def assert_partner_sex_prompt(telegram_id):
    await assert_sent_message(
        telegram_id,
        '*Rand Talk:* Choose your partner\'s sex',
        reply_markup={
            'keyboard': [
                ['Female', 'Male'],
                ['Not specified'],
                ],
            'one_time_keyboard': True,
            },
        )

async def assert_setup_finished(telegram_id):
    await assert_sent_message(
        telegram_id,
        '*Rand Talk:* Thanks for info. 😋 Use /begin to start looking for a'
        ' conversational partner, once you\'re matched you can use /end to'
        ' finish the conversation.',
        reply_markup={
            'hide_keyboard': True,
            },
        )

class TestSetupWizard(asynctest.TestCase):
    @patch_telepot
    def setUp(self):
        run(self)

    def tearDown(self):
        finalize(self)

    async def test_start(self):
        stranger = {
            'id': 1,
            'invitation': re.compile(r'\S{10}'),
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
        assert_db({
            'strangers': [stranger],
            })

    async def test_start__has_one_language(self):
        stranger = {
            'id': 1,
            'invitation': '11_invitation',
            'languages': '["en"]',
            'sex': 'male',
            'partner_sex': 'male',
            'telegram_id': 110,
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

    async def test_start__has_many_languages(self):
        stranger = {
            'id': 1,
            'invitation': '11_invitation',
            'languages': '["en", "fr"]',
            'sex': 'female',
            'partner_sex': 'female',
            'telegram_id': 110,
            }
        setup_db({
            'strangers': [stranger],
            })
        receive_message(stranger['telegram_id'], '/setup')
        await assert_language_prompt(
            stranger,
            '*Rand Talk:* Your current languages are: English, French. Enumerate the languages you'
            ' speak the same way, in descending order of your speaking convenience or just'
            ' pick one at special keyboard.',
            leave_languages_unchanged=True,
            )

    async def test_language(self):
        setup_db({
            'strangers': [STRANGER_LANGUAGES],
            })
        receive_message(STRANGER_LANGUAGES['telegram_id'], 'English')
        await assert_sex_prompt(STRANGER_LANGUAGES)
        assert_db({
            'strangers': [STRANGER_SEX],
            })

    async def test_language__unknown(self):
        setup_db({
            'strangers': [STRANGER_LANGUAGES],
            })
        receive_message(STRANGER_LANGUAGES['telegram_id'], 'Foobar')
        await assert_sent_message(
            STRANGER_LANGUAGES['telegram_id'],
            '*Rand Talk:* Language “Foobar” wasn\'t found. 😳 Try to specify language in English.',
            )
        await assert_language_prompt(
            STRANGER_LANGUAGES,
            '*Rand Talk:* Enumerate the languages you speak like this: “English,'
            ' Italian” — in descending order of your speaking convenience or just'
            ' pick one at special keyboard.',
            )

    async def test_language__too_much_languages(self):
        setup_db({
            'strangers': [STRANGER_LANGUAGES],
            })
        receive_message(STRANGER_LANGUAGES['telegram_id'], 'en, ru, fr, uk, it, de, pt')
        await assert_sent_message(
            STRANGER_LANGUAGES['telegram_id'],
            '*Rand Talk:* Too much languages were specified. Please shorten your list to 6'
            ' languages.',
            )
        await assert_language_prompt(
            STRANGER_LANGUAGES,
            '*Rand Talk:* Enumerate the languages you speak like this: “English,'
            ' Italian” — in descending order of your speaking convenience or just'
            ' pick one at special keyboard.',
            )

    async def test_language__no_languages(self):
        setup_db({
            'strangers': [STRANGER_LANGUAGES],
            })
        receive_message(STRANGER_LANGUAGES['telegram_id'], ',')
        await assert_sent_message(
            STRANGER_LANGUAGES['telegram_id'],
            '*Rand Talk:* Please specify at least one language',
            )
        await assert_language_prompt(
            STRANGER_LANGUAGES,
            '*Rand Talk:* Enumerate the languages you speak like this: “English,'
            ' Italian” — in descending order of your speaking convenience or just'
            ' pick one at special keyboard.',
            )

    async def test_sex(self):
        setup_db({
            'strangers': [STRANGER_SEX],
            })
        receive_message(STRANGER_SEX['telegram_id'], 'Female')
        await assert_partner_sex_prompt(STRANGER_SEX['telegram_id'])
        assert_db({
            'strangers': [STRANGER_PARTNER_SEX],
            })

    async def test_sex__not_specified(self):
        setup_db({
            'strangers': [STRANGER_SEX],
            })
        receive_message(STRANGER_SEX['telegram_id'], 'Not specified')
        await assert_setup_finished(STRANGER_SEX['telegram_id'])
        assert_db({
            'strangers': [
                {
                    'id': STRANGER_SEX['id'],
                    'sex': 'not_specified',
                    'partner_sex': 'not_specified',
                    'wizard': 'none',
                    'wizard_step': None,
                    },
                ],
            })

    async def test_sex__wrong_sex(self):
        setup_db({
            'strangers': [STRANGER_SEX],
            })
        receive_message(STRANGER_SEX['telegram_id'], 'foobar')
        await assert_sent_message(
            STRANGER_SEX['telegram_id'],
            '*Rand Talk:* Unknown sex: “foobar” — is not a valid sex name. Are you sure you'
            ' aren\'t mistaken? 😉',
            )
        await assert_sex_prompt(STRANGER_SEX)
        assert_db({
            'strangers': [STRANGER_SEX],
            })

    async def test_partners_sex(self):
        setup_db({
            'strangers': [STRANGER_PARTNER_SEX],
            })
        receive_message(STRANGER_PARTNER_SEX['telegram_id'], 'Male')
        await assert_setup_finished(STRANGER_PARTNER_SEX['telegram_id'])
        assert_db({
            'strangers': [
                {
                    'id': STRANGER_PARTNER_SEX['id'],
                    'partner_sex': 'male',
                    'wizard': 'none',
                    'wizard_step': None,
                    },
                ],
            })

    async def test_partners_sex__wrong_sex(self):
        setup_db({
            'strangers': [STRANGER_PARTNER_SEX],
            })
        receive_message(STRANGER_PARTNER_SEX['telegram_id'], 'foobar')
        await assert_sent_message(
            STRANGER_SEX['telegram_id'],
            '*Rand Talk:* Unknown sex: “foobar” — is not a valid sex name. Are you sure you'
            ' aren\'t mistaken? 😉',
            )
        await assert_partner_sex_prompt(STRANGER_PARTNER_SEX['telegram_id'])
        assert_db({
            'strangers': [STRANGER_PARTNER_SEX],
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

    async def test_finish_setup__stranger_wasnt_filled(self):
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
        receive_message(stranger['telegram_id'], '/begin')
        await assert_sent_message(
            stranger['telegram_id'],
            '*Rand Talk:* Finish setup process please. After that you can start using bot.',
            )
        await assert_sent_message(
            stranger['telegram_id'],
            '*Rand Talk:* Set up your sex. If you pick “Not Specified” you can\'t choose your'
            ' partner\'s sex.',
            reply_markup = {
                'keyboard': [
                    ['Female', 'Male'],
                    ['Not specified'],
                    ],
                'one_time_keyboard': True,
                },
            )
        assert_db({
            'strangers': [stranger],
            })

    async def test_finish_setup__filled_stranger(self):
        stranger = {
            'id': 1,
            'invitation': '11_invitation',
            'languages': '["en"]',
            'partner_sex': 'male',
            'sex': 'female',
            'telegram_id': 110,
            'wizard': 'setup',
            'wizard_step': 'sex',
            }
        setup_db({
            'strangers': [stranger],
            })
        receive_message(stranger['telegram_id'], '/end')
        await assert_sent_message(
            stranger['telegram_id'],
            '*Rand Talk:* Thanks for info. 😋 Use /begin to start looking for a conversational partner, once you\'re matched you can use /end to finish the conversation.',
            reply_markup={
                'hide_keyboard': True,
                },
            )
        assert_db({
            'strangers': [
                {
                    'id': stranger['id'],
                    'wizard': 'none',
                    'wizard_step': None,
                    },
                ]
            })
