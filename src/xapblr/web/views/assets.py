from flask import send_from_directory
from ...utils import get_data_dir
from .. import app


@app.route("/assets/<path:path>")
def send_static(path):
    return send_from_directory(str(get_data_dir() / ".webstatic"), path)
