from argparse import Namespace
from flask import render_template, request, Response, send_from_directory
from json import dumps
from time import time_ns
from xapblr_web import app

from .utils import get_data_dir

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/list-blogs")
def list_blogs():
    from xapblr.list import list_blogs as l

    args = Namespace()
    return dumps(list(l(args)))

@app.route('/assets/<path:path>')
def send_static(path):
    return send_from_directory(str(get_data_dir() / ".webstatic"), path)

@app.route("/search", methods=["POST"])
def search():
    from xapblr.search import search
    from xapblr.render import renderers, render_plain, render_html, render_embed
    from xapblr.utils import format_timestamp

    args = Namespace()
    args.width = None
    args.limit = None
    for (k, v) in request.json.items():
        setattr(args, k, v)
    setattr(args, "search-term", [request.json["query"]])
    # return vars(args)
    allowed_renderers = ["plain", "html", "embed"]
    if args.render not in allowed_renderers:
        return dumps({"error": "Invalid renderer: " + args.render + "."})
    renderer = renderers[args.render]
    start = time_ns()
    matches = search(args)
    out = {"results": [], "meta": {}}
    for m in matches:
        m["rendered"] = renderer(m, args)
        [m.pop(k) for k in ["content", "trail", "blog"]]
        m["timestamp_hf"] = format_timestamp(m["timestamp"])
        out["results"].append(m)
    stop = time_ns()
    out["meta"]["time_ns"] = stop - start
    out["meta"]["count"] = len(out["results"])

    return Response(dumps(out), mimetype="application/json")
