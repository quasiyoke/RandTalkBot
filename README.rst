Rand Talk
=========

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

Testing
-------

::

    $ python3 -m unittest

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
* 0.4 Translate interface to different languages
* 1.0 Stickers
* 1.1 Customizable greetings message
* 1.2 /oops -- return last partner!
* 1.3 Don't talk with recent partners
* 1.4 Instant bots messages
* 1.5 Replies
