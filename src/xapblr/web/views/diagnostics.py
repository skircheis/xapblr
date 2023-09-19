from argparse import Namespace
from json import dumps
from ...list import list_blogs as _list_blogs
from .. import app


@app.route("/diagnostics")
def list_blogs():
    args = Namespace()
    return dumps(list(_list_blogs(args)))
