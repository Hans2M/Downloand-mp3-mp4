"""
Media Downloader - Storage Manager
Gestión de almacenamiento con soporte para Android Storage Access Framework (SAF),
almacenamiento scoped y directorios públicos en Android y escritorio.
"""

import os
import sys
from typing import Optional

# Detección de plataforma Android
IS_ANDROID = "ANDROID_ARGUMENT" in os.environ or hasattr(sys, "getandroidapilevel")

class StorageManager:
    """Gestiona las rutas de almacenamiento y permisos en Android y Desktop."""

    def __init__(self, custom_subfolder: str = "MediaDownloader"):
        self.subfolder = custom_subfolder
        self.download_dir = self._resolve_download_dir()

    def _resolve_download_dir(self) -> str:
        """Determina la ruta de descarga óptima según el entorno."""
        if IS_ANDROID:
            try:
                from jnius import autoclass
                Environment = autoclass("android.os.Environment")
                # Acceso a /storage/emulated/0/Download
                public_download_dir = Environment.getExternalStoragePublicDirectory(
                    Environment.DIRECTORY_DOWNLOADS
                ).getAbsolutePath()
                target = os.path.join(public_download_dir, self.subfolder)
                os.makedirs(target, exist_ok=True)
                return target
            except Exception as e:
                print(f"[Storage] Error accediendo a Environment de Android: {e}")
                # Fallback al directorio interno de la app
                from android.storage import primary_external_storage_path # type: ignore
                target = os.path.join(primary_external_storage_path(), "Download", self.subfolder)
                os.makedirs(target, exist_ok=True)
                return target
        else:
            # Entorno de pruebas / Desktop / Linux / Windows
            user_home = os.path.expanduser("~")
            target = os.path.join(user_home, "Downloads", self.subfolder)
            os.makedirs(target, exist_ok=True)
            return target

    def get_output_path(self, filename: str) -> str:
        """Devuelve la ruta completa para un archivo destino asegurando nombres únicos."""
        base_name, ext = os.path.splitext(filename)
        candidate = os.path.join(self.download_dir, filename)
        counter = 1
        while os.path.exists(candidate):
            candidate = os.path.join(self.download_dir, f"{base_name}_{counter}{ext}")
            counter += 1
        return candidate

    def scan_media_file(self, file_path: str) -> None:
        """Informa a Android MediaScanner para que el archivo aparezca en la galería/reproductor."""
        if not IS_ANDROID or not os.path.exists(file_path):
            return

        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            MediaScannerConnection = autoclass("android.media.MediaScannerConnection")
            context = PythonActivity.mActivity
            
            MediaScannerConnection.scanFile(
                context,
                [file_path],
                None,
                None
            )
            print(f"[Storage] MediaScannerConnection notificado para: {file_path}")
        except Exception as e:
            print(f"[Storage] Error al notificar a MediaScanner: {e}")

    def get_free_space_bytes(self) -> int:
        """Devuelve el espacio libre disponible en bytes."""
        try:
            stat = os.statvfs(self.download_dir)
            return stat.f_bavail * stat.f_frsize
        except Exception:
            return 0
