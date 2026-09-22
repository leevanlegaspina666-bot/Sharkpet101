import os
import glob
import random

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.core.window import Window

# All sprites are bundled inside the APK.
ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")

PET_SIZE = dp(80)
WALK_SPEED = dp(60)
WALK_FRAME_TIME = 0.10

GRAVITY = dp(1000)
JUMP_SPEED = dp(500)

IDLE_MIN = 2.0
IDLE_MAX = 5.0
REACTION_TIME = 1.2
ACTION_TIME = 1.5

TURN_MIN = 2.5
TURN_MAX = 6.0

DRAG_THRESHOLD = dp(12)

YOUTUBE = "com.google.android.youtube"
MESSENGER = "com.facebook.orca"
DISCORD = "com.discord"


def sprite(name):
    path = os.path.join(ASSETS, name)
    return path if os.path.exists(path) else None


def frames(prefix, direction):
    result = []
    for number in range(1, 9):
        path = sprite(f"{prefix}_{direction}_{number}.png")
        if path:
            result.append(path)
    return result


WALK_RIGHT = frames("walk", "right")
WALK_LEFT = frames("walk", "left")

IDLE = [
    sprite("idle_front.png"),
    sprite("idle_left.png"),
    sprite("idle_right.png"),
    sprite("idle_back.png"),
]
IDLE = [x for x in IDLE if x]

REACTIONS = [
    sprite("expression_happy.png"),
    sprite("expression_sad.png"),
    sprite("expression_angry.png"),
    sprite("expression_blush.png"),
    sprite("expression_surprised.png"),
]
REACTIONS = [x for x in REACTIONS if x]

ACTIONS = [
    sprite("action_jump.png"),
    sprite("action_lay.png"),
    sprite("action_sit.png"),
    sprite("action_wave.png"),
    sprite("action_interact.png"),
]
ACTIONS = [x for x in ACTIONS if x]

SLEEPY = sprite("expression_sleepy.png")


def get_foreground_package():
    """Return the most recently resumed Android package, if Usage Access is enabled."""
    try:
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context = autoclass("android.content.Context")
        System = autoclass("java.lang.System")
        Event = autoclass("android.app.usage.UsageEvents$Event")

        activity = PythonActivity.mActivity
        manager = activity.getSystemService(Context.USAGE_STATS_SERVICE)

        now = System.currentTimeMillis()
        events = manager.queryEvents(now - 5000, now)
        event = Event()

        last_package = None
        while events.hasNextEvent():
            events.getNextEvent(event)
            if event.getEventType() == 1:  # ACTIVITY_RESUMED
                package_name = event.getPackageName()
                if package_name:
                    last_package = str(package_name)

        return last_package
    except Exception:
        return None


