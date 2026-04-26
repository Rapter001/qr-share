import os
import uuid
from flask import Flask, render_template, request, url_for, redirect, session, flash
from werkzeug.middleware.proxy_fix import ProxyFix
from functools import wraps
import qrcode
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 2592000  # 30 days cache
app.config["TEMPLATES_AUTO_RELOAD"] = False
app.secret_key = os.environ.get("SECRET_KEY", "q#y&g2^**X4R9h")

# ✅ UPDATED FOLDERS (all under /static/files/)
UPLOAD_FOLDER = "static/files/uploads"
QR_FOLDER = "static/files/qr"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

USERNAME = os.environ.get("APP_USERNAME")
PASSWORD = os.environ.get("APP_PASSWORD")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    uploads = []

    for filename in sorted(os.listdir(UPLOAD_FOLDER), reverse=True):
        if not allowed_file(filename):
            continue

        file_url = url_for("static", filename=f"files/uploads/{filename}")
        external_file_url = url_for("static", filename=f"files/uploads/{filename}", _external=True)

        qr_name = f"{os.path.splitext(filename)[0]}.png"
        qr_path = os.path.join(QR_FOLDER, qr_name)

        # Generate QR if missing
        if not os.path.exists(qr_path):
            qr_img = qrcode.make(external_file_url)
            with open(qr_path, "wb") as f:
                qr_img.save(f)

        uploads.append({
            "name": filename,
            "file_url": file_url,
            "qr_image": url_for("static", filename=f"files/qr/{qr_name}")
        })

    return render_template("index.html", uploads=uploads)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            flash("Login successful!", "success")
            return redirect(url_for('uploads'))
        else:
            flash("Invalid credentials!", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))


@app.route("/uploads")
@login_required
def uploads():
    return render_template("uploads.html")


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    if "file" not in request.files:
        flash("No file uploaded.", "error")
        return redirect(url_for("uploads"))

    file = request.files["file"]

    if not file or not file.filename:
        flash("No file selected.", "error")
        return redirect(url_for("uploads"))

    if "." not in file.filename:
        flash("Invalid file type. Please upload a PNG, JPG, or JPEG.", "error")
        return redirect(url_for("uploads"))

    ext = file.filename.rsplit(".", 1)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        flash("Only PNG, JPG, and JPEG files are allowed.", "error")
        return redirect(url_for("uploads"))

    random_name = f"{uuid.uuid4().hex}.{ext}"
    upload_path = os.path.join(UPLOAD_FOLDER, random_name)

    file.save(upload_path)

    file_url = url_for("static", filename=f"files/uploads/{random_name}", _external=True)

    # QR generation
    qr_img = qrcode.make(file_url)
    qr_name = f"{os.path.splitext(random_name)[0]}.png"
    qr_path = os.path.join(QR_FOLDER, qr_name)

    with open(qr_path, "wb") as f:
        qr_img.save(f)

    return render_template(
        "result.html",
        file_url=file_url,
        qr_image=url_for("static", filename=f"files/qr/{qr_name}")
    )


@app.route("/delete/<filename>", methods=["POST"])
@login_required
def delete_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    qr_name = f"{os.path.splitext(filename)[0]}.png"
    qr_path = os.path.join(QR_FOLDER, qr_name)

    if os.path.exists(qr_path):
        os.remove(qr_path)

    flash(f"File '{filename}' deleted successfully!", "success")
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)