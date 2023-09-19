from flask import abort, request, Response
from json import dumps

from ..controllers.clip import offer, accept
from ...config import config
from .. import app


def _authenticate(token):
    try:
        if token != config["clip"]["auth_token"]:
            abort(401)
    except KeyError:
        abort(500)


@app.route("/clip", methods=["GET"])
def clip_offer():
    _authenticate(request.args.get("auth_token", ""))
    if "agent" not in request.args.keys():
        abort(400)
    out = offer(request.args)
    return Response(dumps(out), mimetype="application/json")


@app.route("/clip", methods=["POST"])
def clip_accept():
    data = request.json
    _authenticate(data.get("auth_token", ""))

    imgs = data.get("images", None) or abort(400)
    imgs = {i["id"]: i for i in imgs}
    accept(imgs)
    return Response("{}", mimetype="application/json")
