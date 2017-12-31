# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import asynctest
import datetime
import json
import types
import unittest
from asynctest.mock import patch, Mock, CoroutineMock
from peewee import *
from randtalkbot import stats
from randtalkbot.stats_service import StatsService
from randtalkbot.stats import Stats

ENDED_TALKS = (
    {'begin': 315535576, 'end': 315539910, 'partner2_sent': 195, 'searched_since': 315525609, 'partner1_sent': 110},
    {'begin': 315540982, 'end': 315549266, 'partner2_sent': 89, 'searched_since': 315532407, 'partner1_sent': 72},
    {'begin': 315540558, 'end': 315549501, 'partner2_sent': 180, 'searched_since': 315533196, 'partner1_sent': 157},
    {'begin': 315530537, 'end': 315536603, 'partner2_sent': 17, 'searched_since': 315522742, 'partner1_sent': 5},
    {'begin': 315542527, 'end': 315552039, 'partner2_sent': 171, 'searched_since': 315535615, 'partner1_sent': 198},
    {'begin': 315539577, 'end': 315544866, 'partner2_sent': 139, 'searched_since': 315528991, 'partner1_sent': 121},
    {'begin': 315541786, 'end': 315547525, 'partner2_sent': 98, 'searched_since': 315535151, 'partner1_sent': 134},
    {'begin': 315534294, 'end': 315538736, 'partner2_sent': 4, 'searched_since': 315527755, 'partner1_sent': 2},
    {'begin': 315538226, 'end': 315544300, 'partner2_sent': 63, 'searched_since': 315528767, 'partner1_sent': 81},
    {'begin': 315542257, 'end': 315554827, 'partner2_sent': 97, 'searched_since': 315532576, 'partner1_sent': 65},
    {'begin': 315537707, 'end': 315540371, 'partner2_sent': 198, 'searched_since': 315535854, 'partner1_sent': 151},
    {'begin': 315532404, 'end': 315544411, 'partner2_sent': 168, 'searched_since': 315522802, 'partner1_sent': 27},
    {'begin': 315534746, 'end': 315538175, 'partner2_sent': 20, 'searched_since': 315524245, 'partner1_sent': 126},
    {'begin': 315532230, 'end': 315546504, 'partner2_sent': 167, 'searched_since': 315524395, 'partner1_sent': 172},
    {'begin': 315535018, 'end': 315547310, 'partner2_sent': 156, 'searched_since': 315533966, 'partner1_sent': 120},
    {'begin': 315537808, 'end': 315542294, 'partner2_sent': 154, 'searched_since': 315532719, 'partner1_sent': 161},
    {'begin': 315541000, 'end': 315551534, 'partner2_sent': 142, 'searched_since': 315529617, 'partner1_sent': 108},
    {'begin': 315532454, 'end': 315542731, 'partner2_sent': 18, 'searched_since': 315526666, 'partner1_sent': 44},
    {'begin': 315540402, 'end': 315545463, 'partner2_sent': 125, 'searched_since': 315529029, 'partner1_sent': 31},
    {'begin': 315548500, 'end': 315556228, 'partner2_sent': 162, 'searched_since': 315534533, 'partner1_sent': 151},
    {'begin': 315538123, 'end': 315542201, 'partner2_sent': 176, 'searched_since': 315530565, 'partner1_sent': 191},
    {'begin': 315536559, 'end': 315537732, 'partner2_sent': 154, 'searched_since': 315532645, 'partner1_sent': 88},
    {'begin': 315538699, 'end': 315539492, 'partner2_sent': 108, 'searched_since': 315527774, 'partner1_sent': 117},
    {'begin': 315530251, 'end': 315532356, 'partner2_sent': 32, 'searched_since': 315524349, 'partner1_sent': 16},
    {'begin': 315526170, 'end': 315529624, 'partner2_sent': 1, 'searched_since': 315522199, 'partner1_sent': 91},
    {'begin': 315539972, 'end': 315550124, 'partner2_sent': 154, 'searched_since': 315533040, 'partner1_sent': 196},
    {'begin': 315528373, 'end': 315537503, 'partner2_sent': 99, 'searched_since': 315526305, 'partner1_sent': 128},
    {'begin': 315533668, 'end': 315538971, 'partner2_sent': 168, 'searched_since': 315525395, 'partner1_sent': 190},
    {'begin': 315530384, 'end': 315541530, 'partner2_sent': 109, 'searched_since': 315527936, 'partner1_sent': 95},
    {'begin': 315533596, 'end': 315547163, 'partner2_sent': 163, 'searched_since': 315530552, 'partner1_sent': 85},
    {'begin': 315528411, 'end': 315541110, 'partner2_sent': 158, 'searched_since': 315525257, 'partner1_sent': 84},
    {'begin': 315530099, 'end': 315541801, 'partner2_sent': 93, 'searched_since': 315525176, 'partner1_sent': 99},
    {'begin': 315538831, 'end': 315545067, 'partner2_sent': 194, 'searched_since': 315530123, 'partner1_sent': 83},
    {'begin': 315532385, 'end': 315539229, 'partner2_sent': 153, 'searched_since': 315523512, 'partner1_sent': 4},
    {'begin': 315536428, 'end': 315545448, 'partner2_sent': 68, 'searched_since': 315530185, 'partner1_sent': 132},
    {'begin': 315532488, 'end': 315545820, 'partner2_sent': 187, 'searched_since': 315530474, 'partner1_sent': 63},
    {'begin': 315544366, 'end': 315551652, 'partner2_sent': 82, 'searched_since': 315533957, 'partner1_sent': 68},
    {'begin': 315548723, 'end': 315551326, 'partner2_sent': 4, 'searched_since': 315534977, 'partner1_sent': 36},
    {'begin': 315533128, 'end': 315533345, 'partner2_sent': 98, 'searched_since': 315524298, 'partner1_sent': 110},
    {'begin': 315542939, 'end': 315549123, 'partner2_sent': 197, 'searched_since': 315532329, 'partner1_sent': 105},
    {'begin': 315540852, 'end': 315544679, 'partner2_sent': 196, 'searched_since': 315527887, 'partner1_sent': 154},
    {'begin': 315536504, 'end': 315550084, 'partner2_sent': 15, 'searched_since': 315523459, 'partner1_sent': 169},
    {'begin': 315535197, 'end': 315537557, 'partner2_sent': 22, 'searched_since': 315531293, 'partner1_sent': 86},
    {'begin': 315535885, 'end': 315538255, 'partner2_sent': 122, 'searched_since': 315534334, 'partner1_sent': 92},
    {'begin': 315533312, 'end': 315539778, 'partner2_sent': 100, 'searched_since': 315524382, 'partner1_sent': 111},
    {'begin': 315536893, 'end': 315543688, 'partner2_sent': 76, 'searched_since': 315533010, 'partner1_sent': 72},
    {'begin': 315527729, 'end': 315533235, 'partner2_sent': 89, 'searched_since': 315523733, 'partner1_sent': 156},
    {'begin': 315545545, 'end': 315557883, 'partner2_sent': 51, 'searched_since': 315532828, 'partner1_sent': 152},
    {'begin': 315533295, 'end': 315541528, 'partner2_sent': 130, 'searched_since': 315532184, 'partner1_sent': 139},
    {'begin': 315535935, 'end': 315538896, 'partner2_sent': 180, 'searched_since': 315530850, 'partner1_sent': 192},
    {'begin': 315543586, 'end': 315546820, 'partner2_sent': 191, 'searched_since': 315535096, 'partner1_sent': 176},
    {'begin': 315528033, 'end': 315535018, 'partner2_sent': 61, 'searched_since': 315526814, 'partner1_sent': 154},
    {'begin': 315523629, 'end': 315523912, 'partner2_sent': 37, 'searched_since': 315522778, 'partner1_sent': 143},
    {'begin': 315536052, 'end': 315536184, 'partner2_sent': 155, 'searched_since': 315523833, 'partner1_sent': 14},
    {'begin': 315538417, 'end': 315551665, 'partner2_sent': 67, 'searched_since': 315535974, 'partner1_sent': 193},
    {'begin': 315539188, 'end': 315553312, 'partner2_sent': 145, 'searched_since': 315530944, 'partner1_sent': 65},
    {'begin': 315529848, 'end': 315533880, 'partner2_sent': 195, 'searched_since': 315528831, 'partner1_sent': 38},
    {'begin': 315528618, 'end': 315537645, 'partner2_sent': 191, 'searched_since': 315522800, 'partner1_sent': 195},
    {'begin': 315543389, 'end': 315557768, 'partner2_sent': 148, 'searched_since': 315530330, 'partner1_sent': 67},
    {'begin': 315525361, 'end': 315537395, 'partner2_sent': 96, 'searched_since': 315523394, 'partner1_sent': 59},
    {'begin': 315544110, 'end': 315545127, 'partner2_sent': 93, 'searched_since': 315531511, 'partner1_sent': 156},
    {'begin': 315536298, 'end': 315543241, 'partner2_sent': 195, 'searched_since': 315531725, 'partner1_sent': 119},
    {'begin': 315531915, 'end': 315536975, 'partner2_sent': 174, 'searched_since': 315525332, 'partner1_sent': 83},
    {'begin': 315527346, 'end': 315529106, 'partner2_sent': 137, 'searched_since': 315524984, 'partner1_sent': 77},
    {'begin': 315535109, 'end': 315538785, 'partner2_sent': 145, 'searched_since': 315532504, 'partner1_sent': 140},
    {'begin': 315536622, 'end': 315541679, 'partner2_sent': 31, 'searched_since': 315528346, 'partner1_sent': 9},
    {'begin': 315532584, 'end': 315539393, 'partner2_sent': 4, 'searched_since': 315528988, 'partner1_sent': 146},
    {'begin': 315542323, 'end': 315551605, 'partner2_sent': 107, 'searched_since': 315535065, 'partner1_sent': 23},
    {'begin': 315532376, 'end': 315539558, 'partner2_sent': 193, 'searched_since': 315525364, 'partner1_sent': 177},
    {'begin': 315540260, 'end': 315552087, 'partner2_sent': 103, 'searched_since': 315529263, 'partner1_sent': 134},
    {'begin': 315548467, 'end': 315562272, 'partner2_sent': 151, 'searched_since': 315534749, 'partner1_sent': 121},
    {'begin': 315530444, 'end': 315537502, 'partner2_sent': 1, 'searched_since': 315524816, 'partner1_sent': 72},
    {'begin': 315530724, 'end': 315534156, 'partner2_sent': 81, 'searched_since': 315528546, 'partner1_sent': 84},
    {'begin': 315536115, 'end': 315545288, 'partner2_sent': 87, 'searched_since': 315529341, 'partner1_sent': 81},
    {'begin': 315540377, 'end': 315542262, 'partner2_sent': 27, 'searched_since': 315528606, 'partner1_sent': 11},
    {'begin': 315539048, 'end': 315551926, 'partner2_sent': 108, 'searched_since': 315536325, 'partner1_sent': 68},
    {'begin': 315537775, 'end': 315546871, 'partner2_sent': 146, 'searched_since': 315526036, 'partner1_sent': 22},
    {'begin': 315537962, 'end': 315546739, 'partner2_sent': 132, 'searched_since': 315533042, 'partner1_sent': 95},
    {'begin': 315545529, 'end': 315554008, 'partner2_sent': 162, 'searched_since': 315531155, 'partner1_sent': 102},
    {'begin': 315540257, 'end': 315547808, 'partner2_sent': 81, 'searched_since': 315535011, 'partner1_sent': 30},
    {'begin': 315544898, 'end': 315551806, 'partner2_sent': 137, 'searched_since': 315531401, 'partner1_sent': 199},
    {'begin': 315537023, 'end': 315550108, 'partner2_sent': 46, 'searched_since': 315530022, 'partner1_sent': 103},
    {'begin': 315528674, 'end': 315541748, 'partner2_sent': 106, 'searched_since': 315527521, 'partner1_sent': 52},
    {'begin': 315535736, 'end': 315548479, 'partner2_sent': 67, 'searched_since': 315531470, 'partner1_sent': 4},
    {'begin': 315535686, 'end': 315545913, 'partner2_sent': 92, 'searched_since': 315533060, 'partner1_sent': 79},
    {'begin': 315542344, 'end': 315553049, 'partner2_sent': 53, 'searched_since': 315531265, 'partner1_sent': 4},
    {'begin': 315545291, 'end': 315546459, 'partner2_sent': 135, 'searched_since': 315533258, 'partner1_sent': 166},
    {'begin': 315540445, 'end': 315547094, 'partner2_sent': 24, 'searched_since': 315534908, 'partner1_sent': 189},
    {'begin': 315540034, 'end': 315540722, 'partner2_sent': 33, 'searched_since': 315527470, 'partner1_sent': 87},
    {'begin': 315527239, 'end': 315537451, 'partner2_sent': 41, 'searched_since': 315527184, 'partner1_sent': 183},
    {'begin': 315524617, 'end': 315532747, 'partner2_sent': 49, 'searched_since': 315524535, 'partner1_sent': 112},
    {'begin': 315531239, 'end': 315532660, 'partner2_sent': 122, 'searched_since': 315529293, 'partner1_sent': 172},
    {'begin': 315524599, 'end': 315525391, 'partner2_sent': 140, 'searched_since': 315522392, 'partner1_sent': 36},
    {'begin': 315539379, 'end': 315539553, 'partner2_sent': 110, 'searched_since': 315526955, 'partner1_sent': 53},
    {'begin': 315526746, 'end': 315537547, 'partner2_sent': 93, 'searched_since': 315523454, 'partner1_sent': 55},
    {'begin': 315538324, 'end': 315541416, 'partner2_sent': 94, 'searched_since': 315525294, 'partner1_sent': 28},
    {'begin': 315528384, 'end': 315542574, 'partner2_sent': 75, 'searched_since': 315525298, 'partner1_sent': 161},
    {'begin': 315541503, 'end': 315543905, 'partner2_sent': 74, 'searched_since': 315530944, 'partner1_sent': 39},
    {'begin': 315538119, 'end': 315542639, 'partner2_sent': 145, 'searched_since': 315527463, 'partner1_sent': 104},
    {'begin': 315542020, 'end': 315546628, 'partner2_sent': 54, 'searched_since': 315532394, 'partner1_sent': 164},
    )
NOT_ENDED_TALKS = (
    {'begin': 315534560, 'end': None, 'partner2_sent': 52, 'searched_since': 315529527, 'partner1_sent': 129},
    {'begin': 315535264, 'end': None, 'partner2_sent': 52, 'searched_since': 315529093, 'partner1_sent': 110},
    {'begin': 315539525, 'end': None, 'partner2_sent': 29, 'searched_since': 315527251, 'partner1_sent': 146},
    {'begin': 315526497, 'end': None, 'partner2_sent': 135, 'searched_since': 315523473, 'partner1_sent': 22},
    {'begin': 315544200, 'end': None, 'partner2_sent': 100, 'searched_since': 315534532, 'partner1_sent': 30},
    {'begin': 315526965, 'end': None, 'partner2_sent': 119, 'searched_since': 315523092, 'partner1_sent': 61},
    {'begin': 315542554, 'end': None, 'partner2_sent': 8, 'searched_since': 315533661, 'partner1_sent': 185},
    {'begin': 315533333, 'end': None, 'partner2_sent': 93, 'searched_since': 315523991, 'partner1_sent': 32},
    {'begin': 315535555, 'end': None, 'partner2_sent': 38, 'searched_since': 315525621, 'partner1_sent': 141},
    {'begin': 315535003, 'end': None, 'partner2_sent': 185, 'searched_since': 315526501, 'partner1_sent': 73},
    {'begin': 315531982, 'end': None, 'partner2_sent': 136, 'searched_since': 315528920, 'partner1_sent': 42},
    {'begin': 315531638, 'end': None, 'partner2_sent': 162, 'searched_since': 315525205, 'partner1_sent': 173},
    {'begin': 315531322, 'end': None, 'partner2_sent': 110, 'searched_since': 315523982, 'partner1_sent': 77},
    {'begin': 315542161, 'end': None, 'partner2_sent': 48, 'searched_since': 315530543, 'partner1_sent': 120},
    {'begin': 315528983, 'end': None, 'partner2_sent': 33, 'searched_since': 315524315, 'partner1_sent': 162},
    {'begin': 315542619, 'end': None, 'partner2_sent': 102, 'searched_since': 315533220, 'partner1_sent': 102},
    {'begin': 315540642, 'end': None, 'partner2_sent': 176, 'searched_since': 315528142, 'partner1_sent': 95},
    {'begin': 315527977, 'end': None, 'partner2_sent': 92, 'searched_since': 315524879, 'partner1_sent': 74},
    {'begin': 315535598, 'end': None, 'partner2_sent': 152, 'searched_since': 315532629, 'partner1_sent': 83},
    {'begin': 315532429, 'end': None, 'partner2_sent': 120, 'searched_since': 315526309, 'partner1_sent': 42},
    {'begin': 315533378, 'end': None, 'partner2_sent': 200, 'searched_since': 315532007, 'partner1_sent': 173},
    {'begin': 315528802, 'end': None, 'partner2_sent': 137, 'searched_since': 315525638, 'partner1_sent': 115},
    {'begin': 315535409, 'end': None, 'partner2_sent': 170, 'searched_since': 315529859, 'partner1_sent': 37},
    {'begin': 315535686, 'end': None, 'partner2_sent': 105, 'searched_since': 315526189, 'partner1_sent': 119},
    {'begin': 315538893, 'end': None, 'partner2_sent': 29, 'searched_since': 315536180, 'partner1_sent': 95},
    {'begin': 315536249, 'end': None, 'partner2_sent': 95, 'searched_since': 315524722, 'partner1_sent': 163},
    {'begin': 315535769, 'end': None, 'partner2_sent': 185, 'searched_since': 315523600, 'partner1_sent': 120},
    {'begin': 315542044, 'end': None, 'partner2_sent': 39, 'searched_since': 315531962, 'partner1_sent': 159},
    {'begin': 315532457, 'end': None, 'partner2_sent': 86, 'searched_since': 315525518, 'partner1_sent': 180},
    {'begin': 315528494, 'end': None, 'partner2_sent': 186, 'searched_since': 315522168, 'partner1_sent': 101},
    {'begin': 315533289, 'end': None, 'partner2_sent': 88, 'searched_since': 315530379, 'partner1_sent': 127},
    {'begin': 315532801, 'end': None, 'partner2_sent': 138, 'searched_since': 315528576, 'partner1_sent': 99},
    {'begin': 315527654, 'end': None, 'partner2_sent': 99, 'searched_since': 315523709, 'partner1_sent': 11},
    {'begin': 315534207, 'end': None, 'partner2_sent': 175, 'searched_since': 315524568, 'partner1_sent': 95},
    {'begin': 315536081, 'end': None, 'partner2_sent': 54, 'searched_since': 315529470, 'partner1_sent': 174},
    {'begin': 315538607, 'end': None, 'partner2_sent': 172, 'searched_since': 315527999, 'partner1_sent': 176},
    {'begin': 315529580, 'end': None, 'partner2_sent': 15, 'searched_since': 315528785, 'partner1_sent': 108},
    {'begin': 315546432, 'end': None, 'partner2_sent': 146, 'searched_since': 315533910, 'partner1_sent': 108},
    {'begin': 315543974, 'end': None, 'partner2_sent': 20, 'searched_since': 315535312, 'partner1_sent': 162},
    {'begin': 315542559, 'end': None, 'partner2_sent': 177, 'searched_since': 315532682, 'partner1_sent': 168},
    {'begin': 315534129, 'end': None, 'partner2_sent': 112, 'searched_since': 315524557, 'partner1_sent': 184},
    {'begin': 315535868, 'end': None, 'partner2_sent': 129, 'searched_since': 315525874, 'partner1_sent': 72},
    {'begin': 315533837, 'end': None, 'partner2_sent': 13, 'searched_since': 315526375, 'partner1_sent': 93},
    {'begin': 315546044, 'end': None, 'partner2_sent': 151, 'searched_since': 315532438, 'partner1_sent': 27},
    {'begin': 315535263, 'end': None, 'partner2_sent': 156, 'searched_since': 315523622, 'partner1_sent': 39},
    {'begin': 315530123, 'end': None, 'partner2_sent': 64, 'searched_since': 315525010, 'partner1_sent': 92},
    {'begin': 315541444, 'end': None, 'partner2_sent': 80, 'searched_since': 315534521, 'partner1_sent': 68},
    {'begin': 315524650, 'end': None, 'partner2_sent': 109, 'searched_since': 315522081, 'partner1_sent': 186},
    {'begin': 315534471, 'end': None, 'partner2_sent': 164, 'searched_since': 315530609, 'partner1_sent': 200},
    {'begin': 315533115, 'end': None, 'partner2_sent': 14, 'searched_since': 315529794, 'partner1_sent': 179},
    {'begin': 315532517, 'end': None, 'partner2_sent': 86, 'searched_since': 315528063, 'partner1_sent': 52},
    {'begin': 315537737, 'end': None, 'partner2_sent': 106, 'searched_since': 315532162, 'partner1_sent': 163},
    {'begin': 315540581, 'end': None, 'partner2_sent': 104, 'searched_since': 315528540, 'partner1_sent': 174},
    {'begin': 315537023, 'end': None, 'partner2_sent': 161, 'searched_since': 315527756, 'partner1_sent': 167},
    {'begin': 315540455, 'end': None, 'partner2_sent': 106, 'searched_since': 315535045, 'partner1_sent': 83},
    {'begin': 315537807, 'end': None, 'partner2_sent': 35, 'searched_since': 315529591, 'partner1_sent': 53},
    {'begin': 315541693, 'end': None, 'partner2_sent': 198, 'searched_since': 315528074, 'partner1_sent': 90},
    {'begin': 315541732, 'end': None, 'partner2_sent': 130, 'searched_since': 315527996, 'partner1_sent': 9},
    {'begin': 315528005, 'end': None, 'partner2_sent': 41, 'searched_since': 315524387, 'partner1_sent': 3},
    {'begin': 315531496, 'end': None, 'partner2_sent': 79, 'searched_since': 315524804, 'partner1_sent': 46},
    {'begin': 315543367, 'end': None, 'partner2_sent': 148, 'searched_since': 315530406, 'partner1_sent': 120},
    {'begin': 315541648, 'end': None, 'partner2_sent': 49, 'searched_since': 315534926, 'partner1_sent': 91},
    {'begin': 315532880, 'end': None, 'partner2_sent': 121, 'searched_since': 315523154, 'partner1_sent': 198},
    {'begin': 315544787, 'end': None, 'partner2_sent': 99, 'searched_since': 315533713, 'partner1_sent': 68},
    {'begin': 315533802, 'end': None, 'partner2_sent': 0, 'searched_since': 315526704, 'partner1_sent': 166},
    {'begin': 315543000, 'end': None, 'partner2_sent': 87, 'searched_since': 315529749, 'partner1_sent': 105},
    {'begin': 315529384, 'end': None, 'partner2_sent': 144, 'searched_since': 315525330, 'partner1_sent': 90},
    {'begin': 315546345, 'end': None, 'partner2_sent': 156, 'searched_since': 315533360, 'partner1_sent': 164},
    {'begin': 315535531, 'end': None, 'partner2_sent': 49, 'searched_since': 315530377, 'partner1_sent': 23},
    {'begin': 315543951, 'end': None, 'partner2_sent': 194, 'searched_since': 315535613, 'partner1_sent': 72},
    {'begin': 315542296, 'end': None, 'partner2_sent': 44, 'searched_since': 315533730, 'partner1_sent': 111},
    {'begin': 315540608, 'end': None, 'partner2_sent': 95, 'searched_since': 315534470, 'partner1_sent': 189},
    {'begin': 315542607, 'end': None, 'partner2_sent': 82, 'searched_since': 315535091, 'partner1_sent': 147},
    {'begin': 315547271, 'end': None, 'partner2_sent': 105, 'searched_since': 315536363, 'partner1_sent': 48},
    {'begin': 315538878, 'end': None, 'partner2_sent': 139, 'searched_since': 315536059, 'partner1_sent': 46},
    {'begin': 315535141, 'end': None, 'partner2_sent': 1, 'searched_since': 315528597, 'partner1_sent': 116},
    {'begin': 315539129, 'end': None, 'partner2_sent': 10, 'searched_since': 315530304, 'partner1_sent': 125},
    {'begin': 315532433, 'end': None, 'partner2_sent': 57, 'searched_since': 315527056, 'partner1_sent': 160},
    {'begin': 315530065, 'end': None, 'partner2_sent': 83, 'searched_since': 315529856, 'partner1_sent': 142},
    {'begin': 315541645, 'end': None, 'partner2_sent': 122, 'searched_since': 315535897, 'partner1_sent': 146},
    {'begin': 315540618, 'end': None, 'partner2_sent': 43, 'searched_since': 315528278, 'partner1_sent': 44},
    {'begin': 315535023, 'end': None, 'partner2_sent': 164, 'searched_since': 315523631, 'partner1_sent': 69},
    {'begin': 315530374, 'end': None, 'partner2_sent': 180, 'searched_since': 315530156, 'partner1_sent': 36},
    {'begin': 315539242, 'end': None, 'partner2_sent': 177, 'searched_since': 315532319, 'partner1_sent': 127},
    {'begin': 315538692, 'end': None, 'partner2_sent': 177, 'searched_since': 315529580, 'partner1_sent': 109},
    {'begin': 315536109, 'end': None, 'partner2_sent': 32, 'searched_since': 315526397, 'partner1_sent': 27},
    {'begin': 315536006, 'end': None, 'partner2_sent': 117, 'searched_since': 315529950, 'partner1_sent': 43},
    {'begin': 315539226, 'end': None, 'partner2_sent': 12, 'searched_since': 315530971, 'partner1_sent': 14},
    {'begin': 315538138, 'end': None, 'partner2_sent': 18, 'searched_since': 315534289, 'partner1_sent': 120},
    {'begin': 315539152, 'end': None, 'partner2_sent': 174, 'searched_since': 315532879, 'partner1_sent': 46},
    {'begin': 315533804, 'end': None, 'partner2_sent': 165, 'searched_since': 315524040, 'partner1_sent': 5},
    {'begin': 315530704, 'end': None, 'partner2_sent': 75, 'searched_since': 315523298, 'partner1_sent': 134},
    {'begin': 315535850, 'end': None, 'partner2_sent': 47, 'searched_since': 315525120, 'partner1_sent': 54},
    {'begin': 315540102, 'end': None, 'partner2_sent': 172, 'searched_since': 315531045, 'partner1_sent': 8},
    {'begin': 315540931, 'end': None, 'partner2_sent': 23, 'searched_since': 315533894, 'partner1_sent': 63},
    {'begin': 315542676, 'end': None, 'partner2_sent': 15, 'searched_since': 315531224, 'partner1_sent': 11},
    {'begin': 315537971, 'end': None, 'partner2_sent': 122, 'searched_since': 315527791, 'partner1_sent': 45},
    {'begin': 315529693, 'end': None, 'partner2_sent': 118, 'searched_since': 315523112, 'partner1_sent': 89},
    {'begin': 315546072, 'end': None, 'partner2_sent': 189, 'searched_since': 315531748, 'partner1_sent': 198},
    {'begin': 315537598, 'end': None, 'partner2_sent': 148, 'searched_since': 315523821, 'partner1_sent': 100},
    {'begin': 315532727, 'end': None, 'partner2_sent': 178, 'searched_since': 315528103, 'partner1_sent': 64},
    {'begin': 315526660, 'end': None, 'partner2_sent': 81, 'searched_since': 315526423, 'partner1_sent': 134},
    {'begin': 315525105, 'end': None, 'partner2_sent': 88, 'searched_since': 315524510, 'partner1_sent': 166},
    {'begin': 315543163, 'end': None, 'partner2_sent': 71, 'searched_since': 315532980, 'partner1_sent': 1},
    )
