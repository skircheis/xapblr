from flask import Flask
from flask_assets import Environment, Bundle
from flask_login import LoginManager
from subprocess import Popen, PIPE
from sys import exit

from ..config import config
from ..models.user import User
from .utils import get_data_dir
from .controllers.setup import setup


def pandoc_filter(_in, out, **kwargs):
    cmd = ["pandoc", "--to", "html"]
    pandoc = Popen(cmd, stdin=PIPE, stdout=PIPE, text=True)
    out.write((pandoc.communicate(_in.read()))[0])


data_dir = get_data_dir()
static_dir = data_dir / ".webstatic"


class XapblrWebServer(Flask):
    def run(self, *args, **kwargs):
        if config["multi_user"]:
            try:
                app.secret_key = config["secret_key"].encode("utf8")
            except KeyError:
                import secrets

                key = secrets.token_hex()
                exit(
                    f"In multi-user mode, a secret_key must be configured. Here is one you can use: {key}."
                )
            setup()

        Flask.run(self, *args, **kwargs)


app = XapblrWebServer(__name__)
assets = Environment(app)
assets.url = "assets"
assets.directory = str(static_dir)

md = Bundle("SEARCH.md", filters=pandoc_filter, output="SEARCH.md.html")
assets.register("md", md)
css = Bundle("style.sass", filters="sass", output="style.css")
assets.register("css", css)
js = Bundle("scripts.js", output="scripts.js")
assets.register("js", js)

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


login_manager.init_app(app)

from .views import *  # noqa: E402 F401 F403
