import os
import uuid
from flask import Flask, render_template, request, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
import qrcode

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 2592000  # Cache static files for 30 days
app.config["TEMPLATES_AUTO_RELOAD"] = False

UPLOAD_FOLDER = "static/uploads"
QR_FOLDER = "static/qr"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
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


@app.route("/uploads")
def uploads():
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

    return render_template("uploads.html", uploads=uploads)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)