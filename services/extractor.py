"""
Media Downloader - Extractor Service
Módulo de extracción y análisis de enlaces multimedia mediante yt-dlp.
Analiza formatos disponibles, miniaturas, títulos, duraciones y estima tamaños.
"""

import os
import json
import subprocess
from typing import Dict, Any, Optional, List
from utils.helpers import is_valid_url, estimate_file_size, sanitize_filename

class MediaExtractor:
    """Extrae metadatos y opciones de calidad para enlaces compatibles."""

    def __init__(self, ytdlp_binary_path: Optional[str] = None):
        self.binary_path = ytdlp_binary_path or self._find_ytdlp()

    def _find_ytdlp(self) -> str:
        """Localiza el binario o script de yt-dlp disponible."""
        # 1. Verificar binario local en carpeta bin
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        local_bin = os.path.join(base_dir, "bin", "yt-dlp")
        if os.path.exists(local_bin) and os.access(local_bin, os.X_OK):
            return local_bin

        # 2. Verificar en PATH del sistema
        import shutil
        sys_path = shutil.which("yt-dlp")
        if sys_path:
            return sys_path

        # 3. Fallback a módulo python
        return "yt-dlp"

    def analyze_url(self, url: str) -> Dict[str, Any]:
        """
        Analiza la URL y extrae información detallada:
        título, duración, miniatura, calidades de audio y vídeo disponibles.
        """
        if not is_valid_url(url):
            return {
                "success": False,
                "error": "La URL proporcionada no es válida o no utiliza el protocolo http/https."
            }

        try:
            # Localizar archivo de cookies si existe
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cookies_path = os.path.join(base_dir, "data", "cookies.txt")
            cookie_args = ["--cookies", cookies_path] if os.path.exists(cookies_path) and os.path.getsize(cookies_path) > 10 else []

            # Comando yt-dlp para obtener JSON completo sin descargar
            cmd = [
                self.binary_path,
                "--dump-single-json",
                "--no-warnings",
                "--no-playlist",
                "--skip-download",
                "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "--extractor-args", "youtube:player_client=android,web;player_skip=configs",
                *cookie_args,
                url
            ]

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )

            if process.returncode != 0:
                err_msg = process.stderr.strip() or "Error al analizar el enlace."
                err_lower = err_msg.lower()
                if "sign in to confirm you’re not a bot" in err_lower or "sign in to confirm you're not a bot" in err_lower or "bot" in err_lower:
                    return {
                        "success": False,
                        "error": "YouTube detectó IP de servidor y requiere verificación antibot. Configura tus cookies en 'Ajustes > Cookies' o compila el APK (en dispositivos Android no se solicita verificación).",
                        "is_bot_check": True
                    }
                if "drm" in err_lower or "protected" in err_lower:
                    return {
                        "success": False,
                        "error": "El contenido posee protección DRM o restricciones de derechos de autor que no permiten su descarga.",
                        "is_drm": True
                    }
                return {
                    "success": False,
                    "error": f"No se pudo extraer información del enlace: {err_msg[:200]}"
                }

            data = json.loads(process.stdout)

            # Verificar si tiene DRM
            if data.get("_has_drm") or data.get("is_live"):
                return {
                    "success": False,
                    "error": "Transmisiones en vivo o contenido cifrado con DRM no están permitidos.",
                    "is_drm": True
                }

            title = data.get("title", "Sin título")
            duration = int(data.get("duration") or 0)
            thumbnail = data.get("thumbnail") or ""
            uploader = data.get("uploader") or data.get("channel") or "Desconocido"
            
            # Formatos disponibles
            formats_raw = data.get("formats", [])
            has_video = any(f.get("vcodec") and f.get("vcodec") != "none" for f in formats_raw)
            has_audio = any(f.get("acodec") and f.get("acodec") != "none" for f in formats_raw)

            # Calidades de Audio disponibles (bitrates estándar con tamaños estimados)
            audio_qualities = []
            for bitrate in ["320k", "256k", "192k", "128k"]:
                est_size = estimate_file_size(duration, "mp3", bitrate)
                label = f"{bitrate} (Estudio)" if bitrate == "320k" else f"{bitrate} (Estándar)" if bitrate == "192k" else f"{bitrate}"
                audio_qualities.append({
                    "quality": bitrate,
                    "label": label,
                    "estimated_size": est_size,
                    "format": "mp3"
                })

            # Calidades de Video disponibles (resoluciones)
            video_qualities = []
            standard_resolutions = [
                ("1080p", "1080p Full HD", 1080),
                ("720p", "720p HD", 720),
                ("480p", "480p SD", 480),
                ("360p", "360p Móvil", 360)
            ]

            # Detectar qué alturas están presentes
            available_heights = {f.get("height") for f in formats_raw if f.get("height")}
            
            for q_id, q_label, height_val in standard_resolutions:
                # Si no se detectan alturas explícitas o la altura está disponible
                if not available_heights or any(h and h >= height_val for h in available_heights):
                    video_qualities.append({
                        "quality": q_id,
                        "label": q_label,
                        "estimated_size": estimate_file_size(duration, "mp4", q_id),
                        "format": "mp4"
                    })

            if not video_qualities:
                video_qualities.append({
                    "quality": "Best",
                    "label": "Mejor calidad disponible",
                    "estimated_size": estimate_file_size(duration, "mp4", "Best"),
                    "format": "mp4"
                })

            return {
                "success": True,
                "id": str(data.get("id", "media")),
                "title": title,
                "sanitized_title": sanitize_filename(title),
                "url": url,
                "duration": duration,
                "thumbnail": thumbnail,
                "uploader": uploader,
                "has_video": has_video,
                "has_audio": has_audio,
                "audio_qualities": audio_qualities,
                "video_qualities": video_qualities,
                "extractor": data.get("extractor", "genérico")
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Tiempo de espera agotado al consultar los servidores del enlace."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error inesperado durante el análisis: {str(e)}"
            }
