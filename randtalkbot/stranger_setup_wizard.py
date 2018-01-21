# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from telepot.exception import TelegramError
from .errors import EmptyLanguagesError, SexError, StrangerError
from .i18n import get_languages_codes, get_languages_names, LanguageNotFoundError, \
    SUPPORTED_LANGUAGES_NAMES
from .stranger import SEX_NAMES
from .stranger_sender_service import StrangerSenderService
from .stranger_service import StrangerService
from .wizard import Wizard

def _(string_instance):
    return string_instance

LOGGER = logging.getLogger('randtalkbot.stranger_setup_wizard')
SEX_KEYBOARD = {
    'keyboard': [SEX_NAMES[:2], SEX_NAMES[2:], ],
    }

class StrangerSetupWizard(Wizard):
    """Wizard which guides stranger through process of customizing her parameters. Activates
    automatically for novices.
    """

    def __init__(self, stranger_id):
        super(StrangerSetupWizard, self).__init__()
        self._stranger_id = stranger_id

    async def activate(self):
        stranger = self._get_stranger()
        stranger.wizard = 'setup'
        stranger.wizard_step = 'languages'
        stranger.save()
        LOGGER.debug(
            'Stranger %d was activated',
            self._stranger_id,
            )
        await self._prompt()

    async def deactivate(self):
        stranger = self._get_stranger()
        stranger.wizard = 'none'
        stranger.wizard_step = None
        stranger.save()

        try:
            await self._get_sender() \
                .send_notification(
                    _(
                        'Thank you. Use /begin to start looking for a conversational partner,'
                        ' once you\'re matched you can use /end to end the conversation.',
                        ),
                    reply_markup={'hide_keyboard': True},
                    )
        except TelegramError as err:
            LOGGER.warning('Deactivate. Can\'t notify stranger. %s', err)

    def _get_sender(self):
        return StrangerSenderService.get_instance() \
            .get_stranger_sender(self._stranger_id)

    def _get_stranger(self):
        return StrangerService.get_instance() \
            .get_stranger_by_id(self._stranger_id)

    async def handle(self, message):
        """Returns:
            bool: `True` if message was interpreted in this method. `False` if message still needs
                interpretation.
        """
        stranger = self._get_stranger()

        if stranger.wizard == 'none': # Wizard isn't active. Check if we should activate it.
            if stranger.is_novice():
                await self.activate()
                return True

            return False
        elif stranger.wizard != 'setup':
            return False

        try:
            if stranger.wizard_step == 'languages':
                try:
                    stranger.set_languages(get_languages_codes(message.text))
                except EmptyLanguagesError as err:
                    await self._get_sender() \
                        .send_notification(
                            _('Please specify at least one language.'),
                            )
                except LanguageNotFoundError as err:
                    LOGGER.info('Languages weren\'t parsed: \"%s\"', message.text)
                    await self._get_sender() \
                        .send_notification(
                            _('Language \"{0}\" wasn\'t found.'),
                            err.name,
                            )
                except StrangerError:
                    LOGGER.info('Too much languages were specified: \"%s\"', message.text)
                    await self._get_sender() \
                        .send_notification(
                            _(
                                'Too much languages were specified. Please shorten your list'
                                ' to 6 languages.',
                                ),
                            )
                else:
                    self._get_sender() \
                        .update_translation()
                    stranger.wizard_step = 'sex'
                    stranger.save()

                await self._prompt()
            elif stranger.wizard_step == 'sex':
                try:
                    stranger.set_sex(message.text)
                except SexError as err:
                    LOGGER.info('Stranger\'s sex wasn\'t parsed: \"%s\"', message.text)
                    await self._get_sender() \
                        .send_notification(
                            _('Unknown sex: \"{0}\" -- is not a valid sex name.'),
                            err.name,
                            )
                    await self._prompt()
                else:
                    if stranger.sex == 'not_specified':
                        stranger.partner_sex = 'not_specified'
                        stranger.save()
                        await self.deactivate()
                    else:
                        stranger.wizard_step = 'partner_sex'
                        stranger.save()
                        await self._prompt()
            elif stranger.wizard_step == 'partner_sex':
                try:
                    stranger.set_partner_sex(message.text)
                except SexError as err:
                    LOGGER.info('Stranger partner\'s sex wasn\'t parsed: \"%s\"', message.text)
                    await self._get_sender() \
                        .send_notification(
                            _('Unknown sex: \"{0}\" -- is not a valid sex name.'),
                            err.name,
                            )
                    await self._prompt()
                else:
                    stranger.save()
                    await self.deactivate()
            else:
                LOGGER.warning(
                    'Undknown wizard_step value was found: \"%s\"',
                    stranger.wizard_step,
                )
        except TelegramError as err:
            LOGGER.warning('handle() Can not notify stranger. %s', err)

        return True

    async def handle_command(self, message):
        """Returns:
            bool: `True` if command was interpreted in this method. `False` if command still needs
                interpretation.
        """
        stranger = self._get_stranger()

        if stranger.wizard == 'none':
            # Wizard isn't active. Check if we should activate it.
            return (await self.handle(message)) and message.command != 'start'
        elif stranger.is_full():
            if stranger.wizard == 'setup':
                await self.deactivate()
            return False
        else:
            try:
                await self._get_sender() \
                    .send_notification(
                        _('Finish setup process please. After that you can start using bot.'),
                        )
            except TelegramError as err:
                LOGGER.warning('Handle command. Cant notify stranger. %s', err)
            await self._prompt()
            return True

    async def _prompt(self):
        stranger = self._get_stranger()
        wizard_step = stranger.wizard_step

        try:
            if wizard_step == 'languages':
                languages = stranger.get_languages()
                # Just split languages by pairs.
                keyboard = [
                    SUPPORTED_LANGUAGES_NAMES[i: i + 2]
                    for i in range(0, len(SUPPORTED_LANGUAGES_NAMES), 2)
                    ]

                try:
                    languages_enumeration = get_languages_names(languages)
                except LanguageNotFoundError:
                    LOGGER.error('Language not found at setup wizard: %s', stranger.languages)
                    languages_enumeration = ''

                if languages and languages_enumeration:
                    if len(languages) == 1:
                        keyboard.append([_('Leave the language unchanged')])
                        prompt = _(
                            'Your current language is {0}. Enumerate the languages'
                            ' you speak like this: \"English, Italian\" -- in descending order'
                            ' of your speaking convenience or just pick one at special keyboard.',
                            )
                    else:
                        keyboard.append([_('Leave the languages unchanged')])
                        prompt = _(
                            'Your current languages are: {0}. Enumerate the languages you'
                            ' speak the same way -- in descending order of your speaking'
                            ' convenience or just pick one at special keyboard.',
                            )
                else:
                    prompt = _(
                        'Enumerate the languages you speak like this: \"English, Italian\"'
                        ' -- in descending order of your speaking convenience or just pick one'
                        ' at special keyboard.'
                        )

                LOGGER.debug(
                    'Sending languages setup notification `%s`. Keyboard: %s',
                    prompt,
                    keyboard,
                    )
                await self._get_sender() \
                    .send_notification(
                        prompt,
                        languages_enumeration,
                        reply_markup={
                            'keyboard': keyboard,
                            },
                        )
            elif wizard_step == 'sex':
                await self._get_sender() \
                    .send_notification(
                        _(
                            'Set up your sex. If you pick \"Not Specified\" you can\'t choose'
                            ' your partner\'s sex.',
                            ),
                        reply_markup=SEX_KEYBOARD,
                        )
            elif wizard_step == 'partner_sex':
                await self._get_sender() \
                    .send_notification(
                        _('Choose your partner\'s sex'),
                        reply_markup=SEX_KEYBOARD,
                        )
            else:
                LOGGER.warning(
                    'Unknown wizard step: `%s` for stranger %d',
                    wizard_step,
                    self._stranger_id,
                    )
        except TelegramError as err:
            LOGGER.warning('_prompt() Can\'t notify stranger. %s', err)
