import os
import random
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window

YOUTUBE = "com.google.android.youtube"
MESSENGER = "com.facebook.orca"
DISCORD = "com.discord"


def overlay_allowed():
    try:
        from jnius import autoclass
        Settings = autoclass("android.provider.Settings")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        return bool(Settings.canDrawOverlays(PythonActivity.mActivity))
    except Exception:
        return False


def open_overlay_settings():
    try:
        from jnius import autoclass
        Intent = autoclass("android.content.Intent")
        Settings = autoclass("android.provider.Settings")
        Uri = autoclass("android.net.Uri")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity
        intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION)
        intent.setData(Uri.parse("package:" + activity.getPackageName()))
        activity.startActivity(intent)
    except Exception:
        pass


def start_overlay_service():
    if not overlay_allowed():
        return False
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        context = PythonActivity.mActivity
        service_name = str(context.getPackageName()) + ".ServiceOverlay"
        service = autoclass(service_name)
        service.start(context, "")
        return True
    except Exception as e:
        print("Could not start overlay service:", e)
        return False


class PetApp(App):
    title = "Chibi Shark Pet"

    def build(self):
        Window.clearcolor = (0.015, 0.02, 0.04, 1)
        root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(16))

        title = Label(text="🦈 Chibi Shark Pet", font_size=dp(28), size_hint_y=None, height=dp(60))
        root.add_widget(title)

        self.status = Label(
            text="Starting floating pet...",
            halign="center",
            valign="middle",
        )
        root.add_widget(self.status)

        self.button = Button(
            text="Allow floating pet",
            size_hint_y=None,
            height=dp(56),
        )
        self.button.bind(on_release=lambda *_: self.enable_overlay())
        root.add_widget(self.button)

        Clock.schedule_once(lambda dt: self.enable_overlay(), 0.7)
        Clock.schedule_interval(lambda dt: self.refresh_status(), 1.0)
        return root

    def enable_overlay(self):
        if overlay_allowed():
            if start_overlay_service():
                self.status.text = "🦈 Pet is floating over other apps!\nYou can leave this app."
                self.button.text = "Floating pet is ON"
            else:
                self.status.text = "Overlay permission is allowed, but the pet service could not start."
        else:
            self.status.text = "Allow 'Display over other apps' for Chibi Shark Pet."
            self.button.text = "Open overlay permission"
            open_overlay_settings()

    def refresh_status(self):
        if overlay_allowed():
            self.status.text = "🦈 Floating pet is ready.\nYou can leave this app."
            self.button.text = "Floating pet is ON"
        else:
            self.status.text = "Overlay permission is required."
            self.button.text = "Allow floating pet"

    def on_resume(self):
        Clock.schedule_once(lambda dt: self.enable_overlay(), 0.3)


if __name__ == "__main__":
    PetApp().run()
