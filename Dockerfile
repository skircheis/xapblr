#syntax=docker/dockerfile:1.9
FROM archlinux:base-devel

RUN pacman -Syu --noconfirm git python uwsgi uwsgi-plugin-python xapian-core pandoc-cli dart-sass

COPY --from=ghcr.io/astral-sh/uv:0.4.9 /uv /bin/uv

RUN useradd -m xapblr

USER xapblr
WORKDIR /home/xapblr

RUN uv venv

COPY --chown=xapblr ./ /home/xapblr

RUN uv pip install ./

COPY --chown=xapblr ./src/xapblr/config.json /home/xapblr/.config/xapblr/config.json

EXPOSE 5000
ENTRYPOINT [ "/bin/sh", "./init.sh" ]