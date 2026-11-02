"""
Media Downloader - Home Screen (KivyMD)
Pantalla principal para inserción de URLs, análisis de metadatos,
selección de formato MP3/MP4, calidades y botón de descarga.
"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDRectangleFlatIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.spinner import MDSpinner
from kivy.clock import Clock
from kivy.uix.image import AsyncImage
import threading

from utils.helpers import is_valid_url, format_time, format_bytes

class HomeScreen(MDScreen):
    """Pantalla inicial del analizador y descargador."""

    def __init__(self, download_manager, **kwargs):
        super().__init__(**kwargs)
        self.download_manager = download_manager
        self.current_analysis = None
        self.selected_format = "mp4"
        self.selected_quality = "720p"
        self.quality_buttons = {}

        self._build_ui()

    def _build_ui(self):
        """Construye los widgets de la pantalla con diseño KivyMD oscuro."""
        main_layout = MDBoxLayout(
            orientation="vertical",
            padding="16dp",
            spacing="16dp"
        )

        # Encabezado
        header_box = MDBoxLayout(orientation="horizontal", size_hint_y=None, height="48dp")
        logo_label = MDLabel(
            text="Media Downloader",
            font_style="H5",
            theme_text_color="Primary",
            bold=True
        )
        header_box.add_widget(logo_label)
        main_layout.add_widget(header_box)

        # Tarjeta de entrada de enlace
        input_card = MDCard(
            orientation="vertical",
            padding="12dp",
            spacing="8dp",
            size_hint_y=None,
            height="140dp",
            radius=[16, 16, 16, 16],
            elevation=2
        )

        input_row = MDBoxLayout(orientation="horizontal", spacing="8dp")
        self.url_input = MDTextField(
            hint_text="Pega el enlace URL aquí (YouTube, Vimeo, etc.)",
            mode="rectangle",
            size_hint_x=0.85
        )
        paste_btn = MDIconButton(
            icon="content-paste",
            on_release=self.paste_from_clipboard
        )
        input_row.add_widget(self.url_input)
        input_row.add_widget(paste_btn)
        input_card.add_widget(input_row)

        # Botón Analizar
        self.analyze_btn = MDRaisedButton(
            text="ANALIZAR ENLACE",
            icon="magnify",
            size_hint_x=1,
            on_release=self.on_analyze_clicked
        )
        input_card.add_widget(self.analyze_btn)
        main_layout.add_widget(input_card)

        # Spinner de carga
        self.spinner = MDSpinner(
            size_hint=(None, None),
            size=("36dp", "36dp"),
            pos_hint={'center_x': .5},
            active=False
        )
        main_layout.add_widget(self.spinner)

        # Tarjeta de vista previa multimedia
        self.preview_card = MDCard(
            orientation="vertical",
            padding="14dp",
            spacing="10dp",
            size_hint_y=None,
            height="390dp",
            radius=[16, 16, 16, 16],
            opacity=0, # Oculta hasta analizar
            elevation=3
        )

        # Miniatura y datos
        media_row = MDBoxLayout(orientation="horizontal", spacing="12dp", size_hint_y=None, height="90dp")
        self.thumbnail_img = AsyncImage(
            source="",
            size_hint=(None, None),
            size=("120dp", "90dp"),
            allow_stretch=True,
            keep_ratio=True
        )
        
        info_col = MDBoxLayout(orientation="vertical", spacing="4dp")
        self.title_label = MDLabel(
            text="Título del contenido",
            font_style="Subtitle1",
            bold=True,
            theme_text_color="Primary",
            max_lines=2
        )
        self.duration_label = MDLabel(
            text="Duración: --:--",
            font_style="Caption",
            theme_text_color="Secondary"
        )
        self.size_label = MDLabel(
            text="Tamaño estimado: Calculando...",
            font_style="Caption",
            theme_text_color="Secondary"
        )
        info_col.add_widget(self.title_label)
        info_col.add_widget(self.duration_label)
        info_col.add_widget(self.size_label)

        media_row.add_widget(self.thumbnail_img)
        media_row.add_widget(info_col)
        self.preview_card.add_widget(media_row)

        # Selector de Formato (MP3 / MP4)
        format_box = MDBoxLayout(
            orientation="horizontal",
            spacing="10dp",
            size_hint_y=None,
            height="44dp"
        )
        self.mp4_chip = MDRaisedButton(
            text="VIDEO MP4",
            size_hint_x=0.5,
            on_release=lambda x: self.select_format("mp4")
        )
        self.mp3_chip = MDRaisedButton(
            text="AUDIO MP3",
            size_hint_x=0.5,
            on_release=lambda x: self.select_format("mp3")
        )
        format_box.add_widget(self.mp4_chip)
        format_box.add_widget(self.mp3_chip)
        self.preview_card.add_widget(format_box)

        self.quality_label = MDLabel(
            text="Calidad de vídeo",
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="24dp"
        )
        self.preview_card.add_widget(self.quality_label)

        self.quality_scroll = MDScrollView(
            do_scroll_x=True,
            do_scroll_y=False,
            size_hint_y=None,
            height="44dp"
        )
        self.quality_box = MDBoxLayout(
            orientation="horizontal",
            spacing="8dp",
            size_hint_x=None,
            width="0dp"
        )
        self.quality_box.bind(minimum_width=self.quality_box.setter("width"))
        self.quality_scroll.add_widget(self.quality_box)
        self.preview_card.add_widget(self.quality_scroll)

        # Botón de Descarga
        self.download_btn = MDRaisedButton(
            text="DESCARGAR AHORA",
            icon="download",
            size_hint_x=1,
            md_bg_color=(0.1, 0.65, 0.4, 1),
            on_release=self.on_download_clicked
        )
        self.preview_card.add_widget(self.download_btn)

        main_layout.add_widget(self.preview_card)
        self.add_widget(main_layout)

    def paste_from_clipboard(self, *args):
        """Pega el contenido del portapapeles en el campo de texto."""
        from kivy.core.clipboard import Clipboard
        text = Clipboard.paste()
        if text:
            self.url_input.text = text.strip()

    def on_analyze_clicked(self, *args):
        """Inicia el análisis de la URL en un hilo secundario."""
        url = self.url_input.text.strip()
        if not is_valid_url(url):
            self.show_toast("Por favor ingresa una URL válida (http/https)")
            return

        self.spinner.active = True
        self.analyze_btn.disabled = True

        threading.Thread(target=self._analyze_thread, args=(url,), daemon=True).start()

    def _analyze_thread(self, url: str):
        result = self.download_manager.extractor.analyze_url(url)
        Clock.schedule_once(lambda dt: self._update_preview(result), 0)

    def _update_preview(self, result):
        self.spinner.active = False
        self.analyze_btn.disabled = False

        if not result.get("success"):
            self.show_toast(result.get("error", "Error al analizar"))
            return

        self.current_analysis = result
        self.title_label.text = result.get("title", "Sin título")
        self.duration_label.text = f"Duración: {format_time(result.get('duration', 0))}"
        self.thumbnail_img.source = result.get("thumbnail", "")
        self.preview_card.opacity = 1

        video_options = result.get("video_qualities", [])
        audio_options = result.get("audio_qualities", [])
        self.mp4_chip.disabled = not bool(video_options)
        self.mp3_chip.disabled = not bool(audio_options)
        if video_options:
            self.selected_format = "mp4"
        elif audio_options:
            self.selected_format = "mp3"

        self.select_format(self.selected_format)

    def select_format(self, fmt: str):
        if self.current_analysis:
            options_key = "audio_qualities" if fmt == "mp3" else "video_qualities"
            if not self.current_analysis.get(options_key):
                self.show_toast(f"Este enlace no ofrece {fmt.upper()}")
                return

        self.selected_format = fmt
        self.mp4_chip.md_bg_color = (
            (0.1, 0.65, 0.4, 1) if fmt == "mp4" else (0.2, 0.2, 0.25, 1)
        )
        self.mp3_chip.md_bg_color = (
            (0.1, 0.65, 0.4, 1) if fmt == "mp3" else (0.2, 0.2, 0.25, 1)
        )

        options_key = "audio_qualities" if fmt == "mp3" else "video_qualities"
        options = self.current_analysis.get(options_key, []) if self.current_analysis else []
        preferred = "320k" if fmt == "mp3" else "720p"
        available = [option["quality"] for option in options]
        self.selected_quality = preferred if preferred in available else (available[0] if available else preferred)
        self._populate_quality_options(options)
        self.update_estimated_size()

    def _populate_quality_options(self, options):
        """Muestra botones con las calidades que devuelve el extractor."""
        self.quality_box.clear_widgets()
        self.quality_buttons.clear()
        self.quality_label.text = "Calidad de audio" if self.selected_format == "mp3" else "Calidad de vídeo"

        for option in options:
            button = MDRaisedButton(
                text=option.get("label", option.get("quality", "")),
                size_hint_x=None,
                width="132dp" if self.selected_format == "mp4" else "150dp",
                font_size="11sp",
                on_release=lambda _, quality=option["quality"]: self.select_quality(quality)
            )
            self.quality_buttons[option["quality"]] = button
            self.quality_box.add_widget(button)

        self._refresh_quality_buttons()

    def select_quality(self, quality: str):
        """Selecciona una calidad y actualiza el tamaño estimado."""
        self.selected_quality = quality
        self._refresh_quality_buttons()
        self.update_estimated_size()

    def _refresh_quality_buttons(self):
        for quality, button in self.quality_buttons.items():
            button.md_bg_color = (
                (0.1, 0.65, 0.4, 1)
                if quality == self.selected_quality
                else (0.2, 0.2, 0.25, 1)
            )

    def update_estimated_size(self):
        if not self.current_analysis:
            return
        duration = self.current_analysis.get("duration", 0)
        from utils.helpers import estimate_file_size
        bytes_est = estimate_file_size(duration, self.selected_format, self.selected_quality)
        self.size_label.text = f"Tamaño est.: {format_bytes(bytes_est)} ({self.selected_quality})"

    def on_download_clicked(self, *args):
        if not self.current_analysis:
            return

        task_id = self.download_manager.create_task(
            url=self.current_analysis["url"],
            title=self.current_analysis["title"],
            format_type=self.selected_format,
            quality=self.selected_quality,
            thumbnail_url=self.current_analysis.get("thumbnail", ""),
            duration=self.current_analysis.get("duration", 0)
        )
        self.show_toast("Descarga agregada a la cola")

    def show_toast(self, message: str):
        from kivymd.toast import toast
        toast(message)
