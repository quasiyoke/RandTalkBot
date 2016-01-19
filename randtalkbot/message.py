# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import telepot

LOGGER = logging.getLogger('randtalkbot')

class UnsupportedContentError(Exception):
    pass

class Message:
    def __init__(self, message_json):
        try:
            content_type, chat_type, chat_id = telepot.glance2(message_json)
        except RuntimeError:
            raise UnsupportedContentError()
        if 'forward_from' in message_json or 'reply_to_message' in message_json:
            raise UnsupportedContentError()
        try:
            getattr(self, '_init_' + content_type)(message_json)
        except AttributeError:
            raise UnsupportedContentError()
        else:
            self.type = content_type

    def _init_audio(self, message_json):
        try:
            audio = message_json['audio']
            self.sending_kwargs = {
                'audio': audio['file_id'],
                }
        except (KeyError, TypeError):
            raise UnsupportedContentError()
        self.sending_kwargs['duration'] = audio.get('duration')
        self.sending_kwargs['performer'] = audio.get('performer')
        self.sending_kwargs['title'] = audio.get('title')

    def _init_document(self, message_json):
        try:
            self.sending_kwargs = {
                'document': message_json['document']['file_id'],
                }
        except (KeyError, TypeError):
            raise UnsupportedContentError()

    def _init_location(self, message_json):
        try:
            location = message_json['location']
            self.sending_kwargs = {
                'latitude': location['latitude'],
                'longitude': location['longitude'],
                }
        except (KeyError, TypeError):
            raise UnsupportedContentError()

    def _init_photo(self, message_json):
        try:
            self.sending_kwargs = {
                'photo': message_json['photo'][0]['file_id'],
                }
        except (IndexError, KeyError, TypeError):
            raise UnsupportedContentError()
        self.sending_kwargs['caption'] = message_json.get('caption')

    def _init_sticker(self, message_json):
        try:
            self.sending_kwargs = {
                'sticker': message_json['sticker']['file_id'],
                }
        except (KeyError, TypeError):
            raise UnsupportedContentError()

    def _init_text(self, message_json):
        try:
            self.sending_kwargs = {
                'text': message_json['text'],
                }
        except (KeyError, TypeError):
            raise UnsupportedContentError()

    def _init_video(self, message_json):
        try:
            video = message_json['video']
            self.sending_kwargs = {
                'video': video['file_id'],
                }
        except (KeyError, TypeError):
            raise UnsupportedContentError()
        self.sending_kwargs['caption'] = message_json.get('caption')
        self.sending_kwargs['duration'] = video.get('duration')

    def _init_voice(self, message_json):
        try:
            voice = message_json['voice']
            self.sending_kwargs = {
                'voice': voice['file_id'],
                }
        except (KeyError, TypeError):
            raise UnsupportedContentError()
        self.sending_kwargs['duration'] = voice.get('duration')
