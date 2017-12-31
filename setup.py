# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
from setuptools import setup, Command
from setuptools.command.test import test as SetuptoolsTestCommand
from randtalkbot.utils import __version__

with open('README.rst', 'rb') as file_descriptor:
    LONG_DESCRIPTION = file_descriptor.read() \
        .decode('utf-8')

class CoverageCommand(Command):
    user_options = []

    def initialize_options(self):
        # pylint: disable=attribute-defined-outside-init
        self.coveralls_args = []

    def finalize_options(self):
        pass

    def run(self):
        self.distribution.fetch_build_eggs(self.distribution.tests_require)
        from coveralls import cli
        cli.main(self.coveralls_args)

def lint(*options):
    from pylint.lint import Run
    run = Run(options, exit=False)

    if run.linter.msg_status != os.EX_OK:
        sys.exit(run.linter.msg_status)

class LintCommand(Command):
    user_options = []

    def initialize_options(self):
        # pylint: disable=attribute-defined-outside-init
        self.coveralls_args = []

    def finalize_options(self):
        pass

    def run(self):
        self.distribution.fetch_build_eggs(self.distribution.tests_require)
        lint(
            'randtalkbot',
            'setup',
            )
        lint(
            '''--disable=
                invalid-name,
                no-member,
                protected-access,
                redefined-variable-type,
                reimported,
            ''',
            'tests',
            )

class TestCommand(SetuptoolsTestCommand):
    def finalize_options(self):
        super(TestCommand, self).finalize_options()
        self.test_args = []
        # pylint: disable=attribute-defined-outside-init
        self.test_suite = True

    def run_tests(self):
        import coverage.cmdline
        sys.exit(coverage.cmdline.main(argv=['run', '--source=randtalkbot', '-m', 'unittest']))

setup(
    name='RandTalkBot',
    version=__version__,
    description='Telegram bot matching you with a random person of desired sex speaking on your'
    ' language(s).',
    long_description=LONG_DESCRIPTION,
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
        'Framework :: Telepot',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Topic :: Communications :: Chat',
        ],
    install_requires=[
        'docopt>=0.6.2,<0.7',
        'peewee>=2.7.4,<3.0',
        'pycountry>=1.19,<2.0',
        'pymysql>=0.6.7,<0.7',
        'telepot>=12.0,<13.0',
        ],
    tests_require=[
        'asynctest>=0.6,<0.7',
        'coveralls>=1.2.0,<1.3',
        'pylint>=1.8.1,<1.9',
        ],
    cmdclass={
        'coverage': CoverageCommand,
        'lint': LintCommand,
        'test': TestCommand,
        },
    )
