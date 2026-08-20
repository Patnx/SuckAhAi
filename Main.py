import os
import json
import threading

import requests

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.clipboard import Clipboard

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.dropdown import DropDown
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton

from kivy.uix.screenmanager import (
    ScreenManager,
    Screen
)

from openhands_api import OpenHandsAPI


# ============================================================
# THEME
# ============================================================

THEMES = {
    "dark": {
        "background": (0.10, 0.11, 0.15, 1),
        "surface": (0.16, 0.18, 0.24, 1),
        "accent": (0.25, 0.55, 0.95, 1),
        "text": (0.92, 0.93, 0.96, 1),
        "muted": (0.55, 0.58, 0.66, 1),
        "you": (0.18, 0.45, 0.85, 1),
        "ai": (0.22, 0.56, 0.32, 1),
        "system": (0.35, 0.38, 0.46, 1),
        "error": (0.75, 0.25, 0.25, 1),
    },
    "light": {
        "background": (0.93, 0.94, 0.96, 1),
        "surface": (0.84, 0.86, 0.90, 1),
        "accent": (0.20, 0.45, 0.85, 1),
        "text": (0.12, 0.13, 0.17, 1),
        "muted": (0.40, 0.42, 0.48, 1),
        "you": (0.20, 0.40, 0.78, 1),
        "ai": (0.18, 0.45, 0.28, 1),
        "system": (0.60, 0.63, 0.70, 1),
        "error": (0.80, 0.22, 0.22, 1),
    },
}

THEME = THEMES["dark"]


def current_theme():

    return THEME


def apply_theme(name):

    global THEME

    THEME = THEMES.get(
        name,
        THEMES["dark"]
    )


BACKGROUND = THEME["background"]
SURFACE = THEME["surface"]
ACCENT = THEME["accent"]
TEXT = THEME["text"]
MUTED = THEME["muted"]
YOU_COLOR = THEME["you"]
AI_COLOR = THEME["ai"]
SYSTEM_COLOR = THEME["system"]
ERROR_COLOR = THEME["error"]

SPEAKER_COLORS = {
    "You": YOU_COLOR,
    "OpenHands": AI_COLOR,
    "SYSTEM": SYSTEM_COLOR,
    "GIT CHANGES": SYSTEM_COLOR,
    "GIT DIFF": SYSTEM_COLOR,
}


def speaker_color(speaker):

    if "ERROR" in speaker:
        return THEME["error"]

    return SPEAKER_COLORS.get(
        speaker,
        THEME["surface"]
    )


# ============================================================
# SETTINGS
# ============================================================

_SETTINGS_FILE = None


def settings_file():

    global _SETTINGS_FILE

    if _SETTINGS_FILE is not None:
        return _SETTINGS_FILE

    try:
        root = App.get_running_app().user_data_dir
    except Exception:
        root = os.path.expanduser("~")

    os.makedirs(
        root,
        exist_ok=True
    )

    _SETTINGS_FILE = os.path.join(
        root,
        "openhands_client_settings.json"
    )

    return _SETTINGS_FILE


def load_settings():

    path = settings_file()

    if not os.path.exists(path):
        return {}

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as error:

        print(
            "Could not load settings:",
            error
        )

        return {}


def save_settings(
    settings
):

    try:

        with open(
            settings_file(),
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                settings,
                file,
                indent=2
            )

    except Exception as error:

        print(
            "Could not save settings:",
            error
        )




# ============================================================
# CHAT MESSAGE
# ============================================================

class ChatMessage(Label):

    def __init__(
        self,
        speaker,
        message,
        **kwargs
    ):

        super().__init__(
            **kwargs
        )

        self.full_text = (
            f"{speaker}\n\n{message}"
        )

        self.text = self.full_text

        self.color = TEXT

        self.size_hint_y = None

        self.padding = (
            dp(12),
            dp(12)
        )

        color = speaker_color(
            speaker
        )

        with self.canvas.before:

            from kivy.graphics import (
                Color,
                RoundedRectangle
            )

            Color(*color)

            self.bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(8)]
            )

        self.bind(
            pos=self._update_bg,
            size=self._update_bg,
            width=self.update_text_size,
            texture_size=self.update_height
        )

    def _update_bg(
        self,
        *args
    ):

        self.bg.pos = self.pos

        self.bg.size = self.size

    def on_touch_down(
        self,
        touch
    ):

        if touch.is_double_tap:

            if self.collide_point(
                *touch.pos
            ):

                Clipboard.copy(
                    self.full_text
                )

                return True

        return super().on_touch_down(
            touch
        )

    def update_text_size(
        self,
        instance,
        width
    ):

        self.text_size = (
            width - dp(24),
            None
        )

    def update_height(
        self,
        instance,
        texture_size
    ):

        self.height = (
            texture_size[1]
            + dp(24)
        )


# ============================================================
# SETTINGS SCREEN
# ============================================================

class SettingsScreen(Screen):

    def __init__(
        self,
        app,
        **kwargs
    ):

        super().__init__(
            **kwargs
        )

        self.app = app

        root = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = BoxLayout(
            size_hint_y=None,
            height=dp(55)
        )

        title = Label(
            text="Settings",
            font_size=24,
            color=TEXT
        )

        back = Button(
            text="Back",
            size_hint_x=0.2,
            background_color=ACCENT
        )

        back.bind(
            on_press=self.go_back
        )

        header.add_widget(
            title
        )

        header.add_widget(
            back
        )

        root.add_widget(
            header
        )

        # ----------------------------------------------------
        # API KEY
        # ----------------------------------------------------

        root.add_widget(
            Label(
                text="OpenHands API Key",
                color=TEXT,
                size_hint_y=None,
                height=dp(30)
            )
        )

        key_row = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            spacing=dp(5)
        )

        self.api_key_input = TextInput(
            hint_text="Paste API key",
            password=True,
            multiline=False,
            background_color=(1, 1, 1, 1)
        )

        show_button = Button(
            text="Show",
            size_hint_x=0.2,
            background_color=ACCENT
        )

        show_button.bind(
            on_press=self.toggle_key
        )

        key_row.add_widget(
            self.api_key_input
        )

        key_row.add_widget(
            show_button
        )

        root.add_widget(
            key_row
        )

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        save_button = Button(
            text="Save API Key",
            size_hint_y=None,
            height=dp(50),
            background_color=AI_COLOR
        )

        save_button.bind(
            on_press=self.save_key
        )

        root.add_widget(
            save_button
        )

        # ----------------------------------------------------
        # TEST
        # ----------------------------------------------------

        self.test_button = Button(
            text="Test API Key",
            size_hint_y=None,
            height=dp(50),
            background_color=ACCENT
        )

        self.test_button.bind(
            on_press=self.test_key
        )

        root.add_widget(
            self.test_button
        )

        # ----------------------------------------------------
        # DELETE
        # ----------------------------------------------------

        delete_button = Button(
            text="Delete Saved Key",
            size_hint_y=None,
            height=dp(50),
            background_color=ERROR_COLOR
        )

        delete_button.bind(
            on_press=self.delete_key
        )

        root.add_widget(
            delete_button
        )

        # ----------------------------------------------------
        # SERVER
        # ----------------------------------------------------

        root.add_widget(
            Label(
                text="Server URL",
                color=TEXT,
                size_hint_y=None,
                height=dp(30)
            )
        )

        self.server_input = TextInput(
            text="https://app.all-hands.dev",
            multiline=False,
            size_hint_y=None,
            height=dp(50),
            background_color=(1, 1, 1, 1)
        )

        root.add_widget(
            self.server_input
        )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        self.status = Label(
            text="",
            color=TEXT,
            size_hint_y=None,
            height=dp(100)
        )

        root.add_widget(
            self.status
        )

        root.add_widget(
            Label()
        )

        self.add_widget(
            root
        )

    # ========================================================
    # LOAD
    # ========================================================

    def on_pre_enter(
        self,
        *args
    ):

        settings = load_settings()

        self.api_key_input.text = (
            settings.get(
                "api_key",
                ""
            )
        )

        self.server_input.text = (
            settings.get(
                "server_url",
                "https://app.all-hands.dev"
            )
        )

    # ========================================================
    # SHOW KEY
    # ========================================================

    def toggle_key(
        self,
        button
    ):

        self.api_key_input.password = (
            not self.api_key_input.password
        )

        button.text = (
            "Hide"
            if not self.api_key_input.password
            else "Show"
        )

    # ========================================================
    # SAVE KEY
    # ========================================================

    def save_key(
        self,
        *args
    ):

        key = (
            self.api_key_input.text
            .strip()
        )

        server = (
            self.server_input.text
            .strip()
        )

        if not key:

            self.status.text = (
                "Enter an API key first."
            )

            return

        save_settings({
            "api_key": key,
            "server_url": server
        })

        self.status.text = (
            "API key saved locally."
        )

    # ========================================================
    # TEST KEY
    # ========================================================

    def test_key(
        self,
        *args
    ):

        key = (
            self.api_key_input.text
            .strip()
        )

        server = (
            self.server_input.text
            .strip()
        )

        if not key:

            self.status.text = (
                "Enter an API key first."
            )

            return

        self.test_button.disabled = True

        self.status.text = (
            "Testing..."
        )

        threading.Thread(
            target=self._test_worker,
            args=(
                key,
                server
            ),
            daemon=True
        ).start()

    def _test_worker(
        self,
        key,
        server
    ):

        try:

            api = OpenHandsAPI(
                key,
                server
            )

            result = api.get_credits()

            Clock.schedule_once(
                lambda dt:
                self.test_success()
            )

        except Exception as error:

            error_text = str(error)

            Clock.schedule_once(
                lambda dt,
                error_text=error_text:
                self.test_failed(
                    error_text
                )
            )

    def test_success(
        self
    ):

        self.test_button.disabled = False

        self.status.text = (
            "API key works!"
        )

    def test_failed(
        self,
        error
    ):

        self.test_button.disabled = False

        self.status.text = (
            "API test failed:\n\n"
            + error
        )

    # ========================================================
    # DELETE
    # ========================================================

    def delete_key(
        self,
        *args
    ):

        settings = load_settings()

        settings.pop(
            "api_key",
            None
        )

        save_settings(
            settings
        )

        self.api_key_input.text = ""

        self.status.text = (
            "API key deleted."
        )

    # ========================================================
    # BACK
    # ========================================================

    def go_back(
        self,
        *args
    ):

        self.app.screen_manager.current = (
            "chat"
        )


