"""
Media Downloader - Converter Service
Módulo de conversión multimedia mediante FFmpeg.
Maneja extracción de audio MP3 y re-empaquetado de vídeo MP4 en alta calidad.
"""

import os
import shutil
import subprocess
import glob
from typing import Optional, Tuple

class MediaConverter:
    """Ejecuta transformaciones con FFmpeg de forma segura y eficiente."""

    def __init__(self, ffmpeg_binary: Optional[str] = None):
        self.ffmpeg_path = ffmpeg_binary or self._find_ffmpeg()

    @staticmethod
    def _find_ffmpeg() -> str:
        """Localiza FFmpeg en PATH o en instalaciones comunes de Windows."""
        path = shutil.which("ffmpeg")
        if path:
            return path

        candidates = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "ffmpeg", "bin", "ffmpeg.exe"),
            r"C:\ffmpeg\bin\ffmpeg.exe",
        ]
        winget_pattern = os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "Microsoft", "WinGet", "Packages", "*", "*", "bin", "ffmpeg.exe"
        )
        candidates.extend(glob.glob(winget_pattern))
        return next((candidate for candidate in candidates if os.path.isfile(candidate)), "ffmpeg")

    def is_available(self) -> bool:
        """Verifica si FFmpeg está instalado y disponible en el sistema."""
        try:
            res = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                check=False
            )
            return res.returncode == 0
        except Exception:
            return False

    def convert_to_mp3(self, input_file: str, output_file: str, bitrate: str = "320k", title: str = "") -> Tuple[bool, str]:
        """
        Extrae y codifica pista de audio a formato MP3 con el bitrate especificado
        e inserta metadatos ID3.
        """
        if not os.path.exists(input_file):
            return False, f"El archivo de entrada no existe: {input_file}"

        # Parámetros FFmpeg para audio limpio
        cmd = [
            self.ffmpeg_path,
            "-y",                   # Sobrescribir sin preguntar
            "-i", input_file,       # Archivo de entrada
            "-vn",                  # Omitir video
            "-ar", "44100",         # Frecuencia de muestreo estándar
            "-ac", "2",             # Canales estéreo
            "-b:a", bitrate,        # Tasa de bits seleccionada (e.g. 320k, 192k)
            "-codec:a", "libmp3lame",
            "-q:a", "0"
        ]

        if title:
            cmd.extend(["-metadata", f"title={title}"])

        cmd.append(output_file)

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if res.returncode == 0 and os.path.exists(output_file):
                return True, output_file
            return False, f"Fallo al convertir con FFmpeg: {res.stderr[:250]}"
        except Exception as e:
            return False, f"Excepción durante la conversión: {str(e)}"

    def merge_video_audio(self, video_file: str, audio_file: str, output_file: str) -> Tuple[bool, str]:
        """Combina un flujo de vídeo y un flujo de audio en un contenedor MP4 sin recodificar si es posible."""
        if not os.path.exists(video_file):
            return False, "Archivo de video no encontrado."

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", video_file,
            "-i", audio_file,
            "-c:v", "copy",
            "-c:a", "aac",
            "-strict", "experimental",
            output_file
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if res.returncode == 0 and os.path.exists(output_file):
                return True, output_file
            return False, f"Fallo en combinación de flujos: {res.stderr[:250]}"
        except Exception as e:
            return False, f"Excepción en merge: {str(e)}"
