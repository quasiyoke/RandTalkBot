FROM python:3.6
MAINTAINER Pyotr Ermishkin <quasiyoke@gmail.com>

COPY randtalkbot /randtalkbot/
COPY docker-entrypoint.sh /
COPY randtalkbot-runner.py /
COPY README.rst /
COPY setup.py /

VOLUME /configuration

RUN python /setup.py install

CMD ["/docker-entrypoint.sh"]
