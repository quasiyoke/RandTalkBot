Rand Talk
=========

.. image:: https://coveralls.io/repos/quasiyoke/RandTalkBot/badge.svg?branch=dev&service=github
    :target: https://coveralls.io/github/quasiyoke/RandTalkBot?branch=dev

.. image:: https://travis-ci.org/quasiyoke/RandTalkBot.svg?branch=dev
    :target: https://travis-ci.org/quasiyoke/RandTalkBot

Telegram bot matching you with a random person of desired sex speaking on your language(s). Chat with anonymous strangers `here <https://telegram.me/RandTalkBot>`_. Rand Talk was written on Python 3.5 and `telepot <https://github.com/nickoala/telepot>`_ and uses MySQL to store users' preferences. Rand Talk's interface was translated on several languages. You're able to send any messages except replies and forwarded messages. Rand Talk rewards you with bonuses for people you invite using your individual link. To get this link, use @RandTalkBot as inline bot. The bot collects stats regularly. Rand Talk rewards you with more bonuses for the people of rare sex.

List of supported commands
--------------------------

In @BotFather compatible format::

    begin - Begin looking for next stranger
    end - End talking
    setup - Choose sex and languages
    help - Help for Rand Talk

Admins specified at ``admins`` configuration property are able to use the following additional commands::

    clear TELEGRAM_IDs — "Clear" specified users. Stop their coversations or clear "looking for partner" flag.
    pay TELEGRAM_ID AMOUNT GRATITUDE — Pay AMOUNT bonuses to TELEGRAM_ID and notify her with GRATITUDE.

Roadmap
-------

* 1.3 Don't talk with recent partners
* 1.4 Reports
* 1.5 Replies
* 1.6 Customizable greetings message
* 1.7 /oops command to ask your recent partner to connect together again

Deployment
----------

::

    $ virtualenv --python=/usr/bin/python3.5 randtalkbotenv
    $ source randtalkbotenv/bin/activate
    (randtalkbotenv) $ pip install https://github.com/quasiyoke/RandTalkBot/zipball/master

After that write ``randtalkbotenv/configuration.json`` file like that::

    {
        "admins": [31416, 271828],
        "database": {
            "host": "localhost",
            "name": "randtalk",
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
                    },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "simple",
                    "filename": "log.log",
                    "maxBytes": 10485760,
                    "backupCount": 10,
                    "encoding": "utf-8"
                    },
                "email": {
                    "class": "logging.handlers.SMTPHandler",
                    "level": "ERROR",
                    "formatter": "simple",
                    "mailhost": ["smtp.gmail.com", 587],
                    "fromaddr": "example1@gmail.com",
                    "toaddrs": ["example2@gmail.com"],
                    "subject": "[Rand Talk Error]",
                    "credentials": ["example1@gmail.com", "RM49p7XFB:Z6x@kCkv"],
                    "secure": []
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

Create MySQL DB::

    CREATE DATABASE IF NOT EXISTS randtalk CHARACTER SET utf8 COLLATE utf8_general_ci;
    CREATE USER randtalkbot@localhost IDENTIFIED BY 'xwBUr3oobCXjqSvz4t';
    GRANT ALL ON randtalk.* TO randtalkbot@localhost;

Create necessary DB tables::

    (randtalkbotenv) $ randtalkbot install randtalkbotenv/configuration.json

Now you may run ``randtalkbot``::

    (randtalkbotenv) $ randtalkbot randtalkbotenv/configuration.json

Updating using SSH
^^^^^^^^^^^^^^^^^^

I'm using such shell script for semi-automatic deployment::

    #!/bin/bash
    cd path/to/randtalkbotenv/
    source bin/activate
    echo "y" | pip uninstall randtalkbot
    pip install https://github.com/quasiyoke/RandTalkBot/zipball/master
    killall randtalkbot
    nohup randtalkbot configuration.json &

Just launch::

    $ ssh john_doe@8.8.8.8 "bash -s" < deploy.sh

Contributing
------------

We are glad to see your contributions to RandTalk. Our reward starts from 10 bonuses for you.

Translations
^^^^^^^^^^^^

We are interested in growing the number of Rand Talk's translations. You can help in doing that by translating some of ``.po`` files in ``randtalkbot/locale`` directory on your language. Feel free to send this files to quasiyoke@gmail.com

Here's the list of bot translators. Take your chance to be here!

* English. Pyotr Ermishkin <quasiyoke@gmail.com>

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