class Pet(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.size_hint = (None, None)
        self.size = (PET_SIZE, PET_SIZE)
        self.allow_stretch = True
        self.keep_ratio = True

        self.direction = 1
        self.state = "walking"

        self.frames = WALK_RIGHT
        self.frame_index = 0
        self.frame_timer = 0.0

        self.state_timer = 0.0
        self.next_idle = random.uniform(IDLE_MIN, IDLE_MAX)

        self.turn_timer = 0.0
        self.next_turn = random.uniform(TURN_MIN, TURN_MAX)

        self.velocity_y = 0.0

        # Touch/drag state. A tap does NOT stop the pet.
        self.touch_uid = None
        self.touch_start_x = 0
        self.touch_start_y = 0
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.dragging = False

        self.current_app = None

        self.set_walk_frame()

    def set_source(self, path):
        if path and os.path.exists(path):
            self.source = path
            self.texture_update()

    def set_walk_frame(self):
        self.frames = WALK_RIGHT if self.direction == 1 else WALK_LEFT
        if not self.frames:
            return
        self.frame_index %= len(self.frames)
        self.set_source(self.frames[self.frame_index])

    def start_walking(self):
        self.state = "walking"
        self.state_timer = 0
        self.frame_index = 0
        self.set_walk_frame()

    def turn(self):
        self.direction *= -1
        self.frame_index = 0
        self.set_walk_frame()

    def show_for(self, path, duration):
        if not path:
            return
        self.state = "special"
        self.state_timer = duration
        self.set_source(path)

    def react(self):
        if REACTIONS:
            self.show_for(random.choice(REACTIONS), REACTION_TIME)

    def action(self):
        if ACTIONS:
            chosen = random.choice(ACTIONS)
            self.show_for(chosen, ACTION_TIME)

            # Make the jump sprite physically jump too.
            if chosen == sprite("action_jump.png"):
                self.velocity_y = JUMP_SPEED

    def start_idle(self):
        if IDLE:
            self.state = "idle"
            self.state_timer = random.uniform(1.0, 2.5)
            self.set_source(random.choice(IDLE))

    def release_pet(self):
        was_dragging = self.dragging
        self.dragging = False
        self.touch_uid = None

        if was_dragging:
            if self.y <= 0:
                self.y = 0
                self.start_walking()
            else:
                # Let gravity bring it down.
                self.velocity_y = 0

    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return False

        self.touch_uid = touch.uid
        self.touch_start_x = touch.x
        self.touch_start_y = touch.y

        self.drag_offset_x = self.x - touch.x
        self.drag_offset_y = self.y - touch.y

        self.dragging = False
        self.velocity_y = 0
        return True

    def on_touch_move(self, touch):
        if touch.uid != self.touch_uid:
            return False

        if not self.dragging:
            dx = touch.x - self.touch_start_x
            dy = touch.y - self.touch_start_y

            if dx * dx + dy * dy < DRAG_THRESHOLD * DRAG_THRESHOLD:
                return True

            self.dragging = True
            self.state = "dragging"

        self.x = touch.x + self.drag_offset_x
        self.y = touch.y + self.drag_offset_y

        self.x = max(0, min(self.x, Window.width - self.width))
        self.y = max(0, min(self.y, Window.height - self.height))
        return True

    def on_touch_up(self, touch):
        if touch.uid != self.touch_uid:
            return False

        was_dragging = self.dragging
        self.dragging = False
        self.touch_uid = None

        # A normal tap does nothing to movement.
        if was_dragging:
            if self.y <= 0:
                self.y = 0
                self.start_walking()
            else:
                self.velocity_y = 0

        return True

    def update(self, dt):
        # During a real drag, follow the finger and don't run autonomous movement.
        if self.dragging:
            return

        # YouTube mode: sleep and stay still.
        if self.current_app == YOUTUBE:
            if SLEEPY:
                self.state = "youtube"
                self.set_source(SLEEPY)
            return

        # Gravity after a dragged release or a jump.
        if self.y > 0 or self.velocity_y != 0:
            self.velocity_y -= GRAVITY * dt
            self.y += self.velocity_y * dt

            if self.y <= 0:
                self.y = 0
                self.velocity_y = 0
                if self.state in ("jumping", "special"):
                    self.start_walking()

            if self.y > 0:
                return

        # Special animation/action.
        if self.state == "special":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.start_walking()
            return

        # Idle.
        if self.state == "idle":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.start_walking()
            return

        # Normal walking.
        if self.state != "walking":
            self.start_walking()

        self.x += WALK_SPEED * self.direction * dt

        if self.x <= 0:
            self.x = 0
            self.turn()
        elif self.x + self.width >= Window.width:
            self.x = Window.width - self.width
            self.turn()

        self.frame_timer += dt
        if self.frame_timer >= WALK_FRAME_TIME:
            self.frame_timer = 0
            self.frame_index += 1
            self.set_walk_frame()

        # Random turning.
        self.turn_timer += dt
        if self.turn_timer >= self.next_turn:
            self.turn_timer = 0
            self.next_turn = random.uniform(TURN_MIN, TURN_MAX)
            if random.random() < 0.55:
                self.turn()

        # Random idle.
        self.next_idle -= dt
        if self.next_idle <= 0:
            self.next_idle = random.uniform(IDLE_MIN, IDLE_MAX)
            if random.random() < 0.18:
                self.start_idle()


class PetApp(App):
    title = "Chibi Shark Pet"

    def build(self):
        Window.clearcolor = (0.015, 0.02, 0.04, 1)

        root = Widget()
        self.pet = Pet()
        self.pet.pos = (dp(20), 0)
        root.add_widget(self.pet)

        Clock.schedule_interval(self.update, 1 / 60)
        Clock.schedule_interval(self.check_foreground_app, 1.0)
        Clock.schedule_interval(self.random_event, 7.0)

        return root

    def update(self, dt):
        self.pet.update(dt)

    def check_foreground_app(self, dt):
        package = get_foreground_package()

        if package:
            if package in (YOUTUBE, MESSENGER, DISCORD):
                self.pet.current_app = package
            else:
                self.pet.current_app = None

    def random_event(self, dt):
        p = self.pet

        if p.dragging:
            return

        if p.current_app == YOUTUBE:
            return

        if p.y > 0:
            return

        if p.state != "walking":
            return

        if p.current_app in (MESSENGER, DISCORD):
            # More expressive while chatting.
            if random.random() < 0.65:
                p.react()
            else:
                p.action()
        else:
            roll = random.random()
            if roll < 0.25:
                p.react()
            elif roll < 0.40:
                p.action()


if __name__ == "__main__":
    PetApp().run()
