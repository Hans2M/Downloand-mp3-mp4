"""
Media Downloader - Settings Screen (KivyMD)
Pantalla de ajustes: directorio de descargas, formato predeterminado,
calidad por defecto, límites concurrentes y borrado de caché.
"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDRectangleFlatButton
from kivymd.toast import toast

class SettingsScreen(MDScreen):
    """Pantalla para gestionar la configuración de la aplicación."""

    def __init__(self, db_manager, storage_manager, **kwargs):
        super().__init__(**kwargs)
        self.db = db_manager
        self.storage = storage_manager
        self._build_ui()

    def _build_ui(self):
        main_layout = MDBoxLayout(orientation="vertical", padding="16dp", spacing="12dp")

        header = MDLabel(
            text="Configuración",
            font_style="H5",
            bold=True,
            size_hint_y=None,
            height="40dp"
        )
        main_layout.add_widget(header)

        scroll = MDScrollView()
        list_settings = MDList()

        # Ruta de almacenamiento
        current_dir = self.storage.download_dir
        self.item_dir = TwoLineListItem(
            text="Carpeta de Almacenamiento",
            secondary_text=current_dir
        )
        list_settings.add_widget(self.item_dir)

        # Formato predeterminado
        curr_fmt = self.db.get_setting("default_format", "mp4").upper()
        self.item_fmt = TwoLineListItem(
            text="Formato Predeterminado",
            secondary_text=curr_fmt,
            on_release=self.toggle_format
        )
        list_settings.add_widget(self.item_fmt)

        # Descargas simultáneas
        concurrent = self.db.get_setting("max_concurrent", "2")
        self.item_concurrent = TwoLineListItem(
            text="Descargas Simultáneas Máximas",
            secondary_text=f"{concurrent} tareas en paralelo"
        )
        list_settings.add_widget(self.item_concurrent)

        # Diagnósticos del sistema
        item_diag = TwoLineListItem(
            text="Motor Multimedia",
            secondary_text="yt-dlp + FFmpeg con aceleración nativa"
        )
        list_settings.add_widget(item_diag)

        # Limpiar historial
        btn_clear = MDRaisedButton(
            text="VACIAR TODO EL HISTORIAL",
            icon="trash-can-outline",
            md_bg_color=(0.8, 0.2, 0.2, 1),
            size_hint_x=1,
            on_release=self.clear_all_history
        )

        scroll.add_widget(list_settings)
        main_layout.add_widget(scroll)
        main_layout.add_widget(btn_clear)

        self.add_widget(main_layout)

    def toggle_format(self, *args):
        curr = self.db.get_setting("default_format", "mp4")
        new_fmt = "mp3" if curr == "mp4" else "mp4"
        self.db.set_setting("default_format", new_fmt)
        self.item_fmt.secondary_text = new_fmt.upper()
        toast(f"Formato predeterminado cambiado a {new_fmt.upper()}")

    def clear_all_history(self, *args):
        self.db.clear_history()
        toast("Historial vaciado correctamente.")
