"""
Media Downloader - Library & History Screen (KivyMD)
Biblioteca multimedia para reproducir audio y vídeo, compartir archivos,
eliminar elementos y ver el historial registrado en SQLite.
"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, TwoLineAvatarIconListItem, IconLeftWidget, IconRightWidget
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
import os

from utils.helpers import format_bytes

class LibraryScreen(MDScreen):
    """Visualización de archivos descargados y registro de SQLite."""

    def __init__(self, db_manager, storage_manager, **kwargs):
        super().__init__(**kwargs)
        self.db = db_manager
        self.storage = storage_manager
        self._build_ui()

    def _build_ui(self):
        main_layout = MDBoxLayout(orientation="vertical", padding="16dp", spacing="12dp")

        # Cabecera con botón de refresco
        header_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height="40dp")
        header = MDLabel(
            text="Biblioteca y Archivos",
            font_style="H5",
            bold=True
        )
        refresh_btn = MDIconButton(
            icon="refresh",
            on_release=lambda x: self.load_library()
        )
        header_row.add_widget(header)
        header_row.add_widget(refresh_btn)
        main_layout.add_widget(header_row)

        scroll = MDScrollView()
        self.list_container = MDList()
        scroll.add_widget(self.list_container)
        main_layout.add_widget(scroll)

        self.add_widget(main_layout)

    def on_enter(self, *args):
        """Se ejecuta al entrar a la pantalla."""
        self.load_library()

    def load_library(self):
        """Carga los registros desde la base de datos SQLite."""
        self.list_container.clear_widgets()
        items = self.db.get_all_downloads()

        if not items:
            empty_lbl = MDLabel(
                text="No hay descargas registradas en la biblioteca aún.",
                halign="center",
                theme_text_color="Hint"
            )
            self.list_container.add_widget(empty_lbl)
            return

        for item in items:
            icon_name = "music-circle" if item.get("format") == "mp3" else "video"
            size_str = format_bytes(item.get("file_size", 0))
            
            list_item = TwoLineAvatarIconListItem(
                text=item.get("title", "Archivo sin nombre"),
                secondary_text=f"{item.get('format', '').upper()} | {size_str} | {item.get('quality', '')}",
                on_release=lambda x, it=item: self.open_media_options(it)
            )

            # Icono izquierdo según formato
            left_icon = IconLeftWidget(icon=icon_name)
            list_item.add_widget(left_icon)

            # Botón de eliminar
            del_btn = IconRightWidget(
                icon="delete-outline",
                on_release=lambda x, d_id=item["id"], f_path=item.get("file_path"): self.confirm_delete(d_id, f_path)
            )
            list_item.add_widget(del_btn)

            self.list_container.add_widget(list_item)

    def open_media_options(self, item: dict):
        """Muestra opciones para reproducir o compartir el archivo."""
        file_path = item.get("file_path", "")
        dialog = MDDialog(
            title=item.get("title", "Detalle Multimedia"),
            text=f"Ruta: {file_path}\nFormato: {item.get('format')}\nTamaño: {format_bytes(item.get('file_size'))}",
            buttons=[
                MDRaisedButton(
                    text="REPRODUCIR",
                    on_release=lambda x: self.play_media(file_path, dialog)
                ),
                MDRaisedButton(
                    text="CERRAR",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def play_media(self, file_path: str, dialog):
        dialog.dismiss()
        if not file_path or not os.path.exists(file_path):
            from kivymd.toast import toast
            toast("El archivo no existe en el almacenamiento.")
            return

        # En Android abrir con intent nativo
        from utils.android_notifications import IS_ANDROID
        if IS_ANDROID:
            try:
                from jnius import autoclass
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                Intent = autoclass("android.content.Intent")
                Uri = autoclass("android.net.Uri")
                File = autoclass("java.io.File")
                
                context = PythonActivity.mActivity
                intent = Intent(Intent.ACTION_VIEW)
                uri = Uri.fromFile(File(file_path))
                mime = "audio/*" if file_path.endswith(".mp3") else "video/*"
                intent.setDataAndType(uri, mime)
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                context.startActivity(intent)
            except Exception as e:
                print(f"[Playback] Error abriendo reproductor Android: {e}")

    def confirm_delete(self, download_id: str, file_path: str):
        """Elimina el registro y el archivo físico si aún existe."""
        self.db.delete_download(download_id)
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        self.load_library()
