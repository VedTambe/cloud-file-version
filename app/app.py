import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.middleware.proxy_fix import ProxyFix
from mimetypes import guess_type
from .db import init_db, db
from .models import File
from .utils import normalize_file_key, safe_store_name

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.getenv("SECRET_KEY", "change-this-secret")
    max_mb = int(os.getenv("MAX_CONTENT_LENGTH_MB", "10"))
    app.config["MAX_CONTENT_LENGTH"] = max_mb * 1024 * 1024
    app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    init_db(app)
    with app.app_context():
        db.create_all()

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_file(e):
        flash(f"Max file size is {max_mb} MB.", "danger")
        return redirect(url_for("index"))

    @app.route("/")
    def index():
        all_files = File.query.order_by(File.file_key.asc(), File.version.desc()).all()
        grouped = {}
        for f in all_files:
            grouped.setdefault(f.file_key, []).append(f)
        return render_template("index.html", groups=grouped, max_mb=max_mb)

    @app.route("/upload", methods=["POST"])
    def upload():
        file = request.files.get("file")
        if not file or file.filename.strip() == "":
            flash("Please choose a file to upload.", "warning")
            return redirect(url_for("index"))

        original = file.filename
        file_key = normalize_file_key(original)

        latest = File.query.filter_by(file_key=file_key).order_by(File.version.desc()).first()
        next_version = (latest.version + 1) if latest else 1
        stored_name = safe_store_name(original, next_version)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], stored_name)
        file.save(save_path)

        size_bytes = os.path.getsize(save_path)
        mime_type = guess_type(save_path)[0]

        rec = File(
            file_key=file_key,
            original_filename=original,
            stored_filename=stored_name,
            version=next_version,
            size_bytes=size_bytes,
            mime_type=mime_type,
        )
        db.session.add(rec)
        db.session.commit()

        flash(f"Uploaded '{original}' as version {next_version}.", "success")
        return redirect(url_for("index"))

    @app.route("/view/<int:file_id>")
    def view_file(file_id):
        rec = File.query.get_or_404(file_id)
        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            rec.stored_filename,
            as_attachment=False,
            mimetype=rec.mime_type or "application/octet-stream",
            download_name=rec.original_filename,
            max_age=0,
        )

    @app.route("/download/<int:file_id>")
    def download_file(file_id):
        rec = File.query.get_or_404(file_id)
        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            rec.stored_filename,
            as_attachment=True,
            download_name=rec.original_filename,
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=False)
