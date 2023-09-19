from argparse import Namespace
from flask import request
from json import dumps
from time import time_ns

from ...search import search
from ...render import renderers
from ...utils import format_timestamp, fix_date_range
from .. import app
from .utils import _login_required, _render_template, JSONResponse


@app.route("/search", methods=["GET"], defaults={"blog": "", "query": "", "page": 1})
@app.route("/search/<blog>", defaults={"query": "", "page": 1})
@app.route("/search/<blog>/<query>", defaults={"page": 1})
@app.route("/search/<blog>/<query>/page/<int:page>")
@_login_required
def search_get(blog, query, page):
    return _render_template("search.html.jinja", blog=blog, query=query, page=page)


@app.route("/search", methods=["POST"])
@_login_required
def search_post():
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
