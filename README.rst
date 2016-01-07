Rand Talk
=========

Bot matching you with a random person on Telegram. Chat with anonymous strangers here: https://telegram.me/RandTalkBot

Deployment
----------

::

    $ virtualenv --python=/usr/bin/python3 randtalkbotenv
    $ source randtalkbotenv/bin/activate
    (randtalkbotenv) $ pip install git+git://github.com/quasiyoke/RandTalkBot.git#egg=randtalkbot

After that write ``randtalkbotenv/configuration.json`` file::

    {
        "token": "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789"
    }

Now you may run ``randtalkbot``::

    (randtalkbotenv) $ randtalkbot randtalkbotenv/configuration.json

List of supported commands
--------------------------

In @BotFather compatible format::

    begin - Begin looking for next stranger
    end - End talking
    help - Help for Rand Talk
