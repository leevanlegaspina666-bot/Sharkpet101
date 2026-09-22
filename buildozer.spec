[app]

# (str) Title of your application
title = Chibi Shark Pet

# (str) Package name
package.name = chibisharkpet

# (str) Package domain
package.domain = org.chibishark

# (str) Source code where main.py lives
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,jpeg,kv,atlas

# (str) Application version
version = 1.0

# (list) Application requirements
requirements = python3,kivy,pyjnius

# (str) Orientation
orientation = portrait

# (bool) Fullscreen
fullscreen = 1

# Android Usage Access. The user must still enable Usage Access
# for the installed app in Android Settings if foreground-app
# detection is desired.
android.permissions = PACKAGE_USAGE_STATS

# Android build settings
android.api = 35
android.minapi = 24
android.ndk_api = 24
# Keep the app focused on being a normal in-app pet.
# This is NOT an overlay over other apps.
