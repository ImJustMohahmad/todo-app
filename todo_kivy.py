"""
اپ To-Do List با Kivy — قابل ساخت به صورت APK اندروید
"""

import json
import os

from kivy.app import App
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

# ─── Paths ───────────────────────────────────────────────────────────────────

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
FONT_DIR     = os.path.join(BASE_DIR, "fonts")
FONT_REGULAR = os.path.join(FONT_DIR, "Vazirmatn-Regular.ttf")
FONT_BOLD    = os.path.join(FONT_DIR, "Vazirmatn-Bold.ttf")

_DATA_FILE = None  # resolved inside build() so Android user_data_dir is used

# ─── Colours ─────────────────────────────────────────────────────────────────

BG        = (14/255, 14/255, 14/255, 1)   # #0E0E0E
CARD      = (26/255, 26/255, 26/255, 1)   # #1A1A1A
WHITE     = (1, 1, 1, 1)
WHITE_DIM = (1, 1, 1, 0.28)

# ─── Helpers ─────────────────────────────────────────────────────────────────

def to_persian(n: int) -> str:
    digits = "۰۱۲۳۴۵۶۷۸۹"
    return "".join(digits[int(d)] for d in str(n))


def register_font() -> str:
    if os.path.exists(FONT_REGULAR):
        LabelBase.register(
            "Vazirmatn",
            fn_regular=FONT_REGULAR,
            fn_bold=FONT_BOLD if os.path.exists(FONT_BOLD) else FONT_REGULAR,
        )
        return "Vazirmatn"
    return "Roboto"

# ─── Reusable rounded-background base ────────────────────────────────────────

class Card(BoxLayout):
    """BoxLayout with a dark rounded rectangle drawn behind it."""
    def __init__(self, bg=None, radius=10, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            self._col  = Color(*(bg or CARD))
            self._rect = RoundedRectangle(pos=self.pos, size=self.size,
                                          radius=[dp(radius)])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self._rect.pos  = self.pos
        self._rect.size = self.size

# ─── Task row ────────────────────────────────────────────────────────────────

class TaskRow(Card):
    def __init__(self, index, text, done, on_toggle, on_delete, font, **kw):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(54),
            padding=[dp(10), dp(0), dp(10), dp(0)],
            spacing=dp(8),
            **kw,
        )

        # ── × delete button — physical left ──────────────────────────────
        del_btn = Button(
            text="×",
            font_size=dp(22),
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={"center_y": 0.5},
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 0.35),
        )
        del_btn.bind(on_release=lambda *_: on_delete(index))
        self.add_widget(del_btn)

        # ── task text — middle, stretches ────────────────────────────────
        display = ("[s]" + text + "[/s]") if done else text
        lbl = Label(
            text=display,
            markup=True,
            font_name=font,
            font_size=dp(14),
            color=WHITE_DIM if done else WHITE,
            halign="right",
            valign="middle",
            size_hint=(1, 1),
        )
        lbl.bind(size=lbl.setter("text_size"))
        self.add_widget(lbl)

        # ── checkbox — physical right (RTL feel) ─────────────────────────
        cb = CheckBox(
            active=done,
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={"center_y": 0.5},
            color=WHITE,
        )
        # bind AFTER construction so the initial active= doesn't fire toggle
        cb.bind(active=lambda w, val: on_toggle(index, val))
        self.add_widget(cb)

# ─── Application ─────────────────────────────────────────────────────────────

