Rand Talk
=========

.. image:: https://coveralls.io/repos/quasiyoke/RandTalkBot/badge.svg?branch=dev&service=github
    :target: https://coveralls.io/github/quasiyoke/RandTalkBot?branch=dev

.. image:: https://travis-ci.org/quasiyoke/RandTalkBot.svg?branch=dev
    :target: https://travis-ci.org/quasiyoke/RandTalkBot

Bot matching you with a random person on Telegram. Chat with anonymous strangers `here <https://telegram.me/RandTalkBot>`_.

Deployment
----------

::

    $ virtualenv --python=/usr/bin/python3 randtalkbotenv
    $ source randtalkbotenv/bin/activate
    (randtalkbotenv) $ pip install https://github.com/quasiyoke/RandTalkBot/zipball/master

After that write ``randtalkbotenv/configuration.json`` file::

    {
        "database": {
            "host": "localhost",
            "name": "randtalk",
            "user": "randtalkbot",
            "password": "xwBUr3oobCXjqSvz4t"
            },
        "token": "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789"
    }

Create MySQL DB::

    CREATE DATABASE IF NOT EXISTS randtalk CHARACTER SET utf8 COLLATE utf8_general_ci;
    CREATE USER randtalkbot@localhost IDENTIFIED BY 'xwBUr3oobCXjqSvz4t';
    GRANT ALL ON randtalk.* TO randtalkbot@localhost;

Create necessary DB tables::

    (randtalkbotenv) $ randtalkbot install randtalkbotenv/configuration.json

Now you may run ``randtalkbot``::

    (randtalkbotenv) $ randtalkbot randtalkbotenv/configuration.json

List of supported commands
--------------------------

In @BotFather compatible format::

    begin - Begin looking for next stranger
    end - End talking
    setup - Choose sex and language
    help - Help for Rand Talk

Roadmap
-------

* 0.1 Simplest functionality
* 0.2 Storing data at MySQL
* 0.3 Partner's sex, language choosing
* 0.4 Translate interface to various languages
* 1.0 Stickers
* 1.1 Customizable greetings message
* 1.2 /oops -- return last partner!
* 1.3 Don't talk with recent partners
* 1.4 Instant bots messages
* 1.5 Replies

Contributing
------------

Translations
^^^^^^^^^^^^

We are interested in growing the number of Rand Talk's translations. You can help in doing that by translating some of ``.po`` files in ``randtalkbot/locale`` directory on your language. Feel free to send this files to quasiyoke@gmail.com

Building gettext files
^^^^^^^^^^^^^^^^^^^^^^

Use `verboselib <https://github.com/oblalex/verboselib>`_ to extract new messages::

    $ verboselib-manage.py extract -d randtalkbot -l en -l ru -o randtalkbot/locale

And to compile them::

    $ verboselib-manage.py compile -d randtalkbot/locale

Tests
^^^^^

Launch tests and observe code coverage.

::

    $ coverage run --source=randtalkbot -m unittest
    $ coverage report -m
