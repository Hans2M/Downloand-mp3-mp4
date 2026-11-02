"""
Media Downloader - Downloads Screen (KivyMD)
Pantalla del administrador de descargas con visualización en tiempo real
de progreso, velocidad, tamaño descargado, ETA y cancelación.
"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.button import MDIconButton
from kivy.clock import Clock

class DownloadsScreen(MDScreen):
    """Pantalla para supervisar tareas activas y recientes."""

    def __init__(self, download_manager, **kwargs):
        super().__init__(**kwargs)
        self.download_manager = download_manager
        self.item_cards = {}

        self._build_ui()
        # Registrarse como oyente del DownloadManager
        self.download_manager.add_listener(self.on_download_update)

    def _build_ui(self):
        main_layout = MDBoxLayout(orientation="vertical", padding="16dp", spacing="12dp")

        header = MDLabel(
            text="Descargas Activas",
            font_style="H5",
            bold=True,
            size_hint_y=None,
            height="40dp"
        )
        main_layout.add_widget(header)

        scroll = MDScrollView()
        self.list_container = MDList(spacing="10dp")
        scroll.add_widget(self.list_container)
        main_layout.add_widget(scroll)

        self.add_widget(main_layout)

    def on_download_update(self, task_data: dict):
        """Recibe actualizaciones del motor y programa refresco en hilo UI."""
        Clock.schedule_once(lambda dt: self._update_task_ui(task_data), 0)

    def _update_task_ui(self, task: dict):
        task_id = task["id"]
        if task_id not in self.item_cards:
            # Crear nueva tarjeta de descarga
            card = MDCard(
                orientation="vertical",
                padding="12dp",
                spacing="8dp",
                size_hint_y=None,
                height="110dp",
                radius=[12, 12, 12, 12],
                elevation=2
            )

            title_row = MDBoxLayout(orientation="horizontal")
            title_lbl = MDLabel(
                text=task["title"],
                font_style="Subtitle2",
                bold=True,
                max_lines=1,
                size_hint_x=0.85
            )
            cancel_btn = MDIconButton(
                icon="close-circle",
                theme_text_color="Error",
                on_release=lambda x: self.download_manager.cancel_task(task_id)
            )
            title_row.add_widget(title_lbl)
            title_row.add_widget(cancel_btn)
            card.add_widget(title_row)

            # Barra de progreso
            pbar = MDProgressBar(value=task["progress"], max=100)
            card.add_widget(pbar)

            # Fila de métricas: progreso, velocidad, ETA
            metric_row = MDBoxLayout(orientation="horizontal")
            metric_text = task.get("error_message") or (
                f"{task['progress']}% | {task['speed']} | ETA: {task['eta']}"
            )
            metric_lbl = MDLabel(
                text=metric_text,
                font_style="Caption",
                theme_text_color="Secondary"
            )
            status_lbl = MDLabel(
                text=task["status"].upper(),
                font_style="Caption",
                halign="right",
                theme_text_color="Custom",
                text_color=(0.2, 0.8, 0.4, 1) if task["status"] == "completed" else (0.8, 0.4, 0.2, 1)
            )
            metric_row.add_widget(metric_lbl)
            metric_row.add_widget(status_lbl)
            card.add_widget(metric_row)

            self.item_cards[task_id] = {
                "card": card,
                "pbar": pbar,
                "metric_lbl": metric_lbl,
                "status_lbl": status_lbl
            }
            self.list_container.add_widget(card)

        # Actualizar valores
        ui = self.item_cards[task_id]
        ui["pbar"].value = task["progress"]
        ui["metric_lbl"].text = task.get("error_message") or (
            f"{task['progress']}% | {task['speed']} | ETA: {task['eta']}"
        )
        ui["status_lbl"].text = task["status"].upper()
