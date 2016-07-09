# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

class DBError(Exception):
    pass

class EmptyLanguagesError(Exception):
    pass

class MissingCommandError(Exception):
    pass

class MissingPartnerError(Exception):
    pass

class PartnerObtainingError(Exception):
    pass

class SexError(Exception):
    def __init__(self, sex):
        super(SexError, self).__init__(
            'Unknown sex: \"{}\" -- is not a valid sex name.'.format(sex),
            )
        self.name = sex

class StrangerError(Exception):
    pass

class StrangerHandlerError(Exception):
    pass

class StrangerSenderError(Exception):
    pass

class StrangerSenderServiceError(Exception):
    pass

class StrangerServiceError(Exception):
    pass

class UnknownCommandError(Exception):
    def __init__(self, command):
        super(UnknownCommandError, self).__init__()
        self.command = command

class UnsupportedContentError(Exception):
    pass

class WrongStrangerError(Exception):
    pass
