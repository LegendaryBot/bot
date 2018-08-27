FROM python:3.6.6-alpine

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir /config
ADD requirements.txt /config/

#We install the build dependencies in alpine
RUN set -ex \
    && apk add --no-cache --virtual .build-deps  \
		bzip2-dev \
		coreutils \
		dpkg-dev dpkg \
		expat-dev \
		gcc \
		gdbm-dev \
		libc-dev \
		libffi-dev \
		linux-headers \
		make \
		ncurses-dev \
		libressl \
		libressl-dev \
		pax-utils \
		readline-dev \
		sqlite-dev \
		tcl-dev \
		tk \
		tk-dev \
		xz-dev \
        zlib-dev \
        postgresql-dev \
        git \
        && apk add postgresql \
        && pip install -r /config/requirements.txt \
        && pip install -U git+https://github.com/legendarybot/website.git#egg=legendarybot-website \
        && pip install -U git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py \
        && apk del .build-deps
RUN mkdir /code
WORKDIR /code
CMD python bot.py