# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
from randtalkbot.utils import __version__
from setuptools import setup, Command
from setuptools.command.test import test as SetuptoolsTestCommand

with open('README.rst', 'rb') as f:
    long_description = f.read().decode('utf-8')

class CoverageCommand(Command):
    user_options = []

    def initialize_options(self):
        self.coveralls_args = []

    def finalize_options(self):
        pass

    def run(self):
        self.distribution.fetch_build_eggs(self.distribution.tests_require)
        from coveralls import cli
        cli.main(self.coveralls_args)

class TestCommand(SetuptoolsTestCommand):
    def finalize_options(self):
        super(TestCommand, self).finalize_options()
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import sys, coverage.cmdline
        sys.exit(coverage.cmdline.main(argv=['run', '--source=randtalkbot', '-m', 'unittest']))

setup(
    name='RandTalkBot',
    version=__version__,
    description='Bot matching you with a random person on Telegram.',
    long_description=long_description,
    keywords=['telegram', 'bot', 'anonymous', 'chat'],
    license='AGPLv3+',
    author='Pyotr Ermishkin',
    author_email='quasiyoke@gmail.com',
    url='https://github.com/quasiyoke/RandTalkBot',
    packages=['randtalkbot'],
    package_data={
        'randtalkbot': ['locale/*/LC_MESSAGES/*.mo']
        },
    entry_points={
        'console_scripts': ['randtalkbot = randtalkbot.randtalkbot:main'],
        },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
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
        'pycountry>=1.19,<2.0',
        'pymysql>=0.6.7,<0.7',
        'telepot>=6.0,<7.0',
        ],
    tests_require=[
        'coveralls>=1.1,<2.0',
        ],
    cmdclass={
        'coverage': CoverageCommand,
        'test': TestCommand,
        },
    )
