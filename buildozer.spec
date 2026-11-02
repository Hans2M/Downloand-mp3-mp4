[app]

# (str) Title of your application
title = Media Downloader

# (str) Package name
package.name = mediadownloader

# (str) Package domain (needed for android packaging)
package.domain = org.mediadownloader.app

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,sql,txt

# (list) List of directory to exclude
source.exclude_dirs = tests, bin, .git, __pycache__, .pytest_cache

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow,urllib3,requests,certifi,pyjnius,ffmpeg

# (str) Presplash of the application
presplash.filename = %(source.dir)s/assets/presplash.png

# (str) Icon of the application
icon.filename = %(source.dir)s/assets/icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) List of service to declare
# services = DownloadService:./services/download_service.py

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen
fullscreen = 0

# (string) Presplash background color (for Android >= 12)
android.presplash_color = #121826

# (list) Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,READ_MEDIA_AUDIO,READ_MEDIA_VIDEO,FOREGROUND_SERVICE,POST_NOTIFICATIONS,WAKE_LOCK

# (int) Target Android API, should be as high as possible.
android.api = 34

# (int) Minimum API your APK / AAB will support.
android.minapi = 24

# (int) Android SDK version to use
android.sdk = 34

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (list) Android application meta-data to set (key=value format)
# android.meta_data = 

# (list) Android library project to add (will be added in the project.properties)
# android.library_references =

# (list) Android shared libraries which should be added to the APK
# android.add_shared_libs =

# (list) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
# For Google Play, arm64-v8a and armeabi-v7a are required
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) The format used to package the app for release mode (aab or apk)
android.release_artifact = apk

# (bool) Copy library instead of making a libsymlink.
android.copy_libs = 1

# (list) Gradle dependencies
android.gradle_dependencies = androidx.core:core:1.12.0, androidx.appcompat:appcompat:1.6.1

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 0
