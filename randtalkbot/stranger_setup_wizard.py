# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
import re
import sys
import telepot
from .errors import EmptyLanguagesError, MissingPartnerError, SexError, StrangerError
from .i18n import get_languages_codes, get_languages_names, LanguageNotFoundError, \
    SUPPORTED_LANGUAGES_NAMES
from .stranger import SEX_NAMES
from .stranger_sender_service import StrangerSenderService
from .wizard import Wizard
from telepot import TelegramError

def _(s): return s

LOGGER = logging.getLogger('randtalkbot.stranger_setup_wizard')
SEX_KEYBOARD = {
    'keyboard': [SEX_NAMES[:2], SEX_NAMES[2:], ],
    }

class StrangerSetupWizard(Wizard):
    '''
    Wizard which guides stranger through process of customizing her parameters. Activates
    automatically for novices.
    '''

    def __init__(self, stranger):
        super(StrangerSetupWizard, self).__init__()
        self._stranger = stranger
        self._sender = StrangerSenderService.get_instance().get_or_create_stranger_sender(stranger)

    async def activate(self):
        self._stranger.wizard = 'setup'
        self._stranger.wizard_step = 'languages'
        self._stranger.save()
        await self._prompt()

    async def deactivate(self):
        self._stranger.wizard = 'none'
        self._stranger.wizard_step = None
        self._stranger.save()
        try:
            await self._sender.send_notification(
                _('Thank you. Use /begin to start looking for a conversational partner, '
                    'once you\'re matched you can use /end to end the conversation.'),
                reply_markup={'hide_keyboard': True},
                )
        except TelegramError as e:
            LOGGER.warning('Deactivate. Can\'t notify stranger. %s', e)

    async def handle(self, message):
        '''
        @returns `True` if message was interpreted in this method. `False` if message still needs
            interpretation.
        '''
        if self._stranger.wizard == 'none': # Wizard isn't active. Check if we should activate it.
            if self._stranger.is_novice():
                await self.activate()
                return True
            else:
                return False
        elif self._stranger.wizard != 'setup':
            return False
        try:
            if self._stranger.wizard_step == 'languages':
                try:
                    self._stranger.set_languages(get_languages_codes(message.text))
                except EmptyLanguagesError as e:
                    await self._sender.send_notification(
                        _('Please specify at least one language.'),
                        )
                except LanguageNotFoundError as e:
                    LOGGER.info('Languages weren\'t parsed: \"%s\"', message.text)
                    await self._sender.send_notification(_('Language \"{0}\" wasn\'t found.'), e.name)
                except StrangerError as e:
                    LOGGER.info('Too much languages were specified: \"%s\"', message.text)
                    await self._sender.send_notification(
                        _('Too much languages were specified. Please shorten your list to 6 languages.'),
                        )
                else:
                    self._sender.update_translation()
                    self._stranger.wizard_step = 'sex'
                    self._stranger.save()
                await self._prompt()
            elif self._stranger.wizard_step == 'sex':
                try:
                    self._stranger.set_sex(message.text)
                except SexError as e:
                    LOGGER.info('Stranger\'s sex wasn\'t parsed: \"%s\"', message.text)
                    await self._sender.send_notification(
                        _('Unknown sex: \"{0}\" -- is not a valid sex name.'),
                        e.name,
                        )
                    await self._prompt()
                else:
                    if self._stranger.sex == 'not_specified':
                        self._stranger.partner_sex = 'not_specified'
                        # Calls Stranger.save() inside.
                        await self.deactivate()
                    else:
                        self._stranger.wizard_step = 'partner_sex'
                        self._stranger.save()
                        await self._prompt()
            elif self._stranger.wizard_step == 'partner_sex':
                try:
                    self._stranger.set_partner_sex(message.text)
                except SexError as e:
                    LOGGER.info('Stranger partner\'s sex wasn\'t parsed: \"%s\"', message.text)
                    await self._sender.send_notification(
                        _('Unknown sex: \"{0}\" -- is not a valid sex name.'),
                        e.name,
                        )
                    await self._prompt()
                else:
                    # Calls Stranger.save() inside.
                    await self.deactivate()
            else:
                LOGGER.warning(
                    'Undknown wizard_step value was found: \"%s\"',
                    self._stranger.wizard_step,
                )
        except TelegramError as e:
            LOGGER.warning('handle() Can not notify stranger. %s', e)
        return True

    async def handle_command(self, message):
        '''
        @returns `True` if command was interpreted in this method. `False` if command still needs
            interpretation.
        '''
        if self._stranger.wizard == 'none':
            # Wizard isn't active. Check if we should activate it.
            return (await self.handle(message)) and message.command != 'start'
        elif self._stranger.is_full():
            if self._stranger.wizard == 'setup':
                await self.deactivate()
            return False
        else:
            try:
                await self._sender.send_notification(
                    _('Finish setup process please. After that you can start using bot.'),
                    )
            except TelegramError as e:
                LOGGER.warning('Handle command. Cant notify stranger. %s', e)
            await self._prompt()
            return True

    async def _prompt(self):
        wizard_step = self._stranger.wizard_step
        try:
            if wizard_step == 'languages':
                languages = self._stranger.get_languages()
                # Just split languages by pairs.
                keyboard = \
                    [SUPPORTED_LANGUAGES_NAMES[i: i + 2] for i in range(0, len(SUPPORTED_LANGUAGES_NAMES), 2)]
                try:
                    languages_enumeration = get_languages_names(languages)
                except LanguageNotFoundError:
                    LOGGER.error('Language not found at setup wizard: %s', self._stranger.languages)
                    languages_enumeration = ''
                if len(languages) == 0 or not languages_enumeration:
                    prompt = _('Enumerate the languages you speak like this: \"English, Italian\" '
                        '-- in descending order of your speaking convenience or just pick one '
                        'at special keyboard.')
                else:
                    if len(languages) == 1:
                        keyboard.append([_('Leave the language unchanged')])
                        prompt = _('Your current language is {0}. Enumerate the languages '
                            'you speak like this: \"English, Italian\" -- in descending order '
                            'of your speaking convenience or just pick one at special keyboard.')
                    else:
                        keyboard.append([_('Leave the languages unchanged')])
                        prompt = _('Your current languages are: {0}. Enumerate the languages you '
                            'speak the same way -- in descending order of your speaking '
                            'convenience or just pick one at special keyboard.')
                await self._sender.send_notification(
                    prompt,
                    languages_enumeration,
                    reply_markup={
                        'keyboard': keyboard,
                        },
                    )
            elif wizard_step == 'sex':
                await self._sender.send_notification(
                    _('Set up your sex. If you pick \"Not Specified\" you can\'t choose '
                        'your partner\'s sex.'),
                    reply_markup=SEX_KEYBOARD,
                    )
            elif wizard_step == 'partner_sex':
                await self._sender.send_notification(
                    _('Choose your partner\'s sex'),
                    reply_markup=SEX_KEYBOARD,
                    )
        except TelegramError as e:
            LOGGER.warning('_prompt() Can not notify stranger. %s', e)
