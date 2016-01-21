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
from .i18n import get_languages_codes, get_languages_names, LanguageNotFoundError, \
    SUPPORTED_LANGUAGES_NAMES
from .stranger import EmptyLanguagesError, MissingPartnerError, SexError, SEX_NAMES
from .stranger_sender_service import StrangerSenderService
from .wizard import Wizard

def _(s): return s

LOGGER = logging.getLogger('randtalkbot')
SEX_KEYBOARD = {
    'keyboard': [SEX_NAMES[:2], SEX_NAMES[2:], ],
    }

class InvalidCommandError(Exception):
    pass

class StrangerSetupWizard(Wizard):
    '''
    Wizard which guides stranger through process of customizing her parameters. Activates
    automatically for novices.
    '''
    COMMAND_RE_PATTERN = re.compile('^/(\w+)\\b')

    def __init__(self, stranger):
        super(StrangerSetupWizard, self).__init__()
        self._stranger = stranger
        self._sender = StrangerSenderService.get_instance() \
            .get_or_create_stranger_sender(stranger)

    @classmethod
    def _get_command(cls, message):
        command_match = cls.COMMAND_RE_PATTERN.match(message)
        if not command_match:
            raise InvalidCommandError()
        return command_match.group(1)

    @asyncio.coroutine
    def activate(self):
        self._stranger.wizard = 'setup'
        self._stranger.wizard_step = 'languages'
        self._stranger.save()
        yield from self._send_invitation()

    @asyncio.coroutine
    def deactivate(self):
        self._stranger.wizard = 'none'
        self._stranger.wizard_step = None
        self._stranger.save()
        yield from self._sender.send_notification(
            _('Thank you. Use /begin to start looking for a conversational partner, '
                'once you\'re matched you can use /end to end the conversation.'),
            reply_markup={'hide_keyboard': True},
            )

    @asyncio.coroutine
    def handle(self, text):
        '''
        @returns `True` if message was interpreted in this method. `False` if message still needs
            interpretation.
        '''
        if self._stranger.wizard == 'none': # Wizard isn't active. Check if we should activate it.
            if self._stranger.is_novice():
                yield from self.activate()
                return True
            else:
                return False
        elif self._stranger.wizard != 'setup':
            return False
        try:
            command = type(self)._get_command(text)
        except InvalidCommandError:
            pass
        else:
            if not self._stranger.is_full():
                yield from self._sender.send_notification(
                    _('Finish setup process please. After that you can start using bot.'),
                    )
                yield from self._send_invitation()
                return True
            elif command == 'cancel':
                yield from self.deactivate()
                return True
            elif command != 'start':
                yield from self._sender.send_notification(
                    _('To interrupt setup use /cancel.'),
                    )
                yield from self._send_invitation()
                return True
        if self._stranger.wizard_step == 'languages':
            try:
                self._stranger.set_languages(get_languages_codes(text))
            except LanguageNotFoundError as e:
                LOGGER.info('Languages weren\'t parsed: \"%s\"', text)
                yield from self._sender.send_notification(
                    _('Language \"{0}\" wasn\'t found.'),
                    e.name,
                    )
            except EmptyLanguagesError as e:
                yield from self._sender.send_notification(
                    _('Please specify at least one language.'),
                    )
            else:
                self._sender.update_translation()
                self._stranger.wizard_step = 'sex'
                self._stranger.save()
            yield from self._send_invitation()
        elif self._stranger.wizard_step == 'sex':
            try:
                self._stranger.set_sex(text)
            except SexError as e:
                LOGGER.info('Stranger\'s sex wasn\'t parsed: \"%s\"', text)
                yield from self._sender.send_notification(
                    _('Unknown sex: \"{0}\" -- is not a valid sex name.'),
                    e.name,
                    )
                yield from self._send_invitation()
            else:
                if self._stranger.sex == 'not_specified':
                    self._stranger.partner_sex = 'not_specified'
                    yield from self.deactivate()
                else:
                    self._stranger.wizard_step = 'partner_sex'
                    self._stranger.save()
                    yield from self._send_invitation()
        elif self._stranger.wizard_step == 'partner_sex':
            try:
                self._stranger.set_partner_sex(text)
            except SexError as e:
                LOGGER.info('Stranger partner\'s sex wasn\'t parsed: \"%s\"', text)
                yield from self._sender.send_notification(
                    _('Unknown sex: \"{0}\" -- is not a valid sex name.'),
                    e.name,
                    )
                yield from self._send_invitation()
            else:
                yield from self.deactivate()
        else:
            LOGGER.warning(
                'Undknown wizard_step value was found: \"%s\"',
                self._stranger.wizard_step,
                )
        return True

    @asyncio.coroutine
    def _send_invitation(self):
        wizard_step = self._stranger.wizard_step
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
                notification = _('Enumerate the languages you speak like this: \"English, Italian\" '
                    '-- in descending order of your speaking convenience or just pick one '
                    'at special keyboard.')
            else:
                if len(languages) == 1:
                    keyboard.append([_('Leave the language unchanged')])
                    notification = _('Your current language is {0}. Enumerate the languages '
                        'you speak like this: \"English, Italian\" -- in descending order '
                        'of your speaking convenience or just pick one at special keyboard.')
                else:
                    keyboard.append([_('Leave the languages unchanged')])
                    notification = _('Your current languages are: {0}. Enumerate the languages you '
                        'speak the same way -- in descending order of your speaking '
                        'convenience or just pick one at special keyboard.')
            yield from self._sender.send_notification(
                notification,
                languages_enumeration,
                reply_markup={
                    'keyboard': keyboard,
                    },
                )
        elif wizard_step == 'sex':
            yield from self._sender.send_notification(
                _('Set up your sex. If you pick \"Not Specified\" you can\'t choose '
                    'your partner\'s sex.'),
                reply_markup=SEX_KEYBOARD,
                )
        elif wizard_step == 'partner_sex':
            yield from self._sender.send_notification(
                _('Choose your partner\'s sex'),
                reply_markup=SEX_KEYBOARD,
                )
