import os
import random
import time
from jnius import autoclass, PythonJavaClass, java_method

# System-wide floating pet service.
# Runs independently of the Kivy Activity after the user grants overlay permission.

YOUTUBE = "com.google.android.youtube"
MESSENGER = "com.facebook.orca"
DISCORD = "com.discord"

PET_DP = 120
WALK_SPEED_DP = 60
FRAME_SECONDS = 0.10
TURN_MIN = 2.5
TURN_MAX = 6.0
EVENT_SECONDS = 7.0
DRAG_THRESHOLD_DP = 12

Service = autoclass("org.kivy.android.PythonService")
service = Service.mService
context = service.getApplicationContext()

Context = autoclass("android.content.Context")
WindowManager = autoclass("android.view.WindowManager")
LayoutParams = autoclass("android.view.WindowManager$LayoutParams")
PixelFormat = autoclass("android.graphics.PixelFormat")
Gravity = autoclass("android.view.Gravity")
MotionEvent = autoclass("android.view.MotionEvent")
ImageView = autoclass("android.widget.ImageView")
ImageViewScaleType = autoclass("android.widget.ImageView$ScaleType")
BitmapFactory = autoclass("android.graphics.BitmapFactory")
Handler = autoclass("android.os.Handler")
Looper = autoclass("android.os.Looper")
System = autoclass("java.lang.System")

wm = context.getSystemService(Context.WINDOW_SERVICE)
assets = context.getAssets()
density = context.getResources().getDisplayMetrics().density
pet_size = int(PET_DP * density)
walk_speed = WALK_SPEED_DP * density
turn_min = TURN_MIN
turn_max = TURN_MAX

def dp(v):
    return int(v * density)


def asset_bitmap(filename):
    try:
        stream = assets.open("assets/" + filename)
        bitmap = BitmapFactory.decodeStream(stream)
        stream.close()
        return bitmap
    except Exception:
        try:
            stream = assets.open(filename)
            bitmap = BitmapFactory.decodeStream(stream)
            stream.close()
            return bitmap
        except Exception:
            return None


# The asset list is kept explicit so Android packaging is predictable.
RIGHT = [f"walk_right_{i}.png" for i in range(1, 9)]
LEFT = [f"walk_left_{i}.png" for i in range(1, 9)]
# The supplied project has walk_left_3.png; older source bundles may have a renamed frame.
if not asset_bitmap("walk_left_3.png") and asset_bitmap("walk_left_3(2).png"):
    LEFT[2] = "walk_left_3(2).png"

IDLE = ["idle_front.png", "idle_left.png", "idle_right.png", "idle_back.png"]
REACTIONS = [
    "expression_happy.png",
    "expression_sad.png",
    "expression_angry.png",
    "expression_blush.png",
    "expression_surprised.png",
]
ACTIONS = [
    "action_jump.png",
    "action_lay.png",
    "action_sit.png",
    "action_wave.png",
    "action_interact.png",
]
SLEEPY = "expression_sleepy.png"

bitmaps = {}
for filename in set(RIGHT + LEFT + IDLE + REACTIONS + ACTIONS + [SLEEPY]):
    bitmaps[filename] = asset_bitmap(filename)


def bitmap(name):
    return bitmaps.get(name)


class TouchListener(PythonJavaClass):
    __javainterfaces__ = ["android/view/View$OnTouchListener"]

    def __init__(self, pet):
        super().__init__()
        self.pet = pet

    @java_method("(Landroid/view/View;Landroid/view/MotionEvent;)Z")
    def onTouch(self, view, event):
        action = event.getActionMasked()
        x = float(event.getRawX())
        y = float(event.getRawY())
        if action == MotionEvent.ACTION_DOWN:
            self.pet.touch_down(x, y)
            return True
        if action == MotionEvent.ACTION_MOVE:
            self.pet.touch_move(x, y)
            return True
        if action in (MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL):
            self.pet.touch_up(x, y)
            return True
        return True


