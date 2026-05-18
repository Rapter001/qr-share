import os
import uuid

from flask import (
    Flask, render_template, request,
    url_for, redirect, session, flash
)

from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from functools import wraps
from dotenv import load_dotenv

import qrcode
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# =========================
# ENV
# =========================
load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="/static")

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

app.secret_key = os.environ.get("SECRET_KEY", "change-me")

# =========================
# RATE LIMITER
# =========================
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# =========================
# FOLDERS
# =========================
UPLOAD_FOLDER = "static/files/uploads"
QR_FOLDER = "static/files/qr"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)

# =========================
# HELPERS
# =========================
def get_allowed_users():
    users = {}
    raw = os.environ.get("LOGIN", "")

    if raw:
        for pair in raw.split(","):
            if ":" in pair:
                u, p = pair.split(":", 1)
                users[u.strip()] = p.strip()

    return users


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "logged_in" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def allowed_file(filename):
    return (
        "." in filename and
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )

# =========================
# INDEX (GALLERY)
# =========================
@app.route("/")
@limiter.limit("30 per minute")
def index():
    uploads = []

    for f in sorted(os.listdir(UPLOAD_FOLDER), reverse=True):

        file_url = url_for("static", filename=f"files/uploads/{f}")
        qr_name = f"{os.path.splitext(f)[0]}.png"
        qr_url = url_for("static", filename=f"files/qr/{qr_name}")

        uploads.append({
            "name": f,
            "file_url": file_url,
            "qr_image": qr_url
        })

    return render_template("index.html", uploads=uploads)

# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        users = get_allowed_users()

        if username in users and users[username] == password:
            session["logged_in"] = True
            session["username"] = username
            flash("Login success", "success")
            return redirect(url_for("uploads"))

        flash("Invalid login", "error")

    return render_template("login.html")


@app.route("/logout")
@limiter.limit("10 per minute")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =========================
# UPLOAD PAGE
# =========================
@app.route("/uploads")
@login_required
@limiter.limit("30 per minute")
def uploads():
    return render_template("uploads.html")

# =========================
# UPLOAD (IMAGES ONLY)
# =========================
@app.route("/upload", methods=["POST"])
@login_required
@limiter.limit("10 per hour")
def upload():

    if "file" not in request.files:
        flash("No file", "error")
        return redirect(url_for("uploads"))

    file = request.files["file"]

    if not file.filename:
        flash("No file selected", "error")
        return redirect(url_for("uploads"))

    filename = secure_filename(file.filename)

    if not allowed_file(filename):
        flash("Only PNG, JPG, JPEG allowed", "error")
        return redirect(url_for("uploads"))

    ext = filename.rsplit(".", 1)[1].lower()
    uid = uuid.uuid4().hex

    image_name = f"{uid}.{ext}"
    image_path = os.path.join(UPLOAD_FOLDER, image_name)

    file.save(image_path)

    file_url = url_for(
        "static",
        filename=f"files/uploads/{image_name}",
        _external=True
    )

    # QR
    qr = qrcode.make(file_url)

    qr_name = f"{uid}.png"
    qr_path = os.path.join(QR_FOLDER, qr_name)

    with open(qr_path, "wb") as f:
        qr.save(f)

    return render_template(
        "result.html",
        file_url=file_url,
        preview_url=file_url,
        qr_image=url_for("static", filename=f"files/qr/{qr_name}")
    )

# =========================
# DELETE
# =========================
@app.route("/delete/<filename>", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def delete_file(filename):

    filename = secure_filename(filename)

    path = os.path.join(UPLOAD_FOLDER, filename)

    if os.path.exists(path):
        os.remove(path)

    return redirect(url_for("index"))

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)