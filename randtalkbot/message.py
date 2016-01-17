# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import telepot

class UnsupportedContentError(Exception):
    pass

class Message:
    def __init__(self, message_json):
        try:
            self.type, chat_type, chat_id = telepot.glance2(message_json)
        except RuntimeError:
            raise UnsupportedContentError()
        if 'reply_to_message' in message_json:
            raise UnsupportedContentError()
        if self.type == 'text':
            try:
                self.sending_kwargs = {
                    'text': message_json['text'],
                    }
            except (KeyError, TypeError):
                raise UnsupportedContentError()
        elif self.type == 'photo':
            try:
                self.sending_kwargs = {
                    'photo': message_json['photo'][-1]['file_id'],
                    }
            except (KeyError, TypeError):
                raise UnsupportedContentError()
            try:
                self.sending_kwargs['caption'] = message_json['caption']
            except KeyError:
                pass
        elif self.type == 'sticker':
            try:
                self.sending_kwargs = {
                    'sticker': message_json['sticker']['file_id'],
                    }
            except (KeyError, TypeError):
                raise UnsupportedContentError()
        else:
            raise UnsupportedContentError()
