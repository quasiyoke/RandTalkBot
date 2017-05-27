Rand Talk
=========

.. image:: https://coveralls.io/repos/quasiyoke/RandTalkBot/badge.svg?branch=dev&service=github
    :target: https://coveralls.io/github/quasiyoke/RandTalkBot?branch=dev

.. image:: https://travis-ci.org/quasiyoke/RandTalkBot.svg?branch=dev
    :target: https://travis-ci.org/quasiyoke/RandTalkBot

Telegram bot matching you with a random person of desired sex speaking on your language(s). Chat with anonymous strangers `here <https://telegram.me/RandTalkBot>`_. Rand Talk was written on Python 3.6 and `telepot <https://github.com/nickoala/telepot>`_ and uses MySQL to store users' preferences. Rand Talk's interface was translated on several languages. You're able to send any messages except replies and forwarded messages. Rand Talk rewards you with bonuses for people you invite using your individual link. To get this link, use @RandTalkBot as inline bot. The bot collects stats regularly. Rand Talk rewards you with more bonuses for the people of rare sex.

Supported commands
------------------

In @BotFather compatible format::

    begin - Begin looking for next stranger
    end - End talking
    setup - Choose languages and sex
    help - Help for Rand Talk

Admins specified at ``admins`` configuration property are able to use the following additional commands::

    clear TELEGRAM_IDs — "Clear" specified users. Stop their coversations or clear "looking for partner" flag.
    pay TELEGRAM_ID AMOUNT GRATITUDE — Pay AMOUNT bonuses to TELEGRAM_ID and notify her with GRATITUDE.

Roadmap
-------

* 2.2 Reports
* 2.3 Replies
* 2.4 Customizable greetings message
* 2.5 /oops command to ask your recent partner to connect together again

Deployment
----------

::

    $ docker network create \
        --subnet=172.28.0.0/16 \
        randtalkbot
    $ docker run \
        --name=randtalkbot-mysql \
        --net=randtalkbot \
        --ip=172.28.0.50 \
        --env="MYSQL_ROOT_PASSWORD=P9u205LLeY8XyRt3fM8t77D8" \
        --env="MYSQL_DATABASE=randtalkbot" \
        --env="MYSQL_USER=randtalkbot" \
        --env="MYSQL_PASSWORD=xwBUr3oobCXjqSvz4t" \
        --detach \
        mysql:5.7
    $ git clone https://github.com/quasiyoke/RandTalkBot.git
    $ cd RandTalkBot
    $ docker build --tag=randtalkbot .

After that write ``configuration/configuration.json`` file like that::

    {
        "admins": [31416, 271828],
        "database": {
            "host": "172.28.0.50",
            "name": "randtalkbot",
            "user": "randtalkbot",
            "password": "xwBUr3oobCXjqSvz4t"
        },
        "logging": {
            "version": 1,
            "formatters": {
                "simple": {
                    "class": "logging.Formatter",
                    "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "simple"
                }
            },
            "loggers": {
                "randtalkbot": {
                    "level": "DEBUG",
                    "handlers": []
                },
                "peewee": {
                    "level": "DEBUG",
                    "handlers": []
                }
            },
            "root": {
                "level": "DEBUG",
                "handlers": ["console", "email"]
            }
        },
        "token": "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789"
    }

Where:

* ``admins`` — list of admins' Telegram IDs. Admins are able to use extended list of bot commands. Optional. Default is ``[]``.
* ``logging`` — logging setup as described in `this howto <https://docs.python.org/3/howto/logging.html>`_.

Now you may run Rand Talk::

    $ docker run \
        --name=randtalkbot \
        --net=randtalkbot \
        --volume=`pwd`/configuration:/configuration \
        --detach \
        randtalkbot

Contributing
------------

We are glad to see your contributions to Rand Talk. Our reward starts from 10 bonuses for you.

Translations
^^^^^^^^^^^^

We are interested in growing the number of Rand Talk's translations. You can help in doing that by translating some of ``.po`` files in ``randtalkbot/locale`` directory on your language. Feel free to send this files to quasiyoke@gmail.com

Here's the list of bot translators. Take your chance to be here!

* English. Pyotr Ermishkin <quasiyoke@gmail.com>

* German. Jonas Zohren <jfowl@wjclub.tk>

* Italian

  * Marco Giustetto <arducode@gmail.com>
  * Leonardo Guida <leonardo.99.torino@gmail.com>
  * Benedetta Facchinetti <zoidberglupin@gmail.com>
  * Martin Ligabue <martinligabue@gmail.com>

* Russian. Pyotr Ermishkin <quasiyoke@gmail.com>

* Spanish

  * Benedetta Facchinetti <zoidberglupin@gmail.com>
  * Martin Ligabue <martinligabue@gmail.com>

Building gettext files
^^^^^^^^^^^^^^^^^^^^^^

Use `verboselib <https://github.com/oblalex/verboselib>`_ to extract new messages::

    $ verboselib-manage.py extract -d randtalkbot -a -o randtalkbot/locale -i lib

And to compile them::

    $ verboselib-manage.py compile -d randtalkbot/locale

Tests
^^^^^

Launch tests and observe code coverage.

::

    $ coverage run --source=randtalkbot -m unittest
    $ coverage report -m

Launch some specific test.

::

    $ python -m unittest tests.test_stranger.TestStranger
