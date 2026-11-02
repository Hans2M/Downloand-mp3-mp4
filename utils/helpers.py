"""
Media Downloader - Helpers & Utilities
Funciones auxiliares para validación de URLs, formateo de tamaños y tiempos,
y saneamiento de nombres de archivo.
"""

import re
import urllib.parse
from typing import Optional, Tuple

# Expresión regular para validación básica de URL http/https
URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://'  # http:// o https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # dominio
    r'localhost|' # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...o ip
    r'(?::\d+)?' # puerto opcional
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

# Lista de dominios restringidos o no autorizados por seguridad
DISALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "169.254.169.254" # metadata endpoints
]

def is_valid_url(url: str) -> bool:
    """Verifica si la URL tiene una estructura válida y segura."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    
    try:
        parsed = urllib.parse.urlparse(url)
        hostname = (parsed.hostname or "").lower()
        if not hostname:
            return False
        # Evitar SSRF a redes internas
        if hostname in DISALLOWED_HOSTS or hostname.startswith("192.168.") or hostname.startswith("10."):
            return False
        return True
    except Exception:
        return False

def format_bytes(size: Optional[int]) -> str:
    """Convierte bytes a formato legible (KB, MB, GB)."""
    if size is None or size <= 0:
        return "Desconocido"
    power = 1024
    n = 0
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    val = float(size)
    while val >= power and n < len(units) - 1:
        val /= power
        n += 1
    return f"{val:.1f} {units[n]}"

def format_time(seconds: Optional[int]) -> str:
    """Formatea segundos en formato MM:SS o HH:MM:SS."""
    if seconds is None or seconds < 0:
        return "--:--"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def sanitize_filename(name: str, max_length: int = 120) -> str:
    """Sanea una cadena para usarla como nombre de archivo seguro."""
    if not name:
        return "media_download"
    # Eliminar caracteres no permitidos en sistemas de archivos
    sanitized = re.sub(r'[\\/*?:"<>|]', "", name)
    sanitized = sanitized.replace("\n", " ").replace("\r", " ").strip()
    # Acortar longitud si excede
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].strip()
    return sanitized or "media_download"

def estimate_file_size(duration_sec: int, format_type: str, quality: str) -> int:
    """Estima el tamaño en bytes de acuerdo a la duración y la calidad elegida."""
    if duration_sec <= 0:
        return 0
    
    if format_type.lower() == "mp3":
        # Bitrate en kbps
        bitrate_map = {
            "320k": 320,
            "256k": 256,
            "192k": 192,
            "128k": 128
        }
        kbps = bitrate_map.get(quality, 192)
        # bytes = (kbps * 1000 / 8) * seconds
        return int((kbps * 1024 / 8) * duration_sec)
    else: # mp4
        # Bitrate aproximado combinado video+audio en kbps
        resolution_map = {
            "1080p": 3500,
            "720p": 1800,
            "480p": 900,
            "360p": 500,
            "Best": 2200
        }
        kbps = resolution_map.get(quality, 1500)
        return int((kbps * 1024 / 8) * duration_sec)
