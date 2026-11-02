"""
Media Downloader - Core Download Manager
Gestiona la cola de descargas concurrentes en hilos separados,
seguimiento en tiempo real de porcentaje, velocidad, bytes descargados y ETA.
"""

import os
import re
import sys
import time
import uuid
import threading
import subprocess
from typing import Dict, Any, Callable, Optional, List

from database.db_manager import DatabaseManager
from storage.storage_manager import StorageManager
from services.extractor import MediaExtractor
from services.converter import MediaConverter
from utils.helpers import sanitize_filename, format_bytes, format_time
from utils.android_notifications import AndroidNotificationManager

class DownloadTask:
    """Representa una tarea de descarga individual con estado en tiempo real."""

    def __init__(self, task_id: str, url: str, title: str, format_type: str, quality: str, thumbnail_url: str = "", duration: int = 0):
        self.id = task_id
        self.url = url
        self.title = title
        self.format = format_type.lower()  # 'mp3' o 'mp4'
        self.quality = quality
        self.thumbnail_url = thumbnail_url
        self.duration = duration

        # Estado en vivo
        self.status = "queued"  # queued, downloading, converting, completed, failed, cancelled
        self.progress = 0.0     # 0.0 a 100.0
        self.speed_str = "0 KB/s"
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.eta_str = "--:--"
        self.error_message = ""
        self.final_file_path = ""
        self.created_at = time.time()
        
        # Control de cancelación
        self.is_cancelled = False
        self.process: Optional[subprocess.Popen] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializa la tarea a un diccionario accesible para la interfaz."""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "format": self.format,
            "quality": self.quality,
            "thumbnail_url": self.thumbnail_url,
            "duration": self.duration,
            "status": self.status,
            "progress": round(self.progress, 1),
            "speed": self.speed_str,
            "downloaded_bytes": self.downloaded_bytes,
            "total_bytes": self.total_bytes,
            "downloaded_size_str": format_bytes(self.downloaded_bytes),
            "total_size_str": format_bytes(self.total_bytes),
            "eta": self.eta_str,
            "error_message": self.error_message,
            "file_path": self.final_file_path
        }


class DownloadManager:
    """Administrador centralizado de descargas y notificaciones."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None, storage_manager: Optional[StorageManager] = None):
        self.db = db_manager or DatabaseManager()
        self.storage = storage_manager or StorageManager()
        self.extractor = MediaExtractor()
        self.converter = MediaConverter()
        self.notifications = AndroidNotificationManager()
        
        self.tasks: Dict[str, DownloadTask] = {}
        self.max_concurrent = int(self.db.get_setting("max_concurrent", "2"))
        self._lock = threading.Lock()
        self.listeners: List[Callable[[Dict[str, Any]], None]] = []

    def add_listener(self, callback: Callable[[Dict[str, Any]], None]):
        """Registra una función oyente para eventos de progreso."""
        self.listeners.append(callback)

    def _notify_listeners(self, task: DownloadTask):
        """Dispara las actualizaciones hacia los observadores."""
        task_data = task.to_dict()
        for cb in self.listeners:
            try:
                cb(task_data)
            except Exception:
                pass

    def create_task(self, url: str, title: str, format_type: str, quality: str, thumbnail_url: str = "", duration: int = 0) -> str:
        """Crea una nueva tarea, la encola y arranca el hilo de procesamiento."""
        task_id = str(uuid.uuid4())[:8]
        task = DownloadTask(task_id, url, title, format_type, quality, thumbnail_url, duration)
        
        with self._lock:
            self.tasks[task_id] = task

        # Iniciar hilo de ejecución
        worker = threading.Thread(target=self._run_download, args=(task,), daemon=True)
        worker.start()
        
        self._notify_listeners(task)
        return task_id

    def cancel_task(self, task_id: str) -> bool:
        """Detiene una descarga en progreso y limpia temporales."""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return False
            task.is_cancelled = True
            task.status = "cancelled"
            if task.process and task.process.poll() is None:
                try:
                    task.process.terminate()
                except Exception:
                    pass
        
        self.notifications.cancel(abs(hash(task_id)) % 10000)
        self._notify_listeners(task)
        return True

    def _run_download(self, task: DownloadTask):
        """Flujo de trabajo de descarga con yt-dlp y conversión FFmpeg."""
        task.status = "downloading"
        notif_id = abs(hash(task.id)) % 10000
        
        clean_name = sanitize_filename(task.title)
        temp_dir = os.path.join(self.storage.download_dir, ".temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        ext = "mp3" if task.format == "mp3" else "mp4"
        final_filename = f"{clean_name}.{ext}"
        final_dest = self.storage.get_output_path(final_filename)

        if task.format == "mp3" and not self.converter.is_available():
            task.status = "failed"
            task.error_message = (
                "No se puede convertir a MP3 porque FFmpeg no está instalado "
                "o no está disponible."
            )
            self._notify_listeners(task)
            return

        # Configurar argumentos yt-dlp
        ytdlp_bin = self.extractor.binary_path
        
        output_template = os.path.join(temp_dir, f"{task.id}_%(title).50s.%(ext)s")

        # Cookies de YouTube
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cookies_path = os.path.join(base_dir, "data", "cookies.txt")
        cookie_args = ["--cookies", cookies_path] if os.path.exists(cookies_path) and os.path.getsize(cookies_path) > 10 else []

        common_args = [
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "--extractor-args", "youtube:player_client=android,web;player_skip=configs",
            *cookie_args
        ]
        if self.converter.is_available():
            # yt-dlp necesita localizar también ffprobe durante el postprocesado.
            ffmpeg_location = os.path.dirname(os.path.abspath(self.converter.ffmpeg_path))
            common_args.extend(["--ffmpeg-location", ffmpeg_location])

        if task.format == "mp3":
            # Extraer audio y convertir con FFmpeg
            cmd = [
                ytdlp_bin,
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", task.quality, # e.g. '320k'
                "--no-playlist",
                "--newline",
                "--progress",
                *common_args,
                "-o", output_template,
                task.url
            ]
        else: # mp4
            # Descargar video y audio combinados
            height_filter = "best"
            if task.quality == "1080p":
                height_filter = "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
            elif task.quality == "720p":
                height_filter = "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
            elif task.quality == "480p":
                height_filter = "bestvideo[height<=480]+bestaudio/best[height<=480]/best"
            elif task.quality == "360p":
                height_filter = "bestvideo[height<=360]+bestaudio/best[height<=360]/best"

            cmd = [
                ytdlp_bin,
                "-f", height_filter,
                "--merge-output-format", "mp4",
                "--no-playlist",
                "--newline",
                "--progress",
                *common_args,
                "-o", output_template,
                task.url
            ]

        try:
            task.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Patrones regex para capturar progreso yt-dlp
            # Ej: [download]  45.2% of  12.50MiB at  2.34MiB/s ETA 00:03
            prog_regex = re.compile(r'\[download\]\s+(\d+(?:\.\d+)?)%\s+of\s+~?(\d+(?:\.\d+)?\s*[KMGTP]?i?B)(?:\s+at\s+(\S+))?(?:\s+ETA\s+(\S+))?')

            downloaded_file = None
            process_output = []

            for line in iter(task.process.stdout.readline, ''):
                if task.is_cancelled:
                    break

                line_str = line.strip()
                if not line_str:
                    continue
                process_output.append(line_str)
                if len(process_output) > 20:
                    process_output.pop(0)

                match = prog_regex.search(line_str)
                if match:
                    percent_val = float(match.group(1))
                    task.progress = percent_val
                    total_str = match.group(2)
                    speed_val = match.group(3) or "1.2 MB/s"
                    eta_val = match.group(4) or "--:--"

                    task.speed_str = speed_val
                    task.eta_str = eta_val

                    # Actualizar notificación Android cada 10%
                    if int(task.progress) % 10 == 0:
                        self.notifications.show_progress(notif_id, task.title, int(task.progress), task.speed_str)

                    self._notify_listeners(task)

                # Detectar nombre final del archivo generado
                if "[Merger] Merging formats into" in line_str or "[ExtractAudio] Destination:" in line_str or "Destination:" in line_str:
                    parts = line_str.split("Destination:")
                    if len(parts) > 1:
                        downloaded_file = parts[1].strip().strip('"')
                    elif "into" in line_str:
                        downloaded_file = line_str.split("into")[-1].strip().strip('"')

            task.process.wait()

            if task.is_cancelled:
                task.status = "cancelled"
                self._notify_listeners(task)
                return

            if task.process.returncode != 0:
                task.status = "failed"
                task.error_message = (
                    "Error en yt-dlp: "
                    + (process_output[-1] if process_output else "salida no disponible")
                )
                self._notify_listeners(task)
                return

            # Buscar el archivo resultante en carpeta temporal si no se capturó
            if not downloaded_file or not os.path.exists(downloaded_file):
                for f in os.listdir(temp_dir):
                    if f.startswith(task.id):
                        downloaded_file = os.path.join(temp_dir, f)
                        break

            if downloaded_file and os.path.exists(downloaded_file):
                # Mover al destino final en la biblioteca
                import shutil
                shutil.move(downloaded_file, final_dest)
                task.final_file_path = final_dest
                task.status = "completed"
                task.progress = 100.0
                task.file_size = os.path.getsize(final_dest)

                # Registrar en la base de datos SQLite
                self.db.add_download({
                    "id": task.id,
                    "title": task.title,
                    "url": task.url,
                    "format": task.format,
                    "quality": task.quality,
                    "file_size": task.file_size,
                    "file_path": final_dest,
                    "thumbnail_url": task.thumbnail_url,
                    "duration": task.duration,
                    "status": "completed"
                })

                # Notificar a Android MediaScanner y alerta de finalización
                self.storage.scan_media_file(final_dest)
                self.notifications.show_completed(notif_id, task.title, final_dest)

            else:
                task.status = "failed"
                task.error_message = "No se localizó el archivo multimedia generado."

        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
        finally:
            self._notify_listeners(task)

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Lista todas las tareas activas o recientes."""
        with self._lock:
            return [task.to_dict() for task in self.tasks.values()]
