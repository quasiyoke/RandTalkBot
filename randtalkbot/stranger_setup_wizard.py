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

SEX_KEYBOARD = {
    'keyboard': [SEX_NAMES[:2], SEX_NAMES[2:], ],
    }

class StrangerSetupWizard:
    def __init__(self, stranger, sender):
        self._stranger = stranger
        self._sender = sender

    @asyncio.coroutine
    def activate(self):
        self._stranger.wizard_mode = 'setup_full'
        self._stranger.wizard_step = 'languages'
        yield from self._send_invitation()
        self._stranger.save()

    @asyncio.coroutine
    def deactivate(self):
        self._stranger.wizard_mode = 'none'
        self._stranger.wizard_step = None
        self._stranger.save()

    def _ensure_stranger_is_full(self):
        if self._stranger.languages is None:
            self._stranger.wizard_mode = 'setup_missing'
            self._stranger.wizard_step = 'languages'
            return False
        elif self._stranger.sex is None:
            self._stranger.wizard_mode = 'setup_missing'
            self._stranger.wizard_step = 'sex'
            return False
        elif self._stranger.partner_sex is None:
            self._stranger.wizard_mode = 'setup_missing'
            self._stranger.wizard_step = 'partner_sex'
            return False
        else:
            self._stranger.wizard_mode = 'none'
            if self._stranger.wizard_step:
                self._stranger.wizard_step = 'stop'
            return True

    @asyncio.coroutine
    def _setup_languages(self, languages):
        try:
            self._stranger.set_languages(get_languages_codes(languages))
        except LanguageNotFoundError as e:
            print(str(e))
            yield from self._sender.send_notification(str(e))
            return False
        return True

    @asyncio.coroutine
    def _setup_sex(self, sex):
        try:
            self._stranger.set_sex(sex)
        except SexError as e:
            yield from self._sender.send_notification(str(e))
            return False
        return True

    @asyncio.coroutine
    def _setup_partner_sex(self, sex):
        try:
            self._stranger.set_partner_sex(sex)
        except SexError as e:
            yield from self._sender.send_notification(str(e))
            return False
        return True

    @asyncio.coroutine
    def handle(self, text):
        '''
        @returns `True` if message was interpreted in this method. `False` if message still needs
            interpretation.
        '''
        if self._stranger.wizard_mode == 'none':
            if self._ensure_stranger_is_full():
                return False
            if self._stranger.is_empty():
                yield from self.activate()
                return True
            else: # If only a few Stranger's fields aren't set up.
                yield from self._send_invitation(missing=True)
                self._stranger.save()
                return True
        if self._stranger.wizard_mode != 'setup_full' and self._stranger.wizard_mode != 'setup_missing':
            return False
        if self._stranger.wizard_step == 'languages':
            if self._stranger.wizard_mode == 'setup_full':
                if (yield from self._setup_languages(text)):
                    self._stranger.wizard_step = 'sex'
                yield from self._send_invitation()
            elif self._stranger.wizard_mode == 'setup_missing':
                if (yield from self._setup_languages(text)):
                    self._ensure_stranger_is_full()
                    yield from self._send_invitation(missing=True)
                else:
                    yield from self._send_invitation()
        elif self._stranger.wizard_step == 'sex':
            if self._stranger.wizard_mode == 'setup_full':
                if (yield from self._setup_sex(text)):
                    if self._stranger.sex == 'not_specified':
                        self._stranger.partner_sex = 'not_specified'
                        self._stranger.wizard_step = 'stop'
                    else:
                        self._stranger.wizard_step = 'partner_sex'
                yield from self._send_invitation()
            elif self._stranger.wizard_mode == 'setup_missing':
                if (yield from self._setup_sex(text)):
                    if self._stranger.sex == 'not_specified':
                        self._stranger.partner_sex = 'not_specified'
                    self._ensure_stranger_is_full()
                    yield from self._send_invitation(missing=True)
                else:
                    yield from self._send_invitation()
        elif self._stranger.wizard_step == 'partner_sex':
            if self._stranger.wizard_mode == 'setup_full':
                if (yield from self._setup_partner_sex(text)):
                    self._stranger.wizard_step = 'stop'
                yield from self._send_invitation()
            elif self._stranger.wizard_mode == 'setup_missing':
                if (yield from self._setup_partner_sex(text)):
                    self._ensure_stranger_is_full()
                    yield from self._send_invitation(missing=True)
                else:
                    yield from self._send_invitation()
        else:
            return False
        self._stranger.save()
        return True

    @asyncio.coroutine
    def _send_invitation(self, missing=False):
        wizard_step = self._stranger.wizard_step
        if wizard_step == 'languages':
            if missing:
                invitation = 'To continue chatting you need to specify languages you speak. ' + \
                    'Enumerate them like this: \"English, Italian\" -- in order of your speaking ' + \
                    'convenience or just pick one at special keyboard.'
            else:
                invitation = 'Enumerate the languages you speak like this: \"English, Italian\" -- ' + \
                    'in order of your speaking convenience or just pick one at special keyboard.'
            yield from self._sender.send_notification(
                invitation,
                reply_markup={
                    'keyboard': [SUPPORTED_LANGUAGES_NAMES[:2], SUPPORTED_LANGUAGES_NAMES[2:], ],
                    },
                )
        elif wizard_step == 'sex':
            if missing:
                invitation = 'To continue chatting you need to set up your sex. If you pick ' + \
                    '\"Not Specified\" you can\'t choose your partner\'s sex.'
            else:
                invitation = 'Set up your sex. If you pick \"Not Specified\" you can\'t choose ' + \
                    'your partner\'s sex.'
            yield from self._sender.send_notification(invitation, reply_markup=SEX_KEYBOARD)
        elif wizard_step == 'partner_sex':
            if missing:
                invitation = 'To continue chatting you need to choose your partners\' sex.'
            else:
                invitation = 'Choose your partner\'s sex'
            yield from self._sender.send_notification(invitation, reply_markup=SEX_KEYBOARD)
        elif wizard_step == 'stop':
            if missing:
                invitation = 'Thank you. Now you can continue chatting.'
            else:
                invitation = 'Thank you. Use /begin to start looking for a conversational partner, ' + \
                    'once you\'re matched you can use /end to end the conversation.'
            yield from self._sender.send_notification(invitation, reply_markup={'hide_keyboard': True})
            self.deactivate()
