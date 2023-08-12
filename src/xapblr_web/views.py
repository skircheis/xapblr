from argparse import Namespace
from flask import abort, render_template, request, Response, send_from_directory
from importlib import metadata
from json import dumps
from time import time_ns
from xapblr_web import app

from .utils import get_data_dir
from xapblr.utils import fix_date_range
from xapblr.config import config

from .controllers.clip import clip_offer, clip_accept

version = metadata.version("xapblr")


@app.route("/")
def index():
    return render_template("index.html", version=version)


@app.route("/<blog>", defaults={"query": "", "page": 1})
@app.route("/<blog>/<query>", defaults={"page": 1})
@app.route("/<blog>/<query>/page/<int:page>")
def prefilled(blog, query, page):
    return render_template(
        "index.html", blog=blog, query=query, page=page, version=version
    )


@app.route("/list-blogs")
def list_blogs():
    from xapblr.list import list_blogs as _list_blogs

    args = Namespace()
    return dumps(list(_list_blogs(args)))


@app.route("/assets/<path:path>")
def send_static(path):
    return send_from_directory(str(get_data_dir() / ".webstatic"), path)


@app.route("/search", methods=["POST"])
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

    return Response(dumps(out), mimetype="application/json")

def clip_authenticate(token):
    try:
        if token != config["clip"]["auth_token"]:
            abort(401)
    except KeyError:
        abort(500)

@app.route("/clip", methods=["GET"])
def clip_offer_view():
    clip_authenticate(request.args.get("auth_token", ""))
    try:
        agent = request.args["agent"]
    except KeyError:
        abort(400)
    out = clip_offer(request.args)
    return Response(dumps(out), mimetype="application/json")


@app.route("/clip", methods=["POST"])
def clip_accept_view():
    data = request.json
    clip_authenticate(data.get("auth_token", ""))

    imgs = data.get("images", None) or abort(400)
    imgs = {i["id"]: i for i in imgs}
    clip_accept(imgs)
    return Response("{}", mimetype="application/json")
