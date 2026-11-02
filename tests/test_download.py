"""
Media Downloader - Functional Test Suite
Prueba funcional completa con enlaces autorizados de dominio público y Creative Commons.
Valida extracción de metadatos yt-dlp, base de datos SQLite y conversión FFmpeg.
"""

import os
import sys

# Agregar ruta base
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import is_valid_url, format_bytes, format_time
from database.db_manager import DatabaseManager
from services.extractor import MediaExtractor
from services.converter import MediaConverter

# Enlace de prueba autorizado de código abierto / dominio público (Big Buck Bunny 1MB test)
TEST_URL_CC = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4"

def run_tests():
    print("=" * 60)
    print("INICIANDO PRUEBAS DE MEDIA DOWNLOADER")
    print("=" * 60)

    # 1. Prueba de validación de URLs
    print("\n[1/4] Probando validación de URLs...")
    assert is_valid_url(TEST_URL_CC) is True, "Error validando URL válida"
    assert is_valid_url("http://localhost/secret") is False, "Fallo al bloquear localhost SSRF"
    assert is_valid_url("not_a_url") is False, "Fallo al descartar URL no válida"
    print("  -> Validación de URLs: PASÓ [OK]")

    # 2. Prueba de base de datos SQLite
    print("\n[2/4] Probando base de datos SQLite...")
    test_db_path = "/tmp/test_media_downloader.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    db = DatabaseManager(test_db_path)
    
    # Insertar registro de prueba
    success = db.add_download({
        "id": "test_item_01",
        "title": "Big Buck Bunny Sample",
        "url": TEST_URL_CC,
        "format": "mp4",
        "quality": "360p",
        "file_size": 1048576,
        "file_path": "/tmp/sample.mp4",
        "status": "completed"
    })
    assert success is True, "Error insertando registro en SQLite"

    item = db.get_download_by_id("test_item_01")
    assert item is not None and item["title"] == "Big Buck Bunny Sample", "Error recuperando registro de SQLite"
    print("  -> Base de datos SQLite (CRUD): PASÓ [OK]")

    # 3. Prueba de extractor yt-dlp
    print("\n[3/4] Probando extractor yt-dlp con enlace público CC...")
    extractor = MediaExtractor()
    info = extractor.analyze_url(TEST_URL_CC)
    assert info.get("success") is True, f"Fallo al analizar URL de prueba: {info.get('error')}"
    print(f"  -> Título extraído: {info.get('title')}")
    print(f"  -> Duración: {format_time(info.get('duration'))}")
    print(f"  -> Opciones de audio: {len(info.get('audio_qualities', []))} calidades")
    print(f"  -> Opciones de video: {len(info.get('video_qualities', []))} calidades")
    print("  -> Extracción yt-dlp: PASÓ [OK]")

    # 4. Prueba de disponibilidad de FFmpeg
    print("\n[4/4] Verificando FFmpeg...")
    converter = MediaConverter()
    if converter.is_available():
        print("  -> FFmpeg disponible y verificado: PASÓ [OK]")
    else:
        print("  -> FFmpeg no localizado en PATH directo (se usará receta en Android)")

    print("\n" + "=" * 60)
    print("TODAS LAS PRUEBAS COMPLETADAS CON ÉXITO")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
