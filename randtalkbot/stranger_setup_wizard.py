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
from .i18n import get_languages_codes, LanguageNotFoundError, SUPPORTED_LANGUAGES_NAMES
from .stranger import MissingPartnerError, SexError, SEX_NAMES
from .stranger_sender_service import StrangerSenderService
from .wizard import Wizard

SEX_KEYBOARD = {
    'keyboard': [SEX_NAMES[:2], SEX_NAMES[2:], ],
    }

class StrangerSetupWizard(Wizard):
    '''
    Wizard which guides user through process of customizing his parameters. Activates automatically for
    novices.
    '''

    def __init__(self, stranger):
        super(StrangerSetupWizard, self).__init__()
        self._stranger = stranger
        self._sender = StrangerSenderService.get_instance() \
            .get_or_create_stranger_sender(stranger.telegram_id)

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
            'Thank you. Use /begin to start looking for a conversational partner, ' + \
                'once you\'re matched you can use /end to end the conversation.',
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
        if self._stranger.wizard_step == 'languages':
            try:
                self._stranger.set_languages(get_languages_codes(text))
            except LanguageNotFoundError as e:
                yield from self._sender.send_notification(str(e))
            else:
                self._stranger.wizard_step = 'sex'
                self._stranger.save()
            yield from self._send_invitation()
        elif self._stranger.wizard_step == 'sex':
            try:
                self._stranger.set_sex(text)
            except SexError as e:
                yield from self._sender.send_notification(str(e))
            else:
                if self._stranger.sex == 'not_specified':
                    self._stranger.partner_sex = 'not_specified'
                    self.deactivate()
                else:
                    self._stranger.wizard_step = 'partner_sex'
                    self._stranger.save()
            yield from self._send_invitation()
        elif self._stranger.wizard_step == 'partner_sex':
            try:
                self._stranger.set_partner_sex(text)
            except SexError as e:
                yield from self._sender.send_notification(str(e))
            else:
                self.deactivate()
            yield from self._send_invitation()
        else:
            logging.warning('Undknown wizard_step value was found: \"%s\"', self._stranger.wizard_step)
        return True

    @asyncio.coroutine
    def _send_invitation(self):
        wizard_step = self._stranger.wizard_step
        if wizard_step == 'languages':
            yield from self._sender.send_notification(
                'Enumerate the languages you speak like this: \"English, Italian\" -- ' + \
                    'in order of your speaking convenience or just pick one at special keyboard.',
                reply_markup={
                    'keyboard': [SUPPORTED_LANGUAGES_NAMES[:2], SUPPORTED_LANGUAGES_NAMES[2:], ],
                    },
                )
        elif wizard_step == 'sex':
            yield from self._sender.send_notification(
                'Set up your sex. If you pick \"Not Specified\" you can\'t choose ' + \
                    'your partner\'s sex.',
                reply_markup=SEX_KEYBOARD,
                )
        elif wizard_step == 'partner_sex':
            yield from self._sender.send_notification(
                'Choose your partner\'s sex',
                reply_markup=SEX_KEYBOARD,
                )
