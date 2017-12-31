# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import logging
import sys
import telepot
import telepot.aio
from telepot.exception import TelegramError
from .errors import MissingPartnerError, PartnerObtainingError, \
    StrangerError, StrangerServiceError, UnknownCommandError, UnsupportedContentError
from .message import Message
from .stranger_sender_service import StrangerSenderService
from .stranger_service import StrangerService
from .stranger_setup_wizard import StrangerSetupWizard
from .utils import __version__

LOGGER = logging.getLogger('randtalkbot.stranger_handler')


def _(string_instance):
    return string_instance


class StrangerHandler(telepot.aio.helper.UserHandler):
    HOUR_TIMEDELTA = datetime.timedelta(hours=1)
    LONG_WAITING_TIMEDELTA = datetime.timedelta(minutes=10)
    COORDINATOR_CLASS = telepot.aio.helper.CallbackQueryCoordinator

    def __init__(self, seed_tuple, *args, **kwargs):
        super(StrangerHandler, self).__init__(seed_tuple, *args, **kwargs)
        bot, initial_msg, unused_seed = seed_tuple
        self._from_id = initial_msg['from']['id']
        try:
            self._stranger = StrangerService.get_instance() \
                .get_or_create_stranger(self._from_id)
        except StrangerServiceError as err:
            LOGGER.exception('Problems with StrangerHandler construction')
            sys.exit('Problems with StrangerHandler construction: %s' % err)
        self._sender = StrangerSenderService.get_instance(bot). \
            get_or_create_stranger_sender(self._stranger)
        self._stranger_setup_wizard = StrangerSetupWizard(self._stranger)
        self._deferred_advertising = None

    async def handle_command(self, message):
        handler_name = '_handle_command_' + message.command
        try:
            handler = getattr(self, handler_name)
        except AttributeError:
            raise UnknownCommandError(message.command)
        await handler(message)

    async def _handle_command_begin(self, unused_message):
        self._stranger.prevent_advertising()
        try:
            await StrangerService.get_instance().match_partner(self._stranger)
        except PartnerObtainingError:
            LOGGER.debug('Looking for partner: %d', self._stranger.id)
            self._stranger.advertise_later()
            await self._stranger.set_looking_for_partner()
        except StrangerServiceError as err:
            LOGGER.warning('Can\'t set partner for %d. %s', self._stranger.id, err)

    async def _handle_command_end(self, unused_message):
        partner = self._stranger.get_partner()
        LOGGER.debug(
            '/end: %d -x-> %s',
            self._stranger.id,
            'none' if partner is None else partner.id,
            )
        self._stranger.prevent_advertising()
        await self._stranger.end_talk()

    async def _handle_command_help(self, unused_message):
        try:
            await self._sender.send_notification(
                _(
                    '*Help*\n\n'
                    'Use /begin to start looking for a conversational partner, once'
                    ' you\'re matched you can use /end to finish the conversation.'
                    ' To choose your settings, apply /setup.\n\n'
                    'If you have any suggestions or require help, please contact @quasiyoke.'
                    ' When asking questions, please provide this number: {0}.\n\n'
                    'Subscribe to [our news](https://telegram.me/RandTalk). You\'re welcome'
                    ' to inspect and improve [Rand Talk v. {1} source code]'
                    '(https://github.com/quasiyoke/RandTalkBot) or to [give us 5 stars]'
                    '(https://telegram.me/storebot?start=randtalkbot).',
                ),
                self._from_id,
                __version__,
                disable_web_page_preview=True,
                )
        except TelegramError as err:
            LOGGER.warning('Handle /help command. Can\'t notify stranger. %s', err)

    async def _handle_command_mute_bonuses(self, unused_message):
        self._stranger.mute_bonuses_notifications()

        try:
            await self._sender.send_notification(
                _('Notifications about bonuses were muted for 1 hour'),
                )
        except TelegramError as err:
            LOGGER.warning('Handle /mute_bonuses command. Can\'t notify stranger. %s', err)

    async def _handle_command_setup(self, unused_message):
        LOGGER.debug('/setup: %d', self._stranger.id)
        self._stranger.prevent_advertising()
        await self._stranger.end_talk()
        await self._stranger_setup_wizard.activate()

    async def _handle_command_start(self, message):
        LOGGER.debug('/start: %d', self._stranger.id)
        if message.command_args and not self._stranger.invited_by:
            try:
                command_args = message.decode_command_args()
            except UnsupportedContentError as err:
                LOGGER.info(
                    '/start error. Can\'t decode invitation %s: %s',
                    message.command_args,
                    err,
                    )
            else:
                try:
                    invitation = command_args['i']
                except (KeyError, TypeError) as err:
                    LOGGER.info('/start error. Can\'t obtain invitation: %s', err)
                else:
                    if self._stranger.invitation == invitation:
                        try:
                            await self._sender.send_notification(
                                _(
                                    'Don\'t try to fool me. Forward message'
                                    ' with the link to your friends and'
                                    ' receive well-earned bonuses that will'
                                    ' help you to find partner quickly.',
                                    ),
                                )
                        except TelegramError as err:
                            LOGGER.warning(
                                'Handle /start command. Can\'t notify cheating stranger. %s',
                                err,
                                )
                    else:
                        try:
                            invited_by = StrangerService.get_instance() \
                                .get_stranger_by_invitation(invitation)
                        except StrangerServiceError as err:
                            LOGGER.info(
                                '/start error. Can\'t obtain stranger who did invite: %s',
                                err,
                                )
                        else:
                            self._stranger.invited_by = invited_by
                            self._stranger.save()
        if self._stranger.wizard == 'none':
            try:
                await self._sender.send_notification(
                    _(
                        '*Manual*\n\nUse /begin to start looking for a'
                        ' conversational partner, once you\'re matched you can'
                        ' use /end to end the conversation.',
                        ),
                    )
            except TelegramError as err:
                LOGGER.warning('Handle /start command. Can\'t notify stranger. %s', err)

    # pylint: disable=method-hidden
    async def on_close(self, error):
        pass

    async def on_chat_message(self, message_json):
        unused_content_type, chat_type, unused_chat_id = telepot.glance(message_json)

        if chat_type != 'private':
            return

        try:
            message = Message(message_json)
        except UnsupportedContentError:
            await self._sender.send_notification(_('Messages of this type aren\'t supported.'))
            return

        if message.command:
            if await self._stranger_setup_wizard.handle_command(message):
                return

            try:
                await self.handle_command(message)
            except UnknownCommandError:
                await self._sender.send_notification(
                    _('Unknown command. Look /help for the full list of commands.'),
                    )
        elif not await self._stranger_setup_wizard.handle(message):
            try:
                await self._stranger.send_to_partner(message)
            except MissingPartnerError:
                pass
            except StrangerError:
                await self._sender.send_notification(_('Messages of this type aren\'t supported.'))
            except TelegramError:
                LOGGER.warning(
                    'Send message. Can\'t send to partned: %d -> %d',
                    self._stranger.id,
                    self._stranger.get_partner().id,
                    )
                await self._sender.send_notification(
                    _('Your partner has blocked me! How did you do that?!'),
                    )
                await self._stranger.end_talk()

    async def on_edited_chat_message(self, unused_message_json):
        LOGGER.info('User tried to edit their message.')
        await self._sender.send_notification(
            _('Messages editing isn\'t supported'),
            )

    async def on_inline_query(self, query):
        query_id, unused_from_id, query_string = telepot.glance(query, flavor='inline_query')
        LOGGER.debug('Inline query from %d: \"%s\"', self._stranger.id, query_string)
        response = [{
            'type': 'article',
            'id': 'invitation_link',
            'title': _('Rand Talk Invitation Link'),
            'description': _('The more friends\'ll use your link -- the faster the search will be'),
            'thumb_url': 'http://randtalk.ml/static/img/logo-500x500.png',
            'message_text': (
                _(
                    'Do you want to talk with somebody, practice in foreign languages or you'
                    ' just want to have some fun? Rand Talk will help you! It\'s a bot matching'
                    ' you with a random stranger of desired sex speaking on your language. {0}'
                    ),
                self._stranger.get_invitation_link(),
                ),
            'parse_mode': 'Markdown',
            }]
        await self._sender.answer_inline_query(query_id, response)
