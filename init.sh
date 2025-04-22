source .venv/bin/activate
xapblr index $BLOG_URL && systemctl --user enable --now xapblr-hourly@$BLOG_URL &
uwsgi --ini ./config/uwsgi/xapblr.ini -H ./.venv