# ============================================================
# CHAT SCREEN
# ============================================================

class ChatScreen(Screen):

    def __init__(
        self,
        app,
        **kwargs
    ):

        super().__init__(
            **kwargs
        )

        self.app = app

        self.api = None

        self.conversation_id = None

        self.start_task_id = None

        self.seen_event_ids = set()

        self.poll_event = None

        self.last_status = None

        self.finished = False

        self.reply_received = False

        self.debug_enabled = (
            os.getenv("DEBUG") == "1"
        )

        self._poll_active = False

        self.event_cursor = None

        self.repo_dropdown = None

        self.repos_cache = []

        self.stream_label = None

        self.stream_buffer = []

        self.theme_name = (
            load_settings()
            .get("theme", "dark")
        )

        apply_theme(self.theme_name)

        # ----------------------------------------------------
        # ROOT
        # ----------------------------------------------------

        root = BoxLayout(
            orientation="vertical",
            padding=dp(8),
            spacing=dp(8)
        )

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = BoxLayout(
            size_hint_y=None,
            height=dp(55)
        )

        title = Label(
            text="OpenHands AI",
            font_size=22,
            color=TEXT
        )

        settings = Button(
            text="Settings",
            size_hint_x=0.2,
            background_color=ACCENT
        )

        settings.bind(
            on_press=self.open_settings
        )

        header.add_widget(
            title
        )

        header.add_widget(
            settings
        )

        root.add_widget(
            header
        )

        # ----------------------------------------------------
        # REPOSITORY
        # ----------------------------------------------------

        repo_row = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            spacing=dp(5)
        )

        self.repo_input = TextInput(
            hint_text="GitHub repository: user/repo or tap to pick",
            multiline=False
        )

        self.repo_input.bind(
            text=self.on_repo_text,
            focus=(
                lambda w, focused:
                self.maybe_open_dropdown(focused)
            )
        )

        self.start_button = Button(
            text="Start",
            size_hint_x=0.18,
            background_color=ACCENT
        )

        self.start_button.bind(
            on_press=self.start
        )

        repo_row.add_widget(
            self.repo_input
        )

        repo_row.add_widget(
            self.start_button
        )

        root.add_widget(
            repo_row
        )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        status_row = BoxLayout(
            size_hint_y=None,
            height=dp(45)
        )

        self.status_label = Label(
            text="Status: NOT CONNECTED",
            color=TEXT
        )

        self.credits_label = Label(
            text="Credits: ?",
            color=MUTED
        )

        status_row.add_widget(
            self.status_label
        )

        status_row.add_widget(
            self.credits_label
        )

        root.add_widget(
            status_row
        )

        # ----------------------------------------------------
        # CHAT
        # ----------------------------------------------------

        self.scroll = ScrollView()

        self.chat = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8),
            padding=dp(5)
        )

        self.chat.bind(
            minimum_height=
            self.chat.setter(
                "height"
            )
        )

        self.scroll.add_widget(
            self.chat
        )

        root.add_widget(
            self.scroll
        )

        # ----------------------------------------------------
        # MESSAGE INPUT
        # ----------------------------------------------------

        input_row = BoxLayout(
            size_hint_y=None,
            height=dp(75),
            spacing=dp(5)
        )

        self.message_input = TextInput(
            hint_text="Type a message...",
            multiline=True
        )

        self.send_button = Button(
            text="SEND",
            size_hint_x=0.18,
            background_color=AI_COLOR
        )

        self.send_button.bind(
            on_press=self.send
        )

        input_row.add_widget(
            self.message_input
        )

        input_row.add_widget(
            self.send_button
        )

        root.add_widget(
            input_row
        )

        # ----------------------------------------------------
        # GIT
        # ----------------------------------------------------

        git_row = BoxLayout(
            size_hint_y=None,
            height=dp(45),
            spacing=dp(5)
        )

        changes = Button(
            text="Git Changes",
            background_color=ACCENT
        )

        diff = Button(
            text="Git Diff",
            background_color=ACCENT
        )

        changes.bind(
            on_press=self.get_changes
        )

        diff.bind(
            on_press=self.get_diff
        )

        git_row.add_widget(
            changes
        )

        git_row.add_widget(
            diff
        )

        root.add_widget(
            git_row
        )

        # ----------------------------------------------------
        # SETTINGS ROW
        # ----------------------------------------------------

        settings_row = BoxLayout(
            size_hint_y=None,
            height=dp(45),
            spacing=dp(5)
        )

        theme_toggle = ToggleButton(
            text=(
                "Light theme"
                if self.theme_name == "dark"
                else "Dark theme"
            ),
            background_color=ACCENT
        )

        theme_toggle.bind(
            on_press=self.on_theme_toggle
        )

        self.theme_label = theme_toggle

        settings_row.add_widget(
            self.theme_label
        )

        root.add_widget(
            settings_row
        )

        self.add_widget(
            root
        )

        Clock.schedule_once(
            lambda dt:
            self.ask_github_username()
        )

    # ========================================================
    # REPO DROPDOWN
    # ========================================================

    def maybe_open_dropdown(
        self,
        focused
    ):

        if focused:
            self.refresh_repos()
        elif self.repo_dropdown is not None:
            self.repo_dropdown.dismiss()

    def on_repo_text(
        self,
        widget,
        text
    ):

        self.refresh_repos(prefix=text)

    def refresh_repos(
        self,
        prefix=""
    ):

        if self.repo_dropdown is not None:

            self.repo_dropdown.dismiss()

        dropdown = DropDown()

        for name in self.repos_cache:

            if (
                prefix
                and prefix.lower()
                not in name.lower()
            ):
                continue

            btn = Button(
                text=name,
                size_hint_y=None,
                height=dp(40)
            )

            btn.bind(
                on_release=lambda b:
                self.select_repo(b)
            )

            dropdown.add_widget(btn)

        if dropdown.container.children:

            dropdown.open(
                self.repo_input
            )

            self.repo_dropdown = dropdown

    def select_repo(
        self,
        button
    ):

        self.repo_input.text = button.text

        if self.repo_dropdown is not None:

            self.repo_dropdown.dismiss()

            self.repo_dropdown = None

    def fetch_user_repos(
        self,
        username
    ):

        try:

            response = requests.get(
                (
                    f"https://api.github.com/"
                    f"users/{username}/repos"
                ),
                params={
                    "per_page": 100,
                    "type": "owner"
                },
                timeout=5
            )

            response.raise_for_status()

            self.repos_cache = [
                r.get("full_name", "")
                for r in response.json()
                if r.get("full_name")
            ]

        except Exception as error:

            print(
                "Repo fetch error:",
                error
            )

    # ========================================================
    # GITHUB USERNAME POPUP
    # ========================================================

    def ask_github_username(self):

        settings = load_settings()

        if settings.get("github_user") is not None:

            github_user = (
                settings["github_user"]
            )

            if github_user:

                threading.Thread(
                    target=(
                        lambda: self.fetch_user_repos(
                            github_user
                        )
                    ),
                    daemon=True
                ).start()

            return

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(12)
        )

        label = Label(
            text=(
                "Optional: your GitHub username\n"
                "(lets me list your public repos)."
            ),
            size_hint_y=None,
            height=dp(60)
        )

        username_input = TextInput(
            hint_text="GitHub username",
            multiline=False
        )

        buttons = BoxLayout(
            size_hint_y=None,
            height=dp(44),
            spacing=dp(6)
        )

        save_button = Button(
            text="Save",
            background_color=AI_COLOR
        )

        skip_button = Button(
            text="Skip",
            background_color=MUTED
        )

        popup = Popup(
            title="GitHub username",
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=False
        )

        def save(_):

            settings = load_settings()

            settings["github_user"] = (
                username_input.text
                .strip()
                or None
            )

            save_settings(settings)

            popup.dismiss()

            if settings["github_user"]:

                threading.Thread(
                    target=(
                        lambda:
                        self.fetch_user_repos(
                            settings[
                                "github_user"
                            ]
                        )
                    ),
                    daemon=True
                ).start()

        def skip(_):

            settings = load_settings()

            settings["github_user"] = None

            save_settings(settings)

            popup.dismiss()

        save_button.bind(on_press=save)

        skip_button.bind(on_press=skip)

        buttons.add_widget(save_button)

        buttons.add_widget(skip_button)

        content.add_widget(label)

        content.add_widget(username_input)

        content.add_widget(buttons)

        popup.open()

    # ========================================================
    # THEME
    # ========================================================

    def on_theme_toggle(
        self,
        widget
    ):

        self.theme_name = (
            "light"
            if self.theme_name == "dark"
            else "dark"
        )

        apply_theme(self.theme_name)

        settings = load_settings()

        settings["theme"] = self.theme_name

        save_settings(settings)

        self.theme_label.text = (
            "Light theme"
            if self.theme_name == "dark"
            else "Dark theme"
        )

        self.theme_label.background_color = (
            THEME["accent"]
        )

    # ========================================================
    # API
    # ========================================================

    def setup_api(
        self
    ):

        settings = load_settings()

        key = settings.get(
            "api_key"
        )

        server = settings.get(
            "server_url",
            "https://app.all-hands.dev"
        )

        if not key:

            self.add_message(
                "SYSTEM",
                "No API key configured.\n\n"
                "Open Settings and add your API key."
            )

            self.open_settings()

            return False

        self.api = OpenHandsAPI(
            key,
            server
        )

        return True

    # ========================================================
    # START
    # ========================================================

    def start(
        self,
        *args
    ):

        if not self.setup_api():
            return

        repository = (
            self.repo_input.text
            .strip()
        )

        message = (
            self.message_input.text
            .strip()
        )

        if not repository:

            self.add_message(
                "ERROR",
                "Enter a repository.\n\n"
                "Example:\n"
                "Patnx/TestApp"
            )

            return

        if not message:

            self.add_message(
                "ERROR",
                "Enter an initial message."
            )

            return

        self.start_button.disabled = True

        self.send_button.disabled = True

        self.set_status(
            "CREATING CONVERSATION..."
        )

        self.add_message(
            "You",
            message
        )

        self.message_input.text = ""

        threading.Thread(
            target=self._start_worker,
            args=(
                repository,
                message
            ),
            daemon=True
        ).start()

    def _start_worker(
        self,
        repository,
        message
    ):

        try:

            result = (
                self.api.start_conversation(
                    repository,
                    message
                )
            )

            print(
                "\n"
                "================ START RESPONSE ================\n"
            )

            print(
                json.dumps(
                    result,
                    indent=2
                )
            )

            print(
                "\n"
                "==================================================\n"
            )

            task_id = (
                result.get("id")
                or result.get("task_id")
            )

            conversation_id = (
                result.get(
                    "app_conversation_id"
                )
            )

            if conversation_id:

                Clock.schedule_once(
                    lambda dt,
                    conversation_id=conversation_id:
                    self.conversation_ready(
                        conversation_id
                    )
                )

                return

            if not task_id:

                raise RuntimeError(
                    "OpenHands did not return "
                    "a start task ID.\n\n"
                    + json.dumps(
                        result,
                        indent=2
                    )
                )

            self.start_task_id = task_id

            Clock.schedule_once(
                lambda dt:
                self.set_status(
                    "PREPARING..."
                )
            )

            Clock.schedule_once(
                self.poll_start_task,
                1
            )

        except Exception as error:

            error_text = str(error)

            Clock.schedule_once(
                lambda dt,
                error_text=error_text:
                self.api_error(
                    error_text
                )
            )

    # ========================================================
    # START TASK POLLING
    # ========================================================

    def poll_start_task(
        self,
        dt
    ):

        if not self.start_task_id:
            return

        threading.Thread(
            target=self._start_task_worker,
            daemon=True
        ).start()

    def _start_task_worker(
        self
    ):

        try:

            result = (
                self.api.get_start_task(
                    self.start_task_id
                )
            )

            print(
                "\n--- START TASK ---"
            )

            print(
                json.dumps(
                    result,
                    indent=2
                )
            )

            Clock.schedule_once(
                lambda dt,
                result=result:
                self.process_start_task(
                    result
                )
            )

        except Exception as error:

            error_text = str(error)

            Clock.schedule_once(
                lambda dt,
                error_text=error_text:
                self.api_error(
                    error_text
                )
            )

    def process_start_task(
        self,
        result
    ):

        task = None

        if isinstance(
            result,
            list
        ):

            if result:
                task = result[0]

        elif isinstance(
            result,
            dict
        ):

            tasks = (
                result.get("items")
                or result.get("tasks")
                or result.get("data")
            )

            if (
                isinstance(tasks, list)
                and tasks
            ):

                task = tasks[0]

            else:

                task = result

        if not task:
            return

        status = str(
            task.get(
                "status",
                ""
            )
        ).upper()

        detail = task.get(
            "detail"
        )

        conversation_id = (
            task.get(
                "app_conversation_id"
            )
            or task.get(
                "conversation_id"
            )
        )

        if status != self.last_status:

            self.last_status = status

            self.set_status(
                status
            )

        # ----------------------------------------------------
        # READY
        # ----------------------------------------------------

        if conversation_id:

            self.conversation_ready(
                conversation_id
            )

            return

        # ----------------------------------------------------
        # ERROR
        # ----------------------------------------------------

        if status in (
            "ERROR",
            "FAILED",
            "CANCELLED"
        ):

            if detail:

                message = (
                    "OpenHands failed to start:\n\n"
                    + str(detail)
                )

            else:

                message = (
                    "OpenHands failed to start:\n\n"
                    + json.dumps(
                        task,
                        indent=2
                    )
                )

            self.api_error(
                message
            )

            return

        # ----------------------------------------------------
        # KEEP WAITING
        # ----------------------------------------------------

        Clock.schedule_once(
            self.poll_start_task,
            2
        )

    # ========================================================
    # CONVERSATION READY
    # ========================================================

    def conversation_ready(
        self,
        conversation_id
    ):

        self.conversation_id = (
            conversation_id
        )

        self.start_task_id = None

        self.seen_event_ids.clear()

        self.event_cursor = None

        self.finished = False

        self.reply_received = False

        self.start_button.disabled = False

        self.send_button.disabled = False

        self.set_status(
            "READY"
        )

        self.add_message(
            "SYSTEM",
            "Conversation is ready."
        )

        if self.poll_event is not None:

            self.poll_event.cancel()

        self.poll_event = (
            Clock.schedule_interval(
                self.poll_conversation,
                10
            )
        )

        self.refresh_credits()

        # Immediately get existing events.

        self.poll_conversation(
            0
        )

    # ========================================================
    # SEND MESSAGE
    # ========================================================

    def send(
        self,
        *args
    ):

        if not self.conversation_id:

            self.add_message(
                "SYSTEM",
                "Start a conversation first."
            )

            return

        message = (
            self.message_input.text
            .strip()
        )

        if not message:
            return

        self.add_message(
            "You",
            message
        )

        self.message_input.text = ""

        self.finished = False

        self.reply_received = False

        if self.poll_event is None:

            self.poll_event = (
                Clock.schedule_interval(
                    self.poll_conversation,
                    10
                )
            )

        self.send_button.disabled = True

        self.set_status(
            "SENDING..."
        )

        threading.Thread(
            target=self._send_worker,
            args=(message,),
            daemon=True
        ).start()

    def _send_worker(
        self,
        message
    ):

        try:

            result = (
                self.api.send_message(
                    self.conversation_id,
                    message
                )
            )

            print(
                "\n--- SEND RESPONSE ---"
            )

            print(
                json.dumps(
                    result,
                    indent=2
                )
            )

            Clock.schedule_once(
                lambda dt:
                self.message_sent()
            )

        except Exception as error:

            error_text = str(error)

            Clock.schedule_once(
                lambda dt,
                error_text=error_text:
                self.api_error(
                    error_text
                )
            )

    def message_sent(
        self
    ):

        self.send_button.disabled = False

        self.set_status(
            "WORKING..."
        )

        # Poll immediately so the user
        # doesn't wait for the interval.
        self.poll_conversation(0)

    # ========================================================
    # POLL EVENTS
    # ========================================================

    def poll_conversation(
        self,
        dt
    ):

        if not self.conversation_id:
            return

        if self._poll_active:
            return

        self._poll_active = True

        threading.Thread(
            target=self._conversation_worker,
            daemon=True
        ).start()

    def _conversation_worker(
        self
    ):

        try:

            if self.finished:
                return

            events, cursor = (
                self.api.search_events(
                    self.conversation_id,
                    limit=100,
                    page_start=self.event_cursor,
                    max_pages=20
                )
            )

            if cursor is not None:
                self.event_cursor = cursor

            if not events:
                return

            Clock.schedule_once(
                lambda dt,
                events=events:
                self.process_conversation(
                    events
                )
            )

        except Exception as error:

            error_text = str(error)

            if "429" in error_text:
                return

            Clock.schedule_once(
                lambda dt,
                error_text=error_text:
                self.api_error(
                    error_text
                )
            )

        finally:

            self._poll_active = False

    # ========================================================
    # PROCESS CONVERSATION
    # ========================================================

    def process_conversation(
        self,
        events
    ):

        # ----------------------------------------------------
        # GET EVENT LIST
        # ----------------------------------------------------

        if isinstance(
            events,
            list
        ):

            event_list = events

        elif isinstance(
            events,
            dict
        ):

            event_list = (
                events.get(
                    "items"
                )
                or events.get(
                    "events"
                )
                or events.get(
                    "data"
                )
                or []
            )

        else:

            event_list = []

        if not isinstance(
            event_list,
            list
        ):

            return

        # ----------------------------------------------------
        # PROCESS ONLY NEW EVENTS
        # ----------------------------------------------------

        for event in event_list:

            if not isinstance(
                event,
                dict
            ):
                continue

            event_id = event.get(
                "id"
            )

            if (
                event_id
                and event_id
                in self.seen_event_ids
            ):

                continue

            if event_id:

                self.seen_event_ids.add(
                    event_id
                )

            if self.debug_enabled:

                preview = (
                    self.extract_text(
                        event
                    ) or ""
                )

                print(
                    "[EVENT]",
                    event.get("kind"),
                    "| source:",
                    event.get("source"),
                    "|",
                    preview[:80]
                )

            self.process_event(
                event
            )

    # ========================================================
    # EVENT PARSER
    # ========================================================

    def process_event(
        self,
        event
    ):

        kind = str(
            event.get(
                "kind",
                ""
            )
        )

        source = str(
            event.get(
                "source",
                ""
            )
        )

        # ----------------------------------------------------
        # STATE UPDATE
        # ----------------------------------------------------

        if kind == (
            "ConversationStateUpdateEvent"
        ):

            value = event.get(
                "value"
            )

            KNOWN_STATUSES = (
                "idle",
                "running",
                "working",
                "finished",
                "error",
                "cancelled",
                "paused",
                "ready",
                "stuck"
            )

            if isinstance(value, dict):

                status = value.get(
                    "execution_status"
                )

            elif (
                isinstance(value, str)
                and value.lower()
                in KNOWN_STATUSES
            ):

                status = value

            else:

                status = None

            if status:

                self.set_status(
                    str(status)
                )

                self.check_finished(
                    status
                )

            return

        # ----------------------------------------------------
        # ERROR EVENT
        # ----------------------------------------------------

        if "error" in kind.lower():

            text = (
                self.extract_text(
                    event
                )
            )

            if not text:

                text = json.dumps(
                    event,
                    indent=2
                )

            self.add_message(
                "OpenHands ERROR",
                text
            )

            return

        # ----------------------------------------------------
        # MESSAGE EVENT
        # ----------------------------------------------------

        if (
            kind == "MessageEvent"
            and source == "agent"
        ):

            text = (
                self.extract_text(
                    event.get("llm_message") or {}
                )
            )

            if text:

                self.reply_received = True

                self.send_button.disabled = False

                if self.stream_label is not None:

                    self.stream_buffer = []

                    self.stream_label.full_text = (
                        f"OpenHands\n\n{text}"
                    )

                    self.stream_label.text = (
                        self.stream_label
                        .full_text
                    )

                    self.stream_label = None

                    return

                self.add_message(
                    "OpenHands",
                    text
                )

        # ----------------------------------------------------
        # STREAMING EVENT
        # ----------------------------------------------------

        if (
            "delta" in kind.lower()
            and source == "agent"
        ):

            delta = (
                self.extract_text(
                    event
                )
            )

            if delta:

                self.stream_buffer.append(delta)

                if self.stream_label is None:

                    self.stream_label = (
                        ChatMessage(
                            "OpenHands",
                            ""
                        )
                    )

                    self.chat.add_widget(
                        self.stream_label
                    )

                self.stream_label.full_text = (
                    "OpenHands\n\n"
                    + "".join(
                        self.stream_buffer
                    )
                )

                self.stream_label.text = (
                    self.stream_label
                    .full_text
                )

    # ========================================================
    # FINISHED CHECK
    # ========================================================

    def check_finished(
        self,
        status
    ):

        status_lower = str(
            status
        ).lower()

        if status_lower not in (
            "finished",
            "error",
            "cancelled"
        ):
            return

        self.finished = True

        if self.poll_event is not None:

            self.poll_event.cancel()

            self.poll_event = None

        self.send_button.disabled = False

        if not self.reply_received:

            self.add_message(
                "SYSTEM",
                "OpenHands finished without a reply."
            )

        self.reply_received = False

    # ========================================================
    # TEXT EXTRACTION
    # ========================================================

    def extract_text(
        self,
        event
    ):

        # Direct text fields.

        for key in (
            "text",
            "delta",
            "message"
        ):

            value = event.get(
                key
            )

            if isinstance(
                value,
                str
            ):

                return value

        # Content.

        content = event.get(
            "content"
        )

        if isinstance(
            content,
            str
        ):

            return content

        if isinstance(
            content,
            list
        ):

            parts = []

            for item in content:

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                text = item.get(
                    "text"
                )

                if text:

                    parts.append(
                        str(text)
                    )

            if parts:

                return "\n".join(
                    parts
                )

        return None

    # ========================================================
    # CREDITS
    # ========================================================

    def refresh_credits(
        self
    ):

        if not self.api:
            return

        threading.Thread(
            target=self._credits_worker,
            daemon=True
        ).start()

    def _credits_worker(
        self
    ):

        try:

            result = (
                self.api.get_credits()
            )

            Clock.schedule_once(
                lambda dt,
                result=result:
                self.show_credits(
                    result
                )
            )

        except Exception as error:

            print(
                "Credits error:",
                error
            )

    def show_credits(
        self,
        result
    ):

        value = (
            self.find_credit_value(
                result
            )
        )

        if value is not None:

            self.credits_label.text = (
                f"Credits: {value}"
            )

        else:

            self.credits_label.text = (
                "Credits: unknown"
            )

    def find_credit_value(
        self,
        data
    ):

        if not isinstance(
            data,
            dict
        ):
            return None

        for key in (
            "credits",
            "remaining_credits",
            "available_credits",
            "balance",
            "remaining",
            "amount"
        ):

            if key in data:

                value = data[key]

                if isinstance(
                    value,
                    (dict, list)
                ):

                    return json.dumps(
                        value
                    )

                return value

        return None

    # ========================================================
    # GIT CHANGES
    # ========================================================

    def get_changes(
        self,
        *args
    ):

        if not self.conversation_id:

            self.add_message(
                "SYSTEM",
                "Start a conversation first."
            )

            return

        threading.Thread(
            target=self._changes_worker,
            daemon=True
        ).start()

    def _changes_worker(
        self
    ):

        try:

            result = (
                self.api.get_git_changes(
                    self.conversation_id
                )
            )

            text = json.dumps(
                result,
                indent=2
            )

            Clock.schedule_once(
                lambda dt,
                text=text:
                self.add_message(
                    "GIT CHANGES",
                    text
                )
            )

        except Exception as error:

            error_text = str(error)

            Clock.schedule_once(
                lambda dt,
                error_text=error_text:
                self.api_error(
                    error_text
                )
            )

    # ========================================================
    # GIT DIFF
    # ========================================================

    def get_diff(
        self,
        *args
    ):

        if not self.conversation_id:

            self.add_message(
                "SYSTEM",
                "Start a conversation first."
            )

            return

        threading.Thread(
            target=self._diff_worker,
            daemon=True
        ).start()

    def _diff_worker(
        self
    ):

        try:

            result = (
                self.api.get_git_diff(
                    self.conversation_id
                )
            )

            text = json.dumps(
                result,
                indent=2
            )

            Clock.schedule_once(
                lambda dt,
                text=text:
                self.add_message(
                    "GIT DIFF",
                    text
                )
            )

        except Exception as error:

            error_text = str(error)

            Clock.schedule_once(
                lambda dt,
                error_text=error_text:
                self.api_error(
                    error_text
                )
            )

    # ========================================================
    # UI
    # ========================================================

    def add_message(
        self,
        speaker,
        message
    ):

        widget = ChatMessage(
            speaker,
            str(message)
        )

        self.chat.add_widget(
            widget
        )

        Clock.schedule_once(
            lambda dt:
            self.scroll_bottom(),
            0.1
        )

    def scroll_bottom(
        self
    ):

        self.scroll.scroll_y = 0

    def set_status(
        self,
        status
    ):

        self.status_label.text = (
            f"Status: {status}"
        )

    def api_error(
        self,
        error
    ):

        self.start_button.disabled = False

        self.send_button.disabled = False

        self.set_status(
            "ERROR"
        )

        self.add_message(
            "API ERROR",
            error
        )

        print(
            "\n================ CLIENT ERROR ================\n"
        )

        print(
            error
        )

        print(
            "\n===============================================\n"
        )

    # ========================================================
    # SETTINGS
    # ========================================================

    def open_settings(
        self,
        *args
    ):

        self.app.screen_manager.current = (
            "settings"
        )


# ============================================================
# APP
# ============================================================

class OpenHandsClient(
    App
):

    def build(
        self
    ):

        from kivy.core.window import Window

        if Window is not None:
            Window.clearcolor = BACKGROUND

        self.screen_manager = (
            ScreenManager()
        )

        self.chat_screen = ChatScreen(
            self,
            name="chat"
        )

        self.settings_screen = (
            SettingsScreen(
                self,
                name="settings"
            )
        )

        self.screen_manager.add_widget(
            self.chat_screen
        )

        self.screen_manager.add_widget(
            self.settings_screen
        )

        return self.screen_manager


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    OpenHandsClient().run()