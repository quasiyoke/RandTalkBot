# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import datetime
import logging
from .stats import Stats
from peewee import *

COUNT_INTERVALS = (4, 16, 64, 256)
LOGGER = logging.getLogger('randtalkbot.stats_service')

def get_talks_stats(talks, get_value, intervals):
    distribution = {interval: 0 for interval in intervals}
    distribution['more'] = 0
    average = 0
    count = 0
    for talk in talks:
        value = get_value(talk)
        increment_distribution(distribution, value, intervals)
        average += value
        count += 1
    try:
        average /= count
    except ZeroDivisionError:
        pass
    return {
        'distribution': distribution,
        'average': average,
        'count': count,
        }

def increment(d, key):
    try:
        d[key] += 1
    except KeyError:
        d[key] = 1

def increment_distribution(d, value, intervals):
    for interval in intervals:
        if value <= interval:
            break
    else:
        interval = 'more'
    d[interval] += 1

class StatsService:
    INTERVAL = datetime.timedelta(hours=4)

    def __init__(self):
        type(self)._instance = self
        try:
            self._stats = Stats.select().order_by(Stats.created.desc()).get()
        except DoesNotExist:
            self._stats = None
            self._update_stats()

    @classmethod
    def get_instance(cls):
        try:
            return cls._instance
        except AttributeError:
            raise RuntimeError('StatsService was not initialized')

    def get_stats(self):
        return self._stats

    async def run(self):
        while True:
            next_stats_time = self._stats.created + type(self).INTERVAL
            now = datetime.datetime.utcnow()
            if next_stats_time > now:
                await asyncio.sleep((next_stats_time - now).total_seconds())
            self._update_stats()

    def _update_stats(self):
        from .stranger_service import StrangerService
        from .stranger_sender_service import StrangerSenderService
        from .talk import Talk
        stats = Stats()
        stranger_service = StrangerService.get_instance()

        sex_distribution = {}
        partner_sex_distribution = {}
        languages_count_distribution = {}
        languages_popularity = {}
        total_count = 0
        for stranger in stranger_service.get_full_strangers():
            total_count += 1
            increment(sex_distribution, stranger.sex)
            increment(partner_sex_distribution, stranger.partner_sex)
            increment(languages_count_distribution, len(stranger.get_languages()))
            for language in stranger.get_languages():
                increment(languages_popularity, language)
        languages_count_distribution_items = list(languages_count_distribution.items())
        languages_count_distribution_items.sort(key=lambda item: item[0])
        valuable_count = total_count / 100
        languages_popularity_items = [
            (language, popularity)
            for language, popularity in languages_popularity.items() if popularity >= valuable_count
            ]
        languages_popularity_items.sort(key=lambda item: item[1], reverse=True)

        languages_to_orientation = {language: {} for language, popularity in languages_popularity_items}
        for stranger in stranger_service.get_full_strangers():
            orientation = '{} {}'.format(stranger.sex, stranger.partner_sex)
            for language in stranger.get_languages():
                try:
                    orientation_distribution = languages_to_orientation[language]
                except KeyError:
                    continue
                increment(orientation_distribution, orientation)
        languages_to_orientation_items = [
            (language, languages_to_orientation[language])
            for language, popularity in languages_popularity_items
            ]

        talks_waiting = get_talks_stats(
            Talk.get_not_ended_talks(after=None if self._stats is None else self._stats.created),
            lambda talk: (talk.begin - talk.searched_since).total_seconds(),
            (10, 60, 60 * 5, 60 * 30, 60 * 60 * 3, ),
            )

        ended_talks = Talk.get_ended_talks(after=None if self._stats is None else self._stats.created)
        talks_duration = get_talks_stats(
            ended_talks,
            lambda talk: (talk.end - talk.begin).total_seconds(),
            (10, 60, 60 * 5, 60 * 30, ),
            )
        talks_sent = get_talks_stats(
            ended_talks,
            lambda talk: talk.partner1_sent + talk.partner2_sent,
            COUNT_INTERVALS,
            )

        if self._stats is not None:
            Talk.delete_old(before=self._stats.created)

        stats_json = {
            'languages_count_distribution': languages_count_distribution_items,
            'languages_popularity': languages_popularity_items,
            'languages_to_orientation': languages_to_orientation_items,
            'partner_sex_distribution': partner_sex_distribution,
            'sex_distribution': sex_distribution,
            'total_count': total_count,
            'talks_duration': talks_duration,
            'talks_sent': talks_sent,
            'talks_waiting': talks_waiting,
            }
        stats.set_data(stats_json)
        stats.save()
        self._stats = stats
        LOGGER.info('Stats were updated')
        LOGGER.debug(
            'StrangerService cache size: %d',
            StrangerService.get_instance().get_cache_size(),
            )
        LOGGER.debug(
            'StrangerSenderService cache size: %d',
            StrangerSenderService.get_instance().get_cache_size(),
            )