class TodoApp(App):
    title = "Todo"

    def build(self):
        global _DATA_FILE
        Window.clearcolor = BG
        _DATA_FILE = os.path.join(self.user_data_dir, "tasks.json")

        self.tasks = []
        self.font  = register_font()
        self.load_tasks()

        root = BoxLayout(orientation="vertical")
        root.add_widget(self._make_header())
        root.add_widget(self._make_sep())
        root.add_widget(self._make_body())

        self.refresh_list()
        return root

    # ── Header ───────────────────────────────────────────────────────────────

    def _make_header(self):
        hdr = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(92),
            padding=[dp(20), dp(14), dp(20), dp(14)],
            spacing=dp(12),
        )
        with hdr.canvas.before:
            Color(*BG)
            _r = Rectangle(pos=hdr.pos, size=hdr.size)
        hdr.bind(pos=lambda w, v: setattr(_r, "pos", v),
                 size=lambda w, v: setattr(_r, "size", v))

        # ── counter — physical LEFT, fixed narrow width ───────────────────
        self.counter_lbl = Label(
            text="۰/۰",
            font_name=self.font,
            bold=True,
            font_size=dp(22),
            color=WHITE,
            halign="left",
            valign="middle",
            size_hint=(None, 1),
            width=dp(80),
        )
        self.counter_lbl.bind(size=self.counter_lbl.setter("text_size"))
        hdr.add_widget(self.counter_lbl)

        # ── title + subtitle — expand to fill rest, right-aligned ─────────
        title_col = BoxLayout(orientation="vertical", size_hint=(1, 1))

        ttl = Label(
            text="مدیریت کار های روزانه ات",
            font_name=self.font,
            bold=True,
            font_size=dp(17),
            color=WHITE,
            halign="right",
            valign="bottom",
            size_hint=(1, 1),
        )
        ttl.bind(size=ttl.setter("text_size"))

        sub = Label(
            text="ساخته شده توسط محمدرضا شایان نژاد",
            font_name=self.font,
            font_size=dp(10),
            color=(1, 1, 1, 0.30),
            halign="right",
            valign="top",
            size_hint=(1, 1),
        )
        sub.bind(size=sub.setter("text_size"))

        title_col.add_widget(ttl)
        title_col.add_widget(sub)
        hdr.add_widget(title_col)
        return hdr

    # ── Separator ─────────────────────────────────────────────────────────────

    def _make_sep(self):
        sep = Widget(size_hint_y=None, height=dp(1))
        with sep.canvas:
            Color(1, 1, 1, 0.07)
            _r = Rectangle(pos=sep.pos, size=sep.size)
        sep.bind(pos=lambda w, v: setattr(_r, "pos", v),
                 size=lambda w, v: setattr(_r, "size", v))
        return sep

    # ── Body ─────────────────────────────────────────────────────────────────

    def _make_body(self):
        body = BoxLayout(
            orientation="vertical",
            padding=[dp(20), dp(20), dp(20), dp(16)],
            spacing=dp(14),
        )

        sv = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.task_list = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint_y=None,
        )
        self.task_list.bind(minimum_height=self.task_list.setter("height"))
        sv.add_widget(self.task_list)
        body.add_widget(sv)

        body.add_widget(self._make_input_row())
        return body

    # ── Input row ────────────────────────────────────────────────────────────

    def _make_input_row(self):
        frame = Card(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(52),
            padding=[dp(8), dp(5), dp(5), dp(5)],
            spacing=dp(8),
        )

        self.inp = TextInput(
            hint_text="یک کار جدید بنویس...",
            multiline=False,
            font_name=self.font,
            font_size=dp(14),
            # remove ALL default texture/border so Card's bg shows through
            background_normal="",
            background_active="",
            background_color=(0, 0, 0, 0),
            foreground_color=WHITE,
            hint_text_color=(1, 1, 1, 0.35),
            cursor_color=WHITE,
            padding=[dp(6), dp(10), dp(6), dp(10)],
        )
        self.inp.bind(on_text_validate=lambda *_: self.add_task())
        frame.add_widget(self.inp)

        # white rounded "اضافه کن" button
        add_btn = Button(
            text="اضافه کن",
            font_name=self.font,
            bold=True,
            font_size=dp(13),
            size_hint=(None, None),
            size=(dp(110), dp(42)),
            pos_hint={"center_y": 0.5},
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=(0.055, 0.055, 0.055, 1),
        )
        with add_btn.canvas.before:
            Color(*WHITE)
            _rb = RoundedRectangle(pos=add_btn.pos, size=add_btn.size,
                                   radius=[dp(8)])
        add_btn.bind(
            pos=lambda w, v: setattr(_rb, "pos", v),
            size=lambda w, v: setattr(_rb, "size", v),
        )
        add_btn.bind(on_release=lambda *_: self.add_task())
        frame.add_widget(add_btn)
        return frame

    # ── Logic ────────────────────────────────────────────────────────────────

    def add_task(self):
        text = self.inp.text.strip()
        if not text:
            return
        self.tasks.append({"text": text, "done": False})
        self.inp.text = ""
        self.refresh_list()
        self.save_tasks()

    def toggle_task(self, index, val):
        if 0 <= index < len(self.tasks):
            self.tasks[index]["done"] = val
            self.refresh_list()
            self.save_tasks()

    def delete_task(self, index):
        if 0 <= index < len(self.tasks):
            del self.tasks[index]
            self.refresh_list()
            self.save_tasks()

    def refresh_list(self):
        self.task_list.clear_widgets()
        for i, t in enumerate(self.tasks):
            self.task_list.add_widget(TaskRow(
                index=i,
                text=t["text"],
                done=t["done"],
                on_toggle=self.toggle_task,
                on_delete=self.delete_task,
                font=self.font,
            ))
        done      = sum(1 for t in self.tasks if t["done"])
        remaining = len(self.tasks) - done
        self.counter_lbl.text = (
            f"{to_persian(remaining)}/{to_persian(len(self.tasks))}"
        )

    # ── Persistence ──────────────────────────────────────────────────────────

    def save_tasks(self):
        path = _DATA_FILE or os.path.join(BASE_DIR, "tasks.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("خطا در ذخیره:", e)

    def load_tasks(self):
        # prefer user_data_dir (Android-safe), fall back to source dir
        for path in (_DATA_FILE, os.path.join(BASE_DIR, "tasks.json")):
            if path and os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self.tasks = json.load(f)
                    return
                except Exception as e:
                    print("خطا در بارگذاری:", e)
        self.tasks = []


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    TodoApp().run()
