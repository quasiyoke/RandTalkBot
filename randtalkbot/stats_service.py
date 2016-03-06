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

LOGGER = logging.getLogger('randtalkbot.stats_service')

def increment(d, key):
    try:
        d[key] += 1
    except KeyError:
        d[key] = 1

class StatsService:
    INTERVAL = datetime.timedelta(seconds=4 * 60 * 60)

    def __init__(self, stranger_service):
        self._stranger_service = stranger_service
        try:
            self._stats = Stats.select().order_by(Stats.created).get()
        except DoesNotExist:
            self._update_stats()

    def get_stats(self):
        return self._stats

    @asyncio.coroutine
    def run(self):
        while True:
            next_stats_time = self._stats.created + type(self).INTERVAL
            now = datetime.datetime.utcnow()
            if next_stats_time > now:
                yield from asyncio.sleep((next_stats_time - now).total_seconds())
            self._update_stats()

    def _update_stats(self):
        stats = Stats()

        sex_distribution = {}
        partner_sex_distribution = {}
        languages_count_distribution = {}
        languages_popularity = {}
        total_count = 0
        for stranger in self._stranger_service.get_full_strangers():
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
        for stranger in self._stranger_service.get_full_strangers():
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

        stats_json = {
            'languages_count_distribution': languages_count_distribution_items,
            'languages_popularity': languages_popularity_items,
            'languages_to_orientation': languages_to_orientation_items,
            'partner_sex_distribution': partner_sex_distribution,
            'sex_distribution': sex_distribution,
            'total_count': total_count,
            }
        stats.set_data(stats_json)
        stats.save()
        self._stats = stats
        LOGGER.info('Stats were updated')