STRANGERS = (
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['ru'], 'sex': 'female', 'partner_sex': 'male'},
    {'languages': ['ru'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['en', 'it'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['it'], 'sex': 'female', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['en', 'it'], 'sex': 'male', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'not_specified'},
    {'languages': ['en', 'it'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['ru'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['it'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['ru'], 'sex': 'male', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['ru'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['en', 'it'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'male'},
    {'languages': ['en', 'it'], 'sex': 'male', 'partner_sex': 'not_specified'},
    {'languages': ['en', 'it'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['ru', 'en'], 'sex': 'male', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'male'},
    {'languages': ['ru'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['it'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    {'languages': ['it'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['it'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['en', 'it'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['ru', 'en'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'not_specified', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['ru', 'it'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'female', 'partner_sex': 'male'},
    {'languages': ['en', 'it'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['en', 'it'], 'sex': 'not_specified', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['it'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'not_specified'},
    {'languages': ['ru'], 'sex': 'female', 'partner_sex': 'male'},
    {'languages': ['en', 'it'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['ru'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'female'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'female'},
    {'languages': ['ru'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['it'], 'sex': 'male', 'partner_sex': 'male'},
    {'languages': ['en'], 'sex': 'female', 'partner_sex': 'not_specified'},
    {'languages': ['de'], 'sex': 'not_specified', 'partner_sex': 'not_specified'},
    )

def get_strangers():
    for stranger_json in STRANGERS:
        stranger = Mock()
        stranger.sex = stranger_json['sex']
        stranger.partner_sex = stranger_json['partner_sex']
        stranger.get_languages = Mock(return_value=stranger_json['languages'])
        yield stranger

def get_talks(talks_json):
    talks = []
    for talk_json in talks_json:
        talk = Mock()
        talk.partner1_sent = talk_json['partner1_sent']
        talk.partner2_sent = talk_json['partner2_sent']
        talk.searched_since = datetime.datetime.fromtimestamp(talk_json['searched_since'])
        talk.begin = datetime.datetime.fromtimestamp(talk_json['begin'])
        if talk_json['end'] is not None:
            talk.end = datetime.datetime.fromtimestamp(talk_json['end'])
        talks.append(talk)
    return talks

class TestStatsService(asynctest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestStatsService, self).__init__(*args, **kwargs)
        self.database = SqliteDatabase(':memory:')

    def setUp(self):
        stats.DATABASE_PROXY.initialize(self.database)
        self.database.create_tables([Stats])
        self.update_stats = StatsService._update_stats
        StatsService._update_stats = Mock()
        self.stats_service = StatsService()
        self.stats = Mock()
        self.stats.created = datetime.datetime(1990, 1, 1)
        self.stats_service._stats = self.stats

    def tearDown(self):
        self.database.drop_tables([Stats])
        StatsService._update_stats = self.update_stats

    @asynctest.ignore_loop
    def test_init__no_stats_in_db(self):
        self.stats_service._update_stats.assert_called_once_with()
        stats_service = StatsService()
        self.assertEqual(stats_service._stats, None)

    @asynctest.ignore_loop
    def test_init__some_stats_in_db_1(self):
        stats1 = Stats.create(data_json='', created=datetime.datetime(1980, 1, 1))
        stats2 = Stats.create(data_json='', created=datetime.datetime(1990, 1, 1))
        stats_service = StatsService()
        self.assertEqual(stats_service._stats, stats2)

    @asynctest.ignore_loop
    def test_init__some_stats_in_db_2(self):
        stats1 = Stats.create(data_json='', created=datetime.datetime(1990, 1, 1))
        stats2 = Stats.create(data_json='', created=datetime.datetime(1980, 1, 1))
        stats_service = StatsService()
        self.assertEqual(stats_service._stats, stats1)

    @asynctest.ignore_loop
    def test_get_instance__ok(self):
        self.assertEqual(StatsService.get_instance(), self.stats_service)

    @asynctest.ignore_loop
    def test_get_instance__runtime_error(self):
        del StatsService._instance
        with self.assertRaises(RuntimeError):
            StatsService.get_instance()

    @asynctest.ignore_loop
    def test_get_stats(self):
        self.assertEqual(self.stats_service.get_stats(), self.stats)

    @patch('randtalkbot.stats_service.asyncio', CoroutineMock())
    @patch('randtalkbot.stats_service.datetime', Mock())
    async def test_run__ok(self):
        from randtalkbot.stats_service import asyncio
        from randtalkbot.stats_service import datetime as datetime_mock
        self.stats_service._update_stats.reset_mock()
        datetime_mock.datetime.utcnow.side_effect = [datetime.datetime(1990, 1, 1, 3), RuntimeError]
        with self.assertRaises(RuntimeError):
            await self.stats_service.run()
        asyncio.sleep.assert_called_once_with(3600)
        self.stats_service._update_stats.assert_called_once_with()

    @patch('randtalkbot.stats_service.asyncio')
    @patch('randtalkbot.stats_service.datetime', Mock())
    async def test_run__too_late(self, asyncio):
        from randtalkbot.stats_service import datetime as datetime_mock
        self.stats_service._update_stats.reset_mock()
        datetime_mock.datetime.utcnow.side_effect = [
            datetime.datetime(1990, 1, 1, 4, 0, 1),
            RuntimeError,
            ]
        with self.assertRaises(RuntimeError):
            await self.stats_service.run()
        asyncio.sleep.assert_not_called()
        self.stats_service._update_stats.assert_called_once_with()

    @asynctest.ignore_loop
    @patch('randtalkbot.stranger_service.StrangerService', Mock())
    @patch('randtalkbot.stranger_sender_service.StrangerSenderService', Mock())
    @patch('randtalkbot.talk.Talk', Mock())
    def test_update_stats__no_stats_in_db(self):
        from randtalkbot.stranger_service import StrangerService
        from randtalkbot.talk import Talk
        stranger_service = StrangerService.get_instance.return_value
        stranger_service.get_full_strangers = get_strangers
        Talk.get_not_ended_talks.return_value = get_talks(NOT_ENDED_TALKS)
        Talk.get_ended_talks.return_value = get_talks(ENDED_TALKS)
        self.stats_service._update_stats = types.MethodType(self.update_stats, self.stats_service)
        self.stats_service._stats = None
        self.stats_service._update_stats()
        Talk.get_not_ended_talks.assert_called_once_with(after=None)
        Talk.get_ended_talks.assert_called_once_with(after=None)
        Talk.delete_old.assert_not_called()
        actual = json.loads(self.stats_service._stats.data_json)
        expected = {
            'languages_count_distribution': [[1, 88], [2, 13]],
             'languages_popularity': [['en', 67], ['it', 34], ['ru', 12]],
             'languages_to_orientation': [['en',
                                           {'female female': 6,
                                            'female male': 5,
                                            'female not_specified': 11,
                                            'male female': 5,
                                            'male male': 10,
                                            'male not_specified': 6,
                                            'not_specified female': 7,
                                            'not_specified male': 11,
                                            'not_specified not_specified': 6}],
                                          ['it',
                                           {'female female': 5,
                                            'female male': 2,
                                            'female not_specified': 2,
                                            'male female': 7,
                                            'male male': 5,
                                            'male not_specified': 3,
                                            'not_specified female': 4,
                                            'not_specified male': 1,
                                            'not_specified not_specified': 5}],
                                          ['ru',
                                           {'female female': 2,
                                            'female male': 2,
                                            'female not_specified': 3,
                                            'male male': 2,
                                            'male not_specified': 2,
                                            'not_specified male': 1}]],
             'partner_sex_distribution': {'female': 31, 'male': 38, 'not_specified': 32},
             'sex_distribution': {'female': 33, 'male': 36, 'not_specified': 32},
             'talks_duration': {'average': 7092.79,
                                'count': 100,
                                'distribution': {'10': 0, '60': 0, '1800': 8, '300': 4, 'more': 88}},
             'talks_sent': {'average': 210.6,
                            'count': 100,
                            'distribution': {'4': 0, '16': 1, '256': 63, '64': 7, 'more': 29}},
             'talks_waiting': {'average': 7536.865384615385,
                               'count': 104,
                               'distribution': {'10800': 77,
                                                '1800': 3,
                                                '300': 3,
                                                '60': 0,
                                                '10': 0,
                                                'more': 21}},
             'total_count': 101,
            }
        self.assertEqual(actual, expected)

    @asynctest.ignore_loop
    @patch('randtalkbot.stranger_service.StrangerService', Mock())
    @patch('randtalkbot.stranger_sender_service.StrangerSenderService', Mock())
    @patch('randtalkbot.talk.Talk', Mock())
    def test_update_stats__some_stats_in_db(self):
        from randtalkbot.stranger_service import StrangerService
        from randtalkbot.stranger_sender_service import StrangerSenderService
        from randtalkbot.talk import Talk
        stranger_service = StrangerService.get_instance.return_value
        stranger_service.get_full_strangers = get_strangers
        stranger_sender_service = StrangerSenderService.get_instance.return_value
        Talk.get_not_ended_talks.return_value = get_talks(NOT_ENDED_TALKS)
        Talk.get_ended_talks.return_value = get_talks(ENDED_TALKS)
        self.stats_service._update_stats = types.MethodType(self.update_stats, self.stats_service)
        # self.stats_service._stats is not None now.
        self.stats_service._update_stats()
        Talk.get_not_ended_talks.assert_called_once_with(after=datetime.datetime(1990, 1, 1))
        Talk.get_ended_talks.assert_called_once_with(after=datetime.datetime(1990, 1, 1))
        Talk.delete_old.assert_called_once_with(before=datetime.datetime(1990, 1, 1))
        stranger_service.get_cache_size.assert_called_once_with()
        stranger_sender_service.get_cache_size.assert_called_once_with()

    @asynctest.ignore_loop
    @patch('randtalkbot.stranger_service.StrangerService', Mock())
    @patch('randtalkbot.stranger_sender_service.StrangerSenderService', Mock())
    @patch('randtalkbot.talk.Talk', Mock())
    def test_update_stats__no_talks(self):
        from randtalkbot.stranger_service import StrangerService
        from randtalkbot.talk import Talk
        stranger_service = StrangerService.get_instance.return_value
        stranger_service.get_full_strangers.return_value = []
        Talk.get_not_ended_talks.return_value = []
        Talk.get_ended_talks.return_value = []
        self.stats_service._update_stats = types.MethodType(self.update_stats, self.stats_service)
        # self.stats_service._stats is not None now.
        self.stats_service._update_stats()
        self.assertEqual(
            json.loads(self.stats_service._stats.data_json),
            {'languages_count_distribution': [],
             'languages_popularity': [],
             'languages_to_orientation': [],
             'partner_sex_distribution': {},
             'sex_distribution': {},
             'talks_duration': {'average': 0,
                                'count': 0,
                                'distribution': {'10': 0,
                                                 '1800': 0,
                                                 '300': 0,
                                                 '60': 0,
                                                 'more': 0}},
             'talks_sent': {'average': 0,
                            'count': 0,
                            'distribution': {'16': 0,
                                             '256': 0,
                                             '4': 0,
                                             '64': 0,
                                             'more': 0}},
             'talks_waiting': {'average': 0,
                               'count': 0,
                               'distribution': {'10': 0,
                                                '10800': 0,
                                                '1800': 0,
                                                '300': 0,
                                                '60': 0,
                                                'more': 0}},
             'total_count': 0},
            )
