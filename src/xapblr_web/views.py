from argparse import Namespace
from flask import render_template
from json import dumps
from xapblr_web import app


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/list-blogs")
def list_blogs():
    from xapblr.list import list_blogs as l

    args = Namespace()
    return dumps(list(l(args)))


@app.route("/search/<blog>/")
def search(blog):
    from xapblr.search import search
    from xapblr.render import render_html

    args = Namespace()
    args.blog = blog
    args.sort = "newest"
    args.limit = 10
    setattr(args, "search-term", ['tag:"senjougahara hitagi"'])
    return "\n".join([render_html(m, args) for m in search(args)])
