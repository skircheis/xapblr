from flask_login import current_user
from flask import redirect

from .. import app
from ...config import config


@app.route("/")
def index():
    if config["multi_user"] and current_user.is_authenticated:
        return redirect("/search")
    elif config["multi_user"]:
        return redirect("/login")
    else:
        return redirect("/search")


from .assets import *
from .clip import *
from .diagnostics import *
from .login import *
from .search import *
