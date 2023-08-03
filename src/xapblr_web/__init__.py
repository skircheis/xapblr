from flask import Flask
from flask_assets import Environment, Bundle
from subprocess import Popen, PIPE

from .utils import get_data_dir


def pandoc_filter(_in, out, **kwargs):
    cmd = ["pandoc", "--to", "html"]
    pandoc = Popen(cmd, stdin=PIPE, stdout=PIPE, text=True)
    out.write((pandoc.communicate(_in.read()))[0])


data_dir = get_data_dir()
static_dir = data_dir / ".webstatic"

app = Flask(__name__)

assets = Environment(app)
assets.url = "assets"
assets.directory = str(static_dir)

md = Bundle("SEARCH.md", filters=pandoc_filter, output="SEARCH.md.html")
assets.register("md", md)
css = Bundle("style.sass", filters="sass", output="style.css")
assets.register("css", css)
js = Bundle("scripts.js", output="scripts.js")
assets.register("js", js)

from .views import *