class PetController:
    def __init__(self):
        self.view = ImageView(context)
        self.view.setScaleType(ImageViewScaleType.FIT_CENTER)
        self.view.setAdjustViewBounds(True)
        self.listener = TouchListener(self)
        self.view.setOnTouchListener(self.listener)

        flags = (
            LayoutParams.FLAG_NOT_FOCUSABLE
            | LayoutParams.FLAG_LAYOUT_NO_LIMITS
        )
        self.params = LayoutParams(
            pet_size,
            pet_size,
            LayoutParams.TYPE_APPLICATION_OVERLAY,
            flags,
            PixelFormat.TRANSLUCENT,
        )
        self.params.gravity = Gravity.TOP | Gravity.START
        self.params.x = dp(20)
        self.params.y = 0

        self.x = float(self.params.x)
        self.y = float(self.params.y)
        self.vy = 0.0
        self.direction = 1
        self.frames = RIGHT
        self.frame_index = 0
        self.frame_timer = 0.0
        self.turn_timer = 0.0
        self.next_turn = random.uniform(turn_min, turn_max)
        self.event_timer = EVENT_SECONDS
        self.special_timer = 0.0
        self.state = "walking"
        self.dragging = False
        self.touch_start_x = 0.0
        self.touch_start_y = 0.0
        self.drag_offset_x = 0.0
        self.drag_offset_y = 0.0
        self.current_app = None
        self.app_check_timer = 0.0
        self.last_tick = time.monotonic()
        self.handler = Handler(Looper.getMainLooper())

        self.set_image(self.frames[0])
        wm.addView(self.view, self.params)

    def set_image(self, name):
        b = bitmap(name)
        if b is not None:
            self.view.setImageBitmap(b)

    def update_layout(self):
        self.params.x = int(self.x)
        self.params.y = int(self.y)
        try:
            wm.updateViewLayout(self.view, self.params)
        except Exception:
            pass

    def bounds(self):
        metrics = context.getResources().getDisplayMetrics()
        return max(0, metrics.widthPixels - pet_size), max(0, metrics.heightPixels - pet_size)

    def turn(self):
        self.direction *= -1
        self.frames = RIGHT if self.direction == 1 else LEFT
        self.frame_index = 0
        if self.frames:
            self.set_image(self.frames[0])

    def touch_down(self, x, y):
        self.touch_start_x = x
        self.touch_start_y = y
        self.drag_offset_x = self.x - x
        self.drag_offset_y = self.y - y
        self.dragging = False
        self.vy = 0

    def touch_move(self, x, y):
        dx = x - self.touch_start_x
        dy = y - self.touch_start_y
        if not self.dragging and dx * dx + dy * dy < dp(DRAG_THRESHOLD_DP) ** 2:
            return
        self.dragging = True
        max_x, max_y = self.bounds()
        self.x = max(0, min(max_x, x + self.drag_offset_x))
        self.y = max(0, min(max_y, y + self.drag_offset_y))
        self.update_layout()

    def touch_up(self, x, y):
        if self.dragging:
            self.dragging = False
            if self.y <= 0:
                self.y = 0
                self.state = "walking"
            else:
                self.vy = 0
        # A tap intentionally does not stop the pet.

    def special(self, name, duration=1.3):
        if bitmap(name) is not None:
            self.state = "special"
            self.special_timer = duration
            self.set_image(name)
            if name == "action_jump.png":
                self.vy = -dp(500)

    def foreground_package(self):
        try:
            UsageStats = autoclass("android.app.usage.UsageStatsManager")
            UsageEvent = autoclass("android.app.usage.UsageEvents$Event")
            manager = context.getSystemService(Context.USAGE_STATS_SERVICE)
            now = System.currentTimeMillis()
            events = manager.queryEvents(now - 4000, now)
            event = UsageEvent()
            last = None
            while events.hasNextEvent():
                events.getNextEvent(event)
                if event.getEventType() == 1:
                    p = event.getPackageName()
                    if p:
                        last = str(p)
            return last
        except Exception:
            return None

    def tick(self, dt):
        self.app_check_timer -= dt
        if self.app_check_timer <= 0:
            self.app_check_timer = 1.0
            self.current_app = self.foreground_package()

        if self.current_app == YOUTUBE and bitmap(SLEEPY):
            self.state = "youtube"
            self.vy = 0
            self.set_image(SLEEPY)
            return

        if self.dragging:
            return

        if self.state == "youtube":
            self.state = "walking"
            self.frame_index = 0

        # Falling/jumping uses screen coordinates with gravity downward.
        if self.y > 0 or self.vy != 0:
            self.vy += dp(1000) * dt
            self.y += self.vy * dt
            if self.y >= 0 and self.vy >= 0:
                self.y = 0
                self.vy = 0
                self.state = "walking"
            self.update_layout()
            return

        if self.state == "special":
            self.special_timer -= dt
            if self.special_timer <= 0:
                self.state = "walking"
                self.frame_index = 0
                self.set_image(self.frames[0])
            return

        # Walk.
        self.x += walk_speed * self.direction * dt
        max_x, _ = self.bounds()
        if self.x <= 0:
            self.x = 0
            self.turn()
        elif self.x >= max_x:
            self.x = max_x
            self.turn()

        self.frame_timer += dt
        if self.frame_timer >= FRAME_SECONDS and self.frames:
            self.frame_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.set_image(self.frames[self.frame_index])

        self.turn_timer += dt
        if self.turn_timer >= self.next_turn:
            self.turn_timer = 0
            self.next_turn = random.uniform(turn_min, turn_max)
            if random.random() < 0.55:
                self.turn()

        self.event_timer -= dt
        if self.event_timer <= 0:
            self.event_timer = EVENT_SECONDS
            if self.current_app in (MESSENGER, DISCORD):
                self.special(random.choice(REACTIONS if random.random() < 0.65 else ACTIONS), 1.3)
            elif random.random() < 0.35:
                self.special(random.choice(REACTIONS + ACTIONS), 1.3)

        self.update_layout()

    def run(self):
        while True:
            now = time.monotonic()
            dt = min(0.05, now - self.last_tick)
            self.last_tick = now
            self.handler.post(self._tick_runnable)
            time.sleep(0.05)

    def _tick(self):
        try:
            now = time.monotonic()
            dt = min(0.05, now - self.last_tick)
            self.last_tick = now
            self.tick(dt)
        except Exception:
            pass


class TickRunnable(PythonJavaClass):
    __javainterfaces__ = ["java/lang/Runnable"]
    def __init__(self, pet):
        super().__init__()
        self.pet = pet
    @java_method("()V")
    def run(self):
        self.pet._tick()


# Replace the helper call with a persistent Java Runnable object.
pet = PetController()
pet._tick_runnable = TickRunnable(pet)

# Keep the Python service alive. p4a's foreground/sticky service handles the Android side.
try:
    service.setAutoRestartService(True)
except Exception:
    pass

while True:
    pet.handler.post(pet._tick_runnable)
    time.sleep(0.05)
