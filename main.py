"""
Media Downloader - Main Application Entry Point
Aplicación móvil Android desarrollada con KivyMD, Python 3, yt-dlp, FFmpeg y SQLite.
Proporciona navegación inferior con Inicio, Descargas, Biblioteca y Configuración.
"""

import os
import sys

# Asegurar que el directorio raíz de la app esté en sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.boxlayout import MDBoxLayout

from database.db_manager import DatabaseManager
from storage.storage_manager import StorageManager
from core.download_manager import DownloadManager
from ui.screens.home_screen import HomeScreen
from ui.screens.downloads_screen import DownloadsScreen
from ui.screens.library_screen import LibraryScreen
from ui.screens.settings_screen import SettingsScreen

class MediaDownloaderApp(MDApp):
    """Clase principal de la aplicación KivyMD."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Media Downloader"
        self.icon = "assets/icon.png"

        # Inicialización de subsistemas
        self.db_manager = DatabaseManager()
        self.storage_manager = StorageManager()
        self.download_manager = DownloadManager(self.db_manager, self.storage_manager)

    def build(self):
        """Configuración del tema visual oscuro y la estructura de navegación."""
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Indigo"
        self.theme_cls.accent_palette = "Amber"

        root_screen = MDScreen()
        
        # Barra de navegación inferior con 4 pestañas requeridas
        bottom_nav = MDBottomNavigation()

        # 1. Inicio
        tab_home = MDBottomNavigationItem(
            name="screen_home",
            text="Inicio",
            icon="home-variant"
        )
        self.home_screen = HomeScreen(self.download_manager)
        tab_home.add_widget(self.home_screen)
        bottom_nav.add_widget(tab_home)

        # 2. Descargas
        tab_downloads = MDBottomNavigationItem(
            name="screen_downloads",
            text="Descargas",
            icon="download-box"
        )
        self.downloads_screen = DownloadsScreen(self.download_manager)
        tab_downloads.add_widget(self.downloads_screen)
        bottom_nav.add_widget(tab_downloads)

        # 3. Biblioteca
        tab_library = MDBottomNavigationItem(
            name="screen_library",
            text="Biblioteca",
            icon="folder-music"
        )
        self.library_screen = LibraryScreen(self.db_manager, self.storage_manager)
        tab_library.add_widget(self.library_screen)
        bottom_nav.add_widget(tab_library)

        # 4. Configuración
        tab_settings = MDBottomNavigationItem(
            name="screen_settings",
            text="Ajustes",
            icon="cog"
        )
        self.settings_screen = SettingsScreen(self.db_manager, self.storage_manager)
        tab_settings.add_widget(self.settings_screen)
        bottom_nav.add_widget(tab_settings)

        root_screen.add_widget(bottom_nav)
        return root_screen

    def on_start(self):
        """Solicita permisos de almacenamiento en tiempo de ejecución en Android."""
        self.request_android_permissions()

    def request_android_permissions(self):
        """Maneja permisos modernos de Android (API 33/34 READ_MEDIA_AUDIO, READ_MEDIA_VIDEO)."""
        from utils.android_notifications import IS_ANDROID
        if IS_ANDROID:
            try:
                from android.permissions import request_permissions, Permission # type: ignore
                request_permissions([
                    Permission.INTERNET,
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.POST_NOTIFICATIONS
                ])
                print("[App] Permisos de Android solicitados con éxito.")
            except Exception as e:
                print(f"[App] Excepción al pedir permisos: {e}")

if __name__ == "__main__":
    MediaDownloaderApp().run()
