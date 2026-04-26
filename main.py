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
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 2592000  # Cache static files for 30 days
app.config["TEMPLATES_AUTO_RELOAD"] = False
app.secret_key = os.environ.get("SECRET_KEY", "q#y&g2^**X4R9h")

UPLOAD_FOLDER = "static/uploads"
QR_FOLDER = "static/qr"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

# Get credentials from environment
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

        file_url = url_for("static", filename=f"uploads/{filename}", _external=False)
        external_file_url = url_for("static", filename=f"uploads/{filename}", _external=True)
        qr_name = f"{os.path.splitext(filename)[0]}.png"
        qr_path = os.path.join(QR_FOLDER, qr_name)

        if not os.path.exists(qr_path):
            qr_img = qrcode.make(external_file_url)
            with open(qr_path, "wb") as f:
                qr_img.save(f)

        uploads.append({
            "name": filename,
            "file_url": file_url,
            "qr_image": url_for("static", filename=f"qr/{qr_name}")
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
    return redirect(url_for('index'))


@app.route("/uploads")
@login_required
def uploads():
    return render_template("uploads.html")


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    if "file" not in request.files:
        return "No file uploaded", 400

    file = request.files["file"]

    if not file or not file.filename:
        return "No file selected", 400

    filename = file.filename

    if "." not in filename:
        return "Invalid file type", 400

    ext = filename.rsplit(".", 1)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        return "Only PNG, JPG, JPEG, PDF allowed", 400

    random_name = f"{uuid.uuid4().hex}.{ext}"
    upload_path = os.path.join(UPLOAD_FOLDER, random_name)

    file.save(upload_path)

    file_url = url_for("static", filename=f"uploads/{random_name}", _external=True)

    qr_img = qrcode.make(file_url)
    qr_name = f"{os.path.splitext(random_name)[0]}.png"
    qr_path = os.path.join(QR_FOLDER, qr_name)

    if not os.path.exists(qr_path):
        with open(qr_path, "wb") as f:
            qr_img.save(f)

    return render_template(
        "result.html",
        file_url=file_url,
        qr_image=url_for("static", filename=f"qr/{qr_name}")
    )


@app.route("/delete/<filename>", methods=["POST"])
@login_required
def delete_file(filename):
    # Delete the uploaded file
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    # Delete the corresponding QR code
    qr_name = f"{os.path.splitext(filename)[0]}.png"
    qr_path = os.path.join(QR_FOLDER, qr_name)
    if os.path.exists(qr_path):
        os.remove(qr_path)

    flash(f"File '{filename}' deleted successfully!", "success")
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)