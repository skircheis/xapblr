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


from .assets import send_asset
from .clip import clip_offer, clip_accept
from .diagnostics import list_blogs
from .login import login, logout, try_login
from .search import search_view, run_search
