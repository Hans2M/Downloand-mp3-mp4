"""
Media Downloader - Android Notification Service
Gestor de notificaciones nativas de Android mediante PyJNIus.
Crea canales de notificación, muestra barra de progreso en vivo y alertas de éxito/fallo.
"""

import os
import sys

IS_ANDROID = "ANDROID_ARGUMENT" in os.environ or hasattr(sys, "getandroidapilevel")

CHANNEL_ID = "media_downloader_channel"
CHANNEL_NAME = "Media Downloader Descargas"
CHANNEL_DESC = "Notificaciones de progreso y descargas completadas"

class AndroidNotificationManager:
    """Gestiona notificaciones nativas en Android usando PyJNIus."""

    def __init__(self):
        self._init_channel()

    def _init_channel(self):
        """Crea el NotificationChannel requerido para Android 8.0 (API 26) o superior."""
        if not IS_ANDROID:
            return

        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            NotificationManager = autoclass("android.app.NotificationManager")
            NotificationChannel = autoclass("android.app.NotificationChannel")
            BuildVersion = autoclass("android.os.Build$VERSION")
            Context = autoclass("android.content.Context")

            if BuildVersion.SDK_INT >= 26:
                context = PythonActivity.mActivity
                manager = context.getSystemService(Context.NOTIFICATION_SERVICE)
                
                channel = NotificationChannel(
                    CHANNEL_ID,
                    CHANNEL_NAME,
                    NotificationManager.IMPORTANCE_LOW
                )
                channel.setDescription(CHANNEL_DESC)
                manager.createNotificationChannel(channel)
                print("[Notif] NotificationChannel inicializado con éxito.")
        except Exception as e:
            print(f"[Notif] Error inicializando canal de notificación: {e}")

    def show_progress(self, notif_id: int, title: str, progress_percent: int, speed: str = ""):
        """Actualiza la notificación con el progreso de descarga."""
        if not IS_ANDROID:
            return

        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            NotificationCompatBuilder = autoclass("androidx.core.app.NotificationCompat$Builder")
            NotificationManager = autoclass("android.app.NotificationManager")
            Context = autoclass("android.content.Context")

            context = PythonActivity.mActivity
            manager = context.getSystemService(Context.NOTIFICATION_SERVICE)

            builder = NotificationCompatBuilder(context, CHANNEL_ID)
            builder.setContentTitle(f"Descargando: {title}")
            builder.setContentText(f"{progress_percent}% - {speed}")
            builder.setSmallIcon(context.getApplicationInfo().icon)
            builder.setProgress(100, progress_percent, False)
            builder.setOngoing(True)
            builder.setOnlyAlertOnce(True)

            manager.notify(notif_id, builder.build())
        except Exception as e:
            print(f"[Notif] Error mostrando progreso: {e}")

    def show_completed(self, notif_id: int, title: str, file_path: str):
        """Muestra una notificación persistente de descarga completada."""
        if not IS_ANDROID:
            print(f"[Notif Desktop] Descarga completada: {title} -> {file_path}")
            return

        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            NotificationCompatBuilder = autoclass("androidx.core.app.NotificationCompat$Builder")
            NotificationManager = autoclass("android.app.NotificationManager")
            Context = autoclass("android.content.Context")

            context = PythonActivity.mActivity
            manager = context.getSystemService(Context.NOTIFICATION_SERVICE)

            builder = NotificationCompatBuilder(context, CHANNEL_ID)
            builder.setContentTitle("Descarga completada")
            builder.setContentText(title)
            builder.setSmallIcon(context.getApplicationInfo().icon)
            builder.setProgress(0, 0, False)
            builder.setOngoing(False)
            builder.setAutoCancel(True)

            manager.notify(notif_id, builder.build())
        except Exception as e:
            print(f"[Notif] Error mostrando completado: {e}")

    def cancel(self, notif_id: int):
        """Cancela y retira la notificación."""
        if not IS_ANDROID:
            return
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            NotificationManager = autoclass("android.app.NotificationManager")
            Context = autoclass("android.content.Context")

            context = PythonActivity.mActivity
            manager = context.getSystemService(Context.NOTIFICATION_SERVICE)
            manager.cancel(notif_id)
        except Exception as e:
            print(f"[Notif] Error cancelando notificación: {e}")
