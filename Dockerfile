FROM python:3.6
MAINTAINER Petr Ermishkin <quasiyoke@gmail.com>

COPY randtalkbot/ /randtalkbot/
COPY docker-entrypoint.sh randtalkbot-runner.py README.md setup.py /

RUN python /setup.py install
CMD ["/docker-entrypoint.sh"]
