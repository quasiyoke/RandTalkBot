# Rand Talk

[![Build Status](https://coveralls.io/repos/quasiyoke/RandTalkBot/badge.svg?branch=dev&service=github)](https://coveralls.io/github/quasiyoke/RandTalkBot?branch=dev) [![Build Status](https://travis-ci.org/quasiyoke/RandTalkBot.svg?branch=dev)](https://travis-ci.org/quasiyoke/RandTalkBot)

Telegram bot matching you with a random person of desired sex speaking on your language(s). Chat with anonymous strangers [here](https://t.me/RandTalkBot). Rand Talk was written on Python 3.6 and [telepot](https://github.com/nickoala/telepot) and uses MariaDB to store users' preferences. Rand Talk's interface was translated on several languages. You're able to send any messages except replies and forwarded messages. Rand Talk rewards you with bonuses for people you invite using your individual link. To get this link, use @RandTalkBot as inline bot. The bot collects stats regularly. Rand Talk rewards you with more bonuses for the people of rare sex.

## Supported commands

In @BotFather compatible format:

```
begin - Begin looking for next stranger
end - End talking
setup - Choose languages and sex
help - Help for Rand Talk
```

Admins specified at `admins` configuration property are able to use the following additional commands:

```
clear TELEGRAM_IDs — "Clear" specified users. Stop their coversations or clear "looking for partner" flag.
pay TELEGRAM_ID AMOUNT GRATITUDE — Pay AMOUNT bonuses to TELEGRAM_ID and notify her with GRATITUDE.
```

## Roadmap

1. Reports
1. Replies
1. Customizable greetings message
1. /oops command to ask your recent partner to connect together again

## Deployment

We're using [Docker Compose](https://docs.docker.com/compose/install/) to deploy [Rand Talk's Docker container](https://hub.docker.com/r/quasiyoke/randtalkbot/).

Create `configuration/db_root_password` and `configuration/db_password` files containing database passwords and `configuration/telegram_token` containing Telegram bot's token. After that write `configuration/configuration.json` file like that:

```json
{
    "admins": [31416, 271828],
    "database": {
        "host": "db",
        "name": "randtalkbot",
        "user": "randtalkbot",
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
    }
}
```

Where:

- `admins` — list of admins' Telegram IDs. Admins are able to use extended list of bot commands. Optional. Default is `[]`.
- `logging` — logging setup as described in [this howto](https://docs.python.org/3/howto/logging.html).

Fetch Docker Compose file:

```sh
wget https://raw.githubusercontent.com/quasiyoke/RandTalkBot/master/docker-compose.yml
```

Now you may run Rand Talk:

```sh
docker-compose up -d
```

## Contributing

We are glad to see your contributions to Rand Talk. Our reward starts from 10 bonuses for you.

### Translations

We are interested in growing the number of Rand Talk's translations. You can help in doing that by translating some of `.po` files in `randtalkbot/locale` directory on your language. Feel free to send this files to quasiyoke@gmail.com

Here's the list of bot translators. Take your chance to be here!

- English. Pyotr Ermishkin <quasiyoke@gmail.com>

- German. Jonas Zohren <jfowl@wjclub.tk>

- Italian

  - Marco Giustetto <arducode@gmail.com>
  - Leonardo Guida <leonardo.99.torino@gmail.com>
  - Benedetta Facchinetti <zoidberglupin@gmail.com>
  - Martin Ligabue <martinligabue@gmail.com>

- Russian. Pyotr Ermishkin <quasiyoke@gmail.com>

- Spanish

  - Benedetta Facchinetti <zoidberglupin@gmail.com>
  - Martin Ligabue <martinligabue@gmail.com>

### Building gettext files

Use [verboselib](https://github.com/oblalex/verboselib) to extract new messages:

```sh
verboselib-manage.py extract -d randtalkbot -a -o randtalkbot/locale -i lib
```

And to compile them:

```sh
verboselib-manage.py compile -d randtalkbot/locale
```

### Deployment

To comfortably inject source code changes to the Docker container use another Docker Compose file:

```sh
docker-compose --file docker-compose.dev.yml up --abort-on-container-exit
```

### Tests

Launch tests and observe code coverage:

```sh
coverage run --source=randtalkbot -m unittest
coverage report -m
```

Launch some specific test:

```sh
python -m unittest tests.test_stranger.TestStranger
```

### Codestyle

Please notice that tests' source code is also covered with codestyle checks but requirements for it are softer:

```sh
python setup.py lint
```
