from flask import redirect, request, url_for
from flask_login import login_user, logout_user
from sqlalchemy import select
from time import time

from ...config import config
from ...db import get_db
from ...models.user import User
from .. import app
from .utils import _render_template, JSONResponse


@app.route("/login", methods=["GET"])
def login():
    if config["multi_user"]:
        return _render_template("login.html.jinja")
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

    db = get_db()
    with db.session() as s:
        q = select(User).where((User.name == user) | (User.email == user))
        authenticated = None
        for c in s.scalars(q):
            if c.salt_hash_and_digest(password) == c.password:
                authenticated = c
                break

        if authenticated is not None:
            authenticated.last_seen = int(time())
            login_user(authenticated)
            s.commit()
            return JSONResponse(
                {"success": True, "message": f"Welcome {authenticated.name}"}
            )
        else:
            return JSONResponse({"success": False, "message": "invalid credentials"})


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))
