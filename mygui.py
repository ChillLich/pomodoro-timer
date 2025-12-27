import tkinter as tk
from tkinter import messagebox as mb

from config import SettingsManager
from settings_window import SettingsWindow
from timer import Timer

"""
БЫЛО В TIMER.RESET()
# ЛОГИЧЕСКИ ЭТО ЗДЕСЬ НУЖНО. В ТАЙМЕРЕ АВТОМАТИЧЕСКИ ПОДТЯНУТСЯ
# ЗНАЧЕНИЯ ИЗ settings КОЛЛБЭКАМИ
        # Если переданы значения из GUI - сохраняем их в user пресет
        if entry_values:
            try:
                float_values = [float(v) for v in entry_values]
                # Сохраняем в user пресет и переключаемся на него
                self.settings.set_timer_preset("user", float_values)
                # Значения уже загрузятся через callback _on_settings_changed
            except ValueError:
                return False
"""


class MyGUI:
    def __init__(self):
        # Инициализация менеджера настроек
        self.sm = SettingsManager()
        self.sm.load()

        # Создание таймера
        self.timer = Timer(self.sm)
        self.timer.set_gui_callbacks(self._update_gui, self._handle_tick)

        # Создание основного окна
        self.main_window = tk.Tk()
        self.main_window.title("Timer by @CHILLLICH")

        # Получение настроек GUI
        self.load_gui_settings()

        # Применяем настройки окна УБРАТЬ ЭТО СКОРЕЕ ВСЕГО
        self._apply_window_settings()

        # Инициализация компонентов
        self._init_info_display()
        self._init_quick_settings()
        self._init_buttons()

        self.apply_gui_settings()

        # Обновление начального статуса
        self._update_gui()

        # Регистрация callback для обновления тем
        self.sm.add_callback(self._on_settings_changed)

        # Запуск главного цикла
        tk.mainloop()

    def apply_gui_settings(self): ...

    def load_gui_settings(self):
        """Загрузка настроек для GUI из SettingsManager, НЕ применяет их."""
        window = self.sm.get("window")
        self.WIDTH = window.get("width")
        self.HEIGHT = window.get("height")
        self.PADXY = window.get("padxy")
        self.PADXY_S = window.get("padxy_s")
        self.PADXY_SS = window.get("padxy_ss")
        self.ENTRY_WIDTH = window.get("entry_width")

        self.STATUS_TITLE: dict[str, str] = self.sm.get("appearence.status_title")
        self.ENTRIES_LABELS_LIST: list[str] = self.sm.get(
            "appearence.quick_settings_minutes_entries_labels",
        )
        self.BUTTONS_LABELS: dict[str, str | list[str]] = self.sm.get(
            "appearence.quick_settings_buttons_labels"
        )

        self._load_theme_colors()
        self._load_fonts()

    def _load_theme_colors(self):
        """Загрузка цветов темы"""
        theme_name = self.sm.get("appearence.themes.current_preset", "dark")
        theme = self.sm.get(f"appearence.themes.{theme_name}")
        self.COLOR_REST = theme.get("status_rest")
        self.COLOR_PAUSE = theme.get("status_pause")
        self.COLOR_WORK = theme.get("status_focus")
        self.BACKGROUND_TOP = theme.get("background_top")
        self.BACKGROUND_BOT = theme.get("background_bot")

    def _load_fonts(self):
        """Загрузка шрифтов"""
        fonts = self.sm.get("appearence.fonts")
        self.FONT_STATUS = fonts.get("status")
        self.FONT_MINS = fonts.get("minutes")
        self.FONT_BUTTONS = fonts.get("buttons")
        self.FONT_LABELS = fonts.get("labels")

    # ПЕРЕПИСАТЬ ФУНКЦИЮ НА ПРИМЕНЕНИЕ НАСТРОЕН ОКНА
    def _apply_window_settings(self):
        """Применение настроек окна"""
        self.main_window.geometry(f"{self.WIDTH}x{self.HEIGHT}")

        self._apply_always_on_top()

        # Устанавливаем цвета фона
        colors = self.sm.get_current_theme_colors()
        self.main_window.configure(bg=colors["background_top"])

    def _apply_always_on_top(self):
        """Применяет настройку Always on top."""
        if self.sm.get("system.always_on_top_enabled"):
            self.main_window.attributes("-topmost", True)
        else:
            self.main_window.attributes("-topmost", False)

    def _on_settings_changed(self, key: str, value):
        """Обработка изменений настроек"""
        if key.startswith("appearence.themes") or key.startswith("appearence.fonts"):

            # ТУТ УЛУЧШИТЬ, ВЫЗЫВАТЬ load_gui_settings и apply_gui_settings
            # Обновляем цвета и шрифты
            self._load_theme_colors()
            self._load_fonts()

            # Применяем изменения к GUI
            self._apply_theme_to_widgets()
            self._apply_fonts_to_widgets()

        elif key == "system.always_on_top_enabled":
            self._apply_always_on_top()
            # self.main_window.attributes("-topmost", value)

        elif key.startswith("system.quick_settings"):
            # Обновляем видимость quick settings
            self._update_quick_settings_visibility()

    def _apply_theme_to_widgets(self):
        """Применение темы ко всем виджетам"""
        # Обновляем цвета фона окна
        self.main_window.configure(bg=self.BACKGROUND_TOP)

        # Обновляем фреймы
        if hasattr(self, "frame_info_status"):
            self.frame_info_status.configure(bg=self.BACKGROUND_TOP)
            self.frame_info_minutes.configure(bg=self.BACKGROUND_TOP)

        if hasattr(self, "frame_set_n_info"):
            self.frame_set_n_info.configure(bg=self.BACKGROUND_BOT)

        if hasattr(self, "frame_butt"):
            self.frame_butt.configure(bg=self.BACKGROUND_BOT)

        # Обновляем метки
        if hasattr(self, "output_status_label"):
            self.output_status_label.configure(bg=self.BACKGROUND_TOP)

        if hasattr(self, "label_mins_output_label"):
            self.label_mins_output_label.configure(bg=self.BACKGROUND_TOP)

        # Обновляем цвет статуса (используется в _update_gui)
        self._update_gui()

    def _apply_fonts_to_widgets(self):
        """Применение шрифтов ко всем виджетам"""
        if hasattr(self, "output_status_label"):
            self.output_status_label.configure(font=self.FONT_STATUS)

        if hasattr(self, "label_mins_output_label"):
            self.label_mins_output_label.configure(font=self.FONT_MINS)

        # Обновляем шрифты кнопок
        if hasattr(self, "buttons"):
            for button in self.buttons:
                button.configure(font=self.FONT_BUTTONS)

        # Обновляем шрифты меток
        if hasattr(self, "label_settings"):
            for label in self.label_settings:
                label.configure(font=self.FONT_LABELS)

        if hasattr(self, "label_settings_description"):
            self.label_settings_description.configure(font=self.FONT_LABELS)

    def _init_info_display(self):
        """Инициализация информационных виджетов"""
        # Фрейм для статуса
        self.frame_info_status = tk.Frame(self.main_window, bg=self.BACKGROUND_TOP)
        self.frame_info_status.pack(padx=self.PADXY, pady=self.PADXY_SS, fill=tk.X)

        self.output_status = tk.StringVar()
        self.output_status_label = tk.Label(
            self.frame_info_status,
            textvariable=self.output_status,
            font=self.FONT_STATUS,
            bg=self.BACKGROUND_TOP,
            fg="white",  # Белый текст на темном фоне
        )
        self.output_status_label.pack(side="top", padx=0, pady=0)

        # Фрейм для минут
        self.frame_info_minutes = tk.Frame(self.main_window, bg=self.BACKGROUND_TOP)
        self.frame_info_minutes.pack(padx=self.PADXY, pady=self.PADXY_SS, fill=tk.X)

        self.mins_output = tk.StringVar()
        self.label_mins_output_label = tk.Label(
            self.frame_info_minutes,
            textvariable=self.mins_output,
            font=self.FONT_MINS,
            bg=self.BACKGROUND_TOP,
            fg="white",
        )
        self.label_mins_output_label.pack(side="top")

    def _init_quick_settings(self):
        """Инициализация быстрых настроек (если включены)"""
        # Проверяем, нужно ли показывать minutes entries
        show_entries = self.sm.get("system.quick_settings.minutes_entries", True)

        if show_entries:
            self.frame_set_n_info = tk.Frame(self.main_window, bg=self.BACKGROUND_BOT)
            self.frame_set_n_info.pack(padx=self.PADXY, pady=self.PADXY, fill=tk.X)

            self.label_settings_description = tk.Label(
                self.frame_set_n_info,
                text="Timer Settings:",
                font=self.FONT_LABELS,
                bg=self.BACKGROUND_BOT,
                fg="white",
            )
            self.label_settings_description.pack(side="top", padx=self.PADXY, pady=(0, 5))

            self.frame_settings_labels = []
            self.label_settings = []
            self.entry_settings = []

            timer_values = self.timer.get_timer_values()

            for i in range(4):
                frame = tk.Frame(self.frame_set_n_info, bg=self.BACKGROUND_BOT)
                frame.pack(side="left", padx=self.PADXY, pady=self.PADXY, expand=True, fill=tk.X)
                self.frame_settings_labels.append(frame)

                label = tk.Label(
                    frame,
                    text=self.ENTRIES_LABELS_LIST[i],
                    font=self.FONT_LABELS,
                    bg=self.BACKGROUND_BOT,
                    fg="white",
                )
                label.pack(padx=self.PADXY, side=tk.LEFT)
                self.label_settings.append(label)

                entry = tk.Entry(frame, width=self.ENTRY_WIDTH, justify=tk.RIGHT)
                entry.insert(0, str(timer_values[i]))
                entry.pack(padx=self.PADXY, side=tk.RIGHT)
                self.entry_settings.append(entry)

    def _init_buttons(self):
        """Инициализация кнопок"""
        self.frame_butt = tk.Frame(self.main_window, bg=self.BACKGROUND_BOT)
        self.frame_butt.pack(padx=self.PADXY, pady=(0, self.PADXY), fill=tk.X)

        # Создание кнопок из настроек
        button_configs = [
            ("pause_on_end", "Pause on End", self._toggle_pause_on_end),
            ("media_api", "Media", self._toggle_media_api),
            ("reset_timer", "↺ Reset", self._reset_timer),
            ("sound_player", "♫ Sound", self._toggle_sound),
            ("settings", "⚙", self._open_settings),
            ("exit", "Exit", self._exit_app),
        ]

        self.buttons = []
        for key, default_text, command in button_configs:
            # Проверяем, нужно ли показывать эту кнопку
            show_button = self.sm.get(f"system.quick_settings.{key}", True)

            if show_button or key in [
                "settings",
                "exit",
            ]:  # Кнопки настроек и выхода всегда показываем
                text = self.BUTTONS_LABELS.get(key, default_text)
                btn = tk.Button(
                    self.frame_butt,
                    text=text,
                    command=command,
                    font=self.FONT_BUTTONS,
                    bg=self.BACKGROUND_BOT,
                    fg="white",
                    relief=tk.FLAT,
                )
                btn.pack(side="left", padx=self.PADXY_S, pady=self.PADXY_S, expand=True, fill=tk.X)
                self.buttons.append(btn)

                # Устанавливаем начальное состояние кнопок
                if key == "pause_on_end":
                    btn.config(
                        relief=(
                            tk.SUNKEN
                            if self.sm.get("system.pause_on_end_enabled", False)
                            else tk.RAISED
                        )
                    )
                elif key == "media_api":
                    btn.config(
                        relief=(
                            tk.SUNKEN
                            if self.sm.get("system.media_api_enabled", True)
                            else tk.RAISED
                        )
                    )
                elif key == "sound_player":
                    btn.config(
                        relief=(
                            tk.SUNKEN
                            if self.sm.get("system.sound_player_enabled", False)
                            else tk.RAISED
                        )
                    )

    def _update_quick_settings_visibility(self):
        """Обновление видимости quick settings"""
        # Этот метод будет вызываться при изменении quick settings
        # Для простоты перезагрузим весь GUI
        # В реальном приложении можно обновлять только измененные виджеты

        # Удаляем старые виджеты
        if hasattr(self, "frame_set_n_info"):
            self.frame_set_n_info.destroy()

        # Переинициализируем quick settings
        self._init_quick_settings()

        # Обновляем кнопки
        if hasattr(self, "frame_butt"):
            self.frame_butt.destroy()
        self._init_buttons()

    def _bind_play_pause_to_frames(self):
        """Привязка обработки кликов к фреймам"""
        tag = "frames_for_info"

        def add_tag_to_children(widget):
            widget.bindtags((tag,) + widget.bindtags())
            for child in widget.winfo_children():
                add_tag_to_children(child)

        for frame in [self.frame_info_minutes, self.frame_info_status]:
            add_tag_to_children(frame)
            frame.bind_class(tag, "<Button-1>", self._handle_click)

    def _handle_click(self, event):
        """Обработка клика по фреймам"""
        if getattr(self, "_handling_click", False):
            return

        self._handling_click = True
        try:
            status_info = self.timer.get_status_info()
            if status_info["status_type"] == "pause":
                self.timer.start()
            else:
                self.timer.pause()
        finally:
            self._handling_click = False

    # DONE не трогать, должно работать
    def _handle_tick(self, action, arg=None):
        """Обработка тиков таймера"""
        if action == "schedule":
            return self.main_window.after(arg, self.timer.count_tick)
        elif action == "cancel" and arg:
            self.main_window.after_cancel(arg)
        return None

    def _update_gui(self):
        """Обновление GUI на основе состояния таймера"""
        status_info = self.timer.get_status_info()

        # Обновление времени
        self.mins_output.set(status_info["minutes"])

        # Обновление статуса и цвета
        status_type = status_info["status_type"]
        self.output_status.set(self.STATUS_TITLE.get(status_type, status_type.upper()))

        color_map = {"pause": self.COLOR_PAUSE, "focus": self.COLOR_WORK, "rest": self.COLOR_REST}

        color = color_map.get(status_type, self.COLOR_PAUSE)

        # Обновляем цвет фона виджетов статуса
        self.output_status_label.configure(bg=color)
        self.label_mins_output_label.configure(bg=color)

        # Обновляем цвет фреймов
        self.frame_info_status.configure(bg=color)
        self.frame_info_minutes.configure(bg=color)

    # Обработчики кнопок
    def _toggle_sound(self):
        new_state = self.sm.toggle_setting("system.sound_player_enabled")
        # Находим кнопку sound_player
        for i, btn in enumerate(self.buttons):
            if "♫" in btn.cget("text"):
                btn.config(relief=tk.SUNKEN if new_state else tk.RAISED)
                break

    def _toggle_media_api(self):
        new_state = self.sm.toggle_setting("system.media_api_enabled")
        # Находим кнопку media_api
        for i, btn in enumerate(self.buttons):
            if "Media" in btn.cget("text"):
                btn.config(relief=tk.SUNKEN if new_state else tk.RAISED)
                break

    def _toggle_pause_on_end(self):
        new_state = self.sm.toggle_setting("system.pause_on_end_enabled")
        # Находим кнопку pause_on_end
        for i, btn in enumerate(self.buttons):
            if "Pause" in btn.cget("text"):
                btn.config(relief=tk.SUNKEN if new_state else tk.RAISED)
                break

    def _reset_timer(self):
        """Сброс таймера"""
        entry_values = [entry.get() for entry in self.entry_settings]

        if not self.timer.reset(entry_values):
            mb.showerror("Error", "You must use float values in input fields!")

    def _open_settings(self):
        """Открытие окна настроек"""
        SettingsWindow(self.main_window, self.sm, self._on_settings_applied)

    def _on_settings_applied(self):
        """Callback после применения настроек"""
        # Обновляем GUI после применения настроек
        self._update_gui()
        self._apply_theme_to_widgets()

    def _exit_app(self):
        """Выход из приложения"""
        # self.timer._cancel_and_stop()
        self.main_window.destroy()
