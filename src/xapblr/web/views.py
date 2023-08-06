from argparse import Namespace
from importlib import metadata
from json import dumps
from time import time_ns
from sqlalchemy import select

from ..config import config
from ..database import db, User
from ..utils import fix_date_range, get_data_dir

from flask import (
    redirect,
    render_template,
    request,
    Response,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_user, logout_user, login_required
from . import app

version = metadata.version("xapblr")


def _render_template(*args, **kwargs):
    return render_template(*args, **kwargs, config=config)


def _login_required(f):
    if config["multi_user"]:
        return login_required(f)
    else:
        return f


def JSONResponse(x):
    return Response(dumps(x), mimetype="application/json")


@app.route("/")
def index():
    if config["multi_user"] and current_user.is_authenticated:
        return redirect("/search")
    elif config["multi_user"]:
        return redirect("/login")
    else:
        return redirect("/search")


@app.route("/login", methods=["GET"])
def login():
    if config["multi_user"]:
        return _render_template("login.html.jinja", version=version)
    else:
        return redirect("/search")


@app.route("/login", methods=["POST"])
def do_login():
    try:
        user = request.json["username"]
    except KeyError:
        return JSONResponse({"success": False, "message": "username required"})
    try:
        password = request.json["password"]
    except KeyError:
        return JSONResponse({"success": False, "message": "password required"})

    with db.session() as s:
        q = select(User).where((User.name == user) | (User.email == user))
        authenticated = None
        for c in s.scalars(q):
            if c.salt_hash_and_digest(password) == c.password:
                authenticated = c
                break

    if authenticated is not None:
        login_user(authenticated)
        return JSONResponse({"success": True, "message": f"Welcome {authenticated.name}"})
    else:
        return JSONResponse({"success": False, "message": "invalid credentials"})


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/search", methods=["GET"], defaults={"blog": "", "query": "", "page": 1})
@app.route("/search/<blog>", defaults={"query": "", "page": 1})
@app.route("/search/<blog>/<query>", defaults={"page": 1})
@app.route("/search/<blog>/<query>/page/<int:page>")
@_login_required
def prefilled(blog, query, page):
    return _render_template(
        "search.html.jinja", blog=blog, query=query, page=page, version=version
    )


@app.route("/search", methods=["POST"])
@_login_required
def search():
    from xapblr.search import search
    from xapblr.render import renderers
    from xapblr.utils import format_timestamp

    pagesize = 50
    # TODO make this configurable?

    args = Namespace()
    args.width = None
    args.limit = pagesize
    try:
        page = int(request.json.get("page", 1)) - 1
    except (IndexError, ValueError):
        page = 0
    args.offset = pagesize * page
    for k, v in request.json.items():
        setattr(args, k, v)
    args.search = [fix_date_range(request.json["query"])]
    # return vars(args)
    allowed_renderers = ["plain", "html", "embed"]
    if args.render not in allowed_renderers:
        return dumps({"error": "Invalid renderer: " + args.render + "."})
    renderer = renderers[args.render]
    start = time_ns()
    res = search(args)
    out = {"results": [], "meta": res[0]}
    for m in res[1]:
        m["rendered"] = renderer(m, args)
        [m.pop(k) for k in ["content", "trail", "blog"]]
        m["timestamp_hf"] = format_timestamp(m["timestamp"])
        out["results"].append(m)
    stop = time_ns()
    out["meta"]["time_ns"] = stop - start
    out["meta"]["count"] = len(out["results"])

    return JSONResponse(out)


@app.route("/diagnostics")
def list_blogs():
    from xapblr.list import list_blogs as _list_blogs

    args = Namespace()
    return dumps(list(_list_blogs(args)))


@app.route("/assets/<path:path>")
def send_static(path):
    return send_from_directory(str(get_data_dir() / ".webstatic"), path)
