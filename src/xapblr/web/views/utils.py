from flask import render_template, Response
from flask_login import login_required
from importlib import metadata
from json import dumps
from ...config import config


def _render_template(*args, **kwargs):
    version = metadata.version("xapblr")
    return render_template(*args, **kwargs, config=config, version=version)


def _login_required(f):
    if config["multi_user"]:
        return login_required(f)
    else:
        return f


def JSONResponse(x):
    return Response(dumps(x), mimetype="application/json")
