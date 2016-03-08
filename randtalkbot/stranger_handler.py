# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import datetime
import logging
import re
import sys
import telepot
import telepot.async
from .errors import MissingPartnerError, StrangerError, StrangerHandlerError, UnknownCommandError
from .i18n import get_languages_codes, get_translation, LanguageNotFoundError, SUPPORTED_LANGUAGES_NAMES
from .message import Message, UnsupportedContentError
from .stranger import SEX_NAMES
from .stranger_sender import StrangerSender
from .stranger_sender_service import StrangerSenderService
from .stranger_service import PartnerObtainingError, StrangerServiceError
from .stranger_setup_wizard import StrangerSetupWizard
from .utils import __version__
from telepot import TelegramError

LOGGER = logging.getLogger('randtalkbot.stranger_handler')

def _(s): return s

class StrangerHandler(telepot.async.helper.UserHandler):
    HOUR_TIMEDELTA = datetime.timedelta(hours=1)
    LONG_WAITING_TIMEDELTA = datetime.timedelta(minutes=10)

    def __init__(self, seed_tuple, stranger_service):
        '''
        Most of this constructor's code were copied from telepot.helper.ChatHandler and
        its superclasses to inject stranger_sender_service.
        '''
        bot, initial_msg, seed = seed_tuple
        telepot.helper.ListenerContext.__init__(self, bot, seed)
        from_id = initial_msg['from']['id']
        self._from_id = from_id
        self.listener.set_options()
        self.listener.capture(from__id=from_id)
        self._stranger_service = stranger_service
        try:
            self._stranger = self._stranger_service.get_or_create_stranger(self._from_id)
        except StrangerServiceError as e:
            LOGGER.error('Problems with StrangerHandler construction: %s', e)
            sys.exit('Problems with StrangerHandler construction: %s' % e)
        self._sender = StrangerSenderService.get_instance(bot).get_or_create_stranger_sender(self._stranger)
        self._stranger_setup_wizard = StrangerSetupWizard(self._stranger)
        self._deferred_advertising = None

    @asyncio.coroutine
    def handle_command(self, message):
        handler_name = '_handle_command_' + message.command
        try:
            handler = getattr(self, handler_name)
        except AttributeError:
            raise UnknownCommandError(message.command)
        yield from handler(message)

    @asyncio.coroutine
    def _handle_command_begin(self, message):
        self._stranger.prevent_advertising()
        try:
            yield from self._set_partner()
        except PartnerObtainingError:
            LOGGER.debug('Looking for partner: %d', self._stranger.id)
            self._stranger.advertise_later()
            yield from self._stranger.set_looking_for_partner()
        except StrangerHandlerError as e:
            LOGGER.warning('Can\'t notify seeking for partner stranger: %s', e)
        except StrangerServiceError as e:
            LOGGER.error('Problems with handling /begin command for %d: %s', self._stranger.id, str(e))
            yield from self._sender.send_notification(
                _('Internal error. Admins are already notified about that.'),
                )

    @asyncio.coroutine
    def _handle_command_end(self, message):
        LOGGER.debug(
            '/end: %d -x-> %d',
            self._stranger.id,
            self._stranger.partner.id if self._stranger.partner else 0,
            )
        self._stranger.prevent_advertising()
        yield from self._stranger.end_chatting()

    @asyncio.coroutine
    def _handle_command_help(self, message):
        yield from self._sender.send_notification(
            _('*Help*\n\n'
                'Use /begin to start looking for a conversational partner, once '
                'you\'re matched you can use /end to finish the conversation. '
                'To choose your settings, apply /setup.\n\n'
                'If you have any suggestions or require help, please contact @quasiyoke. '
                'When asking questions, please provide this number: {0}.\n\n'
                'Subscribe to [our news](https://telegram.me/RandTalk). You\'re welcome '
                'to inspect and improve [Rand Talk v. {1} source code]'
                '(https://github.com/quasiyoke/RandTalkBot) or to [give us 5 stars]'
                '(https://telegram.me/storebot?start=randtalkbot).'),
            self._from_id,
            __version__,
            )

    @asyncio.coroutine
    def _handle_command_mute_bonuses(self, message):
        self._stranger.mute_bonuses_notifications()
        yield from self._sender.send_notification(
            _('Notifications about bonuses were muted for 1 hour'),
            )

    @asyncio.coroutine
    def _handle_command_setup(self, message):
        LOGGER.debug('/setup: %d', self._stranger.id)
        self._stranger.prevent_advertising()
        yield from self._stranger.end_chatting()
        yield from self._stranger_setup_wizard.activate()

    @asyncio.coroutine
    def _handle_command_start(self, message):
        LOGGER.debug('/start: %d', self._stranger.id)
        if message.command_args and not self._stranger.invited_by:
            try:
                command_args = message.decode_command_args()
            except UnsupportedContentError as e:
                LOGGER.info('/start error. Can\'t decode invitation %s: %s', message.command_args, e)
            else:
                try:
                    invitation = command_args['i']
                except (KeyError, TypeError) as e:
                    LOGGER.info('/start error. Can\'t obtain invitation: %s', e)
                else:
                    if self._stranger.invitation == invitation:
                        yield from self._sender.send_notification(
                            _('Don\'t try to fool me. Forward message with the link to your friends and '
                                'receive well-earned bonuses that will help you to find partner quickly.'),
                            )
                    else:
                        try:
                            invited_by = self._stranger_service.get_stranger_by_invitation(invitation)
                        except StrangerServiceError as e:
                            LOGGER.info('/start error. Can\'t obtain stranger who did invite: %s', e)
                        else:
                            self._stranger.invited_by = invited_by
                            self._stranger.save()
        if self._stranger.wizard == 'none':
            yield from self._sender.send_notification(
                _('*Manual*\n\nUse /begin to start looking for a conversational partner, once '
                    'you\'re matched you can use /end to end the conversation.'),
                )

    @asyncio.coroutine
    def on_chat_message(self, message_json):
        content_type, chat_type, chat_id = telepot.glance(message_json)

        if chat_type != 'private':
            return

        try:
            message = Message(message_json)
        except UnsupportedContentError:
            yield from self._sender.send_notification(_('Messages of this type aren\'t supported.'))
            return

        if message.command:
            if (yield from self._stranger_setup_wizard.handle_command(message)):
                return
            try:
                yield from self.handle_command(message)
            except UnknownCommandError as e:
                yield from self._sender.send_notification(
                    _('Unknown command. Look /help for the full list of commands.'),
                    )
        elif not (yield from self._stranger_setup_wizard.handle(message)):
            try:
                yield from self._stranger.send_to_partner(message)
            except MissingPartnerError:
                pass
            except StrangerError:
                yield from self._sender.send_notification(_('Messages of this type aren\'t supported.'))
            except TelegramError:
                LOGGER.warning(
                    'Send message. Can\'t send to partned: %d -> %d',
                    self._stranger.id,
                    self._stranger.partner.id,
                    )
                yield from self._sender.send_notification(
                    _('Your partner has blocked me! How did you do that?!'),
                    )
                yield from self._stranger.end_chatting()

    @asyncio.coroutine
    def on_inline_query(self, query):
        query_id, from_id, query_string = telepot.glance(query, flavor='inline_query')
        LOGGER.debug('Inline query from {}: {}'.format(self._stranger.id, query_string))
        response = [{
            'type': 'article',
            'id': 'invitation_link',
            'title': _('Rand Talk Invitation Link'),
            'description': _('The more friends\'ll use your link -- the faster the search will be'),
            'thumb_url': 'http://randtalk.ml/static/img/logo-500x500.png',
            'message_text': (
                _('Do you want to talk with somebody, practice in foreign languages or you just want '
                    'to have some fun? Rand Talk will help you! It\'s a bot matching you with '
                    'a random stranger of desired sex speaking on your language. {0}'),
                self._stranger.get_invitation_link(),
                ),
            'parse_mode': 'Markdown',
            }]
        yield from self._sender.answer_inline_query(query_id, response)

    @asyncio.coroutine
    def _set_partner(self):
        '''
        Finds partner for the stranger. Does handling of strangers who have blocked the bot.

        @raise PartnerObtainingError if there's no proper partners.
        @raise StrangerHandlerError if the stranger has blocked the bot.
        @raise StrangerServiceError if there're some DB troubles.
        '''
        while True:
            partner = self._stranger_service.get_partner(self._stranger)
            try:
                yield from partner.notify_partner_found(self._stranger)
            except StrangerError:
                # Potential partner has blocked the bot. Let's look for next potential partner.
                yield from partner.end_chatting()
            else:
                try:
                    yield from self._stranger.notify_partner_found(partner)
                except StrangerError as e:
                    # Stranger has blocked the bot. Forgive him, clear his potential partner and exit
                    # the cycle.
                    raise StrangerHandlerError('Can\'t notify seeking for partner stranger: {0}'.format(e))
                else:
                    yield from self._stranger.set_partner(partner)
                    yield from partner.set_partner(self._stranger)
                    LOGGER.debug('Found partner: %d -> %d.', self._stranger.id, partner.id)
                    break
