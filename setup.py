# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
from setuptools import setup

# Looking for version number at randtalkbot/utils.py file.
with open('randtalkbot/utils.py') as f:
    version = re.search(
        '^__version__\s*=\s*\'(.*)\'',
        f.read(),
        re.M,
        ).group(1)

with open('README.rst', 'rb') as f:
    long_description = f.read().decode('utf-8')

setup(
    name='RandTalkBot',
    version=version,
    description='Bot matching you with a random person on Telegram.',
    long_description=long_description,
    keywords=['telegram', 'bot', 'anonymous', 'chat'],
    license='AGPLv3+',
    author='Pyotr Ermishkin',
    author_email='quasiyoke@gmail.com',
    url='https://github.com/quasiyoke/RandTalkBot',
    packages=['randtalkbot'],
    entry_points={
        'console_scripts': ['randtalkbot = randtalkbot.randtalkbot:main'],
        },
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Communications :: Chat',
        ],
    install_requires=[
        'asyncio>=3.4.3,<4.0',
        'docopt>=0.6.2,<0.7',
        'peewee>=2.7.4,<3.0',
        'pymysql>=0.6.7,<0.7',
        'telepot>=5.0,<6.0',
        ],
    test_suite='tests',
    tests_require=[
        'asynctest',
        ],
    )
