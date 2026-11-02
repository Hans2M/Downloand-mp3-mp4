"""Interfaz web local para Media Downloader.

La aplicación web reutiliza el motor existente de descargas y no modifica
el flujo de la aplicación Kivy/Android.
"""

import os
import sys
from typing import Any, Dict

from flask import Flask, jsonify, render_template, request, send_file

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.download_manager import DownloadManager
from database.db_manager import DatabaseManager
from services.extractor import MediaExtractor
from storage.storage_manager import StorageManager


app = Flask(__name__)
db_manager = DatabaseManager()
storage_manager = StorageManager()
download_manager = DownloadManager(db_manager, storage_manager)
extractor = MediaExtractor()


def error_response(message: str, status: int = 400):
    return jsonify({"success": False, "error": message}), status


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/analyze")
def analyze():
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    url = str(payload.get("url", "")).strip()
    if not url:
        return error_response("Introduce una URL para analizar.")
    return jsonify(extractor.analyze_url(url))


@app.post("/api/download")
def create_download():
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    required = ("url", "title", "format", "quality")
    missing = [field for field in required if not str(payload.get(field, "")).strip()]
    if missing:
        return error_response(f"Faltan datos: {', '.join(missing)}.")

    media_format = str(payload["format"]).lower()
    if media_format not in {"mp3", "mp4"}:
        return error_response("El formato debe ser MP3 o MP4.")

    task_id = download_manager.create_task(
        url=str(payload["url"]).strip(),
        title=str(payload["title"]).strip(),
        format_type=media_format,
        quality=str(payload["quality"]).strip(),
        thumbnail_url=str(payload.get("thumbnail", "")),
        duration=int(payload.get("duration") or 0),
    )
    return jsonify({"success": True, "task_id": task_id}), 202


@app.get("/api/tasks")
def tasks():
    return jsonify({"success": True, "tasks": download_manager.get_active_tasks()})


@app.post("/api/tasks/<task_id>/cancel")
def cancel_task(task_id: str):
    if not download_manager.cancel_task(task_id):
        return error_response("La tarea no existe.", 404)
    return jsonify({"success": True})


@app.get("/api/history")
def history():
    return jsonify({"success": True, "downloads": db_manager.get_all_downloads()})


@app.get("/api/files/<path:download_id>")
def download_file(download_id: str):
    record = db_manager.get_download_by_id(download_id)
    if not record or record.get("status") != "completed":
        return error_response("El archivo no está disponible.", 404)
    path = record.get("file_path", "")
    if not path or not os.path.isfile(path):
        return error_response("El archivo ya no existe en el almacenamiento.", 404)
    return send_file(path, as_attachment=True, download_name=os.path.basename(path))


if __name__ == "__main__":
    app.run(
        host=os.environ.get("MEDIA_DOWNLOADER_HOST", "127.0.0.1"),
        port=int(os.environ.get("MEDIA_DOWNLOADER_PORT", "5000")),
        debug=False,
    )
