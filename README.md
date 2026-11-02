# Media Downloader APK - Python, KivyMD & Android

Aplicación móvil Android de grado producción desarrollada en **Python 3** con **KivyMD**, diseñada para la descarga, conversión y gestión de archivos multimedia (MP3 / MP4) mediante enlaces URL autorizados.

---

## 📱 Características Principales

- **Interfaz Móvil Moderna**: Diseño oscuro con KivyMD con navegación inferior (4 pestañas: *Inicio*, *Descargas*, *Biblioteca*, *Ajustes*).
- **Extracción Inteligente (yt-dlp)**: Análisis de metadatos en tiempo real (título, autor, duración, miniatura, calidades y peso estimado).
- **Descargas MP3 de Alta Fidelidad**: Extracción y codificación a MP3 con tasas de bits seleccionables (320 kbps Estudio, 256 kbps, 192 kbps Estándar, 128 kbps Ligero).
- **Descargas de Vídeo MP4**: Selección de resolución (1080p FHD, 720p HD, 480p SD, 360p Móvil) con remuxing automático de vídeo y audio vía FFmpeg.
- **Administrador de Descargas en Tiempo Real**:
  - Hilos concurrentes y cola de tareas.
  - Progreso porcentual y barra animada.
  - Velocidad de transferencia en MB/s y tamaño descargado.
  - Tiempo estimado restante (ETA).
  - Cancelación de tareas y limpieza automática de temporales.
- **Notificaciones Nativas Android (PyJNIus)**:
  - Notificaciones en vivo con barra de progreso mientras se descarga en segundo plano.
  - Alerta sonora y visual al completar o fallar.
- **Biblioteca y Reproductor**:
  - Listado de archivos guardados con miniatura y tamaño.
  - Reproducción de audio y vídeo directamente en la app o lanzador nativo.
  - Compartir y eliminar archivos con sincronización a `MediaScannerConnection`.
- **Historial SQLite**:
  - Base de datos relacional SQLite (`media_downloader.db`).
  - Registro de URL original, fecha, tamaño y ruta del archivo.
  - Función de repetir descarga con un solo toque.
- **Almacenamiento Scoped y Android SAF**:
  - Compatible con Android 10, 11, 12, 13 y 14 (API 34).
  - Guarda en la carpeta pública `/Download/MediaDownloader` para fácil acceso del usuario.

---

## 📂 Arquitectura del Proyecto

```
python_app/
├── main.py                     # Punto de entrada de la aplicación KivyMD
├── buildozer.spec              # Configuración completa de empaquetado Android APK
├── requirements.txt            # Dependencias Python
├── README.md                   # Documentación técnica y guía de compilación
├── ui/
│   ├── screens/
│   │   ├── home_screen.py      # Pantalla principal (URL, análisis, preview y descarga)
│   │   ├── downloads_screen.py # Administrador de descargas activas y progreso en vivo
│   │   ├── library_screen.py   # Biblioteca de medios y reproductor integrado
│   │   └── settings_screen.py  # Configuración de carpetas, calidad y almacenamiento
├── core/
│   └── download_manager.py     # Motor multi-hilo de descargas y callbacks en tiempo real
├── services/
│   ├── extractor.py            # Analizador de enlaces con yt-dlp y cálculo de tamaños
│   └── converter.py            # Conversor y remuxer multimedia con FFmpeg
├── database/
│   └── db_manager.py           # Gestor SQLite (historial, biblioteca y ajustes)
├── storage/
│   └── storage_manager.py      # Gestor de almacenamiento Android SAF y MediaScanner
├── utils/
│   ├── helpers.py              # Validación de URLs, saneamiento de nombres y formateo
│   └── android_notifications.py# Notificaciones nativas Android vía PyJNIus
└── tests/
    └── test_download.py        # Suite de pruebas unitarias y funcionales
```

---

## 🚀 Guía de Compilación del APK con Buildozer

### Método 1: Compilación Rápida en Google Colab (Recomendado - 5 Minutos)
No necesitas instalar Linux, el SDK de Android ni el NDK en tu ordenador personal.

1. Abre un cuaderno en [Google Colab](https://colab.research.google.com).
2. Asegúrate de tener activa la GPU o CPU estándar.
3. Copia y ejecuta este script en la primera celda:

```bash
# 1. Instalar dependencias del sistema para Buildozer
!sudo apt-get update -y
!sudo apt-get install -y git zip unzip autoconf libtool pkg-config zlib1g-dev \
    libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev \
    python3-pip ffmpeg openjdk-17-jdk

# 2. Instalar Cython y Buildozer
!pip install --upgrade Cython==0.29.36 buildozer virtualenv

# 3. Clonar o subir tu carpeta python_app
# Sube tus archivos python_app/ al entorno de Colab
%cd /content/python_app

# 4. Compilar APK en modo debug
!buildozer -v android debug

# 5. Descargar el APK generado
from google.colab import files
import glob
apk_files = glob.glob("bin/*.apk")
if apk_files:
    print(f"Descargando {apk_files[0]}...")
    files.download(apk_files[0])
```

---

### Método 2: Compilación con Docker

Si prefieres compilar en tu máquina local sin alterar tu sistema operativo:

```bash
# Ejecutar contenedor oficial de buildozer
docker run --volume "$(pwd)":/home/user/hostcwd \
    kivy/buildozer \
    android debug
```
El archivo `.apk` resultante se guardará en la carpeta `bin/`.

---

### Método 3: Compilación Local en Ubuntu / Debian

```bash
# 1. Instalar dependencias requeridas
sudo apt update
sudo apt install -y python3-pip git zip unzip openjdk-17-jdk autoconf libtool \
    pkg-config zlib1g-dev libncurses5-dev cmake libffi-dev libssl-dev ffmpeg

# 2. Instalar buildozer y cython
pip3 install --user --upgrade buildozer Cython==0.29.36

# 3. Compilar el APK
cd python_app
buildozer -v android debug
```

---

## 🔒 Seguridad, DRM y Derechos de Autor

- **Validación de URLs**: Toda dirección ingresada se verifica contra esquemas permitidos (`http`/`https`) y se bloquean accesos a direcciones locales (prevención SSRF contra redes privadas).
- **Protección DRM**: El analizador detecta transmisiones cifradas o con DRM y detiene la descarga notificando al usuario.
- **Responsabilidad de Uso**: Diseñado exclusivamente para descargar contenido de dominio público, con licencias Creative Commons, o contenido propio sobre el cual se ostenten derechos o autorización expresa del titular.

---

## 🧪 Ejecución de Pruebas

Para verificar el funcionamiento de los extractores, SQLite y validaciones en tu entorno local:

```bash
python3 tests/test_download.py
```
Salida esperada:
```
[1/4] Probando validación de URLs...  -> PASÓ [OK]
[2/4] Probando base de datos SQLite... -> PASÓ [OK]
[3/4] Probando extractor yt-dlp...     -> PASÓ [OK]
[4/4] Verificando FFmpeg...            -> PASÓ [OK]
```
