source .venv/bin/activate

python run.py & 

uwsgi --ini ./config/uwsgi/xapblr.ini -H ./.venv
