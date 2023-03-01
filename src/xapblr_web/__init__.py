from flask import Flask
from flask_assets import Environment, Bundle
from subprocess import Popen, PIPE
from os import environ
from pathlib import Path


def get_data_dir():
    try:
        xdg_data_home = Path(environ["XDG_DATA_HOME"])
    except KeyError:
        xdg_data_home = Path(environ["HOME"]) / ".local/share"
    return xdg_data_home / "xapblr"


def pandoc_filter(_in, out, **kwargs):
    cmd = ["pandoc", "--to", "html"]
    pandoc = Popen(cmd, stdin=PIPE, stdout=PIPE, text=True)
    out.write((pandoc.communicate(_in.read()))[0])


app = Flask(__name__)

data_dir = get_data_dir()
assets = Environment(app, )
assets.directory=data_dir
assets.load_path=[str(Path(__file__).parent / "static")]


md = Bundle("SEARCH.md", filters=pandoc_filter, output="SEARCH.md.html")
assets.register("md", md)
css = Bundle("style.sass", filters="sass", output="style.css")
assets.register("css", css)

from .views import *
