import io
import os
import tempfile
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge

from utils.pdf_generator import create_pdf

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_TOTAL_UPLOAD_SIZE_BYTES = 500 * 1024 * 1024

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_TOTAL_UPLOAD_SIZE_BYTES
app.config["CORS_HEADERS"] = "Content-Type"

CORS(app)


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(error):
    return (
        jsonify(
            {
                "error": (
                    f"Uploaded files are too large. Maximum upload size is {MAX_TOTAL_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
                )
            }
        ),
        413,
    )


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def allowed_file(filename: str) -> bool:
    return "." in filename and Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def get_upload_size(uploaded_file) -> int:
    content_length = getattr(uploaded_file, "content_length", None)
    if content_length is not None:
        return int(content_length)

    try:
        uploaded_file.stream.seek(0, os.SEEK_END)
        size = uploaded_file.stream.tell()
        uploaded_file.stream.seek(0)
        return int(size)
    except (AttributeError, OSError, ValueError):
        return 0


@app.route("/")
def home():
    return jsonify(
        {
            "status": "SnapPDF backend is ready",
            "message": "Send a POST request to /convert with image files.",
        }
    )


@app.route("/convert", methods=["OPTIONS", "POST"])
def convert_images():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    uploaded_files = request.files.getlist("images")
    actual_files = [file for file in uploaded_files if file and getattr(file, "filename", None)]
    compression = request.form.get("compression", "medium").lower().strip()

    if not actual_files:
        return (
            jsonify(
                {
                    "error": "No images were uploaded. Please add JPG, PNG, or WEBP files."
                }
            ),
            400,
        )

    total_upload_size = 0
    for uploaded_file in actual_files:
        if not allowed_file(uploaded_file.filename):
            return (
                jsonify(
                    {
                        "error": "Unsupported format. Please upload JPG, PNG, or WEBP images only."
                    }
                ),
                400,
            )

        total_upload_size += get_upload_size(uploaded_file)
        if total_upload_size > MAX_TOTAL_UPLOAD_SIZE_BYTES:
            return (
                jsonify(
                    {
                        "error": (
                            f"Total upload size exceeds {MAX_TOTAL_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB. "
                            "Please upload fewer or smaller images."
                        )
                    }
                ),
                400,
            )

    with tempfile.TemporaryDirectory(prefix="snappdf_") as temp_dir:
        temp_path = Path(temp_dir)
        image_paths = []

        try:
            for uploaded_file in actual_files:
                extension = Path(uploaded_file.filename).suffix.lower()
                temporary_name = f"{uuid.uuid4().hex}{extension}"
                saved_path = temp_path / temporary_name
                uploaded_file.save(saved_path)
                image_paths.append(str(saved_path))

            if not image_paths:
                return (
                    jsonify(
                        {"error": "No valid image files were received. Please upload image files."}
                    ),
                    400,
                )

            pdf_buffer = io.BytesIO()
            create_pdf(
                image_paths=image_paths,
                output_file=pdf_buffer,
                compression=compression,
                temp_dir=temp_path,
            )
            pdf_buffer.seek(0)

            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name="SnapPDF.pdf",
                mimetype="application/pdf",
                max_age=0,
            )

        except ValueError as exc:
            app.logger.warning("SnapPDF validation failed: %s", exc)
            return jsonify({"error": str(exc)}), 400
        except Exception:
            app.logger.exception("SnapPDF conversion failed")
            return (
                jsonify(
                    {
                        "error": (
                            "Unable to generate the PDF right now. "
                            "Please verify your images and try again."
                        )
                    }
                ),
                500,
            )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
