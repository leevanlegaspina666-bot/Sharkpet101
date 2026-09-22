[app]

title = Chibi Shark Pet
package.name = chibisharkpet
package.domain = org.chibishark
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas
version = 2.0
requirements = python3,kivy,pyjnius,android
orientation = portrait
fullscreen = 0

# Overlay + usage detection + foreground service.
android.permissions = SYSTEM_ALERT_WINDOW,PACKAGE_USAGE_STATS,FOREGROUND_SERVICE,FOREGROUND_SERVICE_SPECIAL_USE,POST_NOTIFICATIONS

# Android build settings. API 24 avoids the Python 3.14 pwritev issue seen with API 23.
android.api = 35
android.minapi = 24
android.ndk_api = 24
p4a.branch = develop

# The overlay is a real Android foreground service so it can remain alive
# after the Kivy Activity is no longer visible.
services = Overlay:services/overlay.py:foreground:sticky:foregroundServiceType=specialUse

# Make the sprite folder available to the service's AssetManager.
android.add_assets = assets:assets
