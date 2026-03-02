import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk


class SettingsWindow(tk.Toplevel):
    """Модальное окно для расширенных настроек приложения."""

    def __init__(self, parent, settings_manager, rebuild_callback):
        """
        Инициализация окна настроек.

        Args:
            parent: Родительское окно Tkinter.
            settings_manager: Экземпляр SettingsManager.
            rebuild_callback: Функция обратного вызова для обновления главного UI.
        """
        super().__init__(parent)
        self.settings = settings_manager
        self.rebuild_callback = rebuild_callback
        self.title("Settings")
        self.geometry("580x550")
        self.resizable(True, True)

        self.qs_vars = {}
        self.user_theme_vars = {}

        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=5)

        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=5)

        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=1)

        self.create_preset_frame(self.left_frame)
        self.create_quick_settings_frame(self.left_frame)
        self.create_audio_frame(self.right_frame)
        self.create_theme_frame(self.right_frame)

        btn_frame = tk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, pady=10)
        tk.Button(btn_frame, text="Save & Close", command=self.save_and_close, width=12).pack(
            side=tk.LEFT, padx=10
        )
        tk.Button(btn_frame, text="Cancel", command=self.destroy, width=12).pack(
            side=tk.LEFT, padx=10
        )

    def create_preset_frame(self, parent):
        """Секция настройки пресетов таймера."""
        frame = tk.LabelFrame(parent, text="Preset Settings", padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)

        info_label = tk.Label(
            frame,
            text="Select preset. 'User' can be customized below.",
            font=("Helvetica", 8),
            justify=tk.LEFT,
            anchor=tk.W,
        )
        info_label.pack(fill=tk.X, pady=(0, 5))

        preset_frame = tk.Frame(frame)
        preset_frame.pack(fill=tk.X, pady=5)

        tk.Label(preset_frame, text="Current: ", width=8, anchor=tk.W).pack(side=tk.LEFT)

        presets = ["small", "medium", "big", "user"]
        current_preset = self.settings.get("timer.current_preset", "medium")
        self.preset_combo = ttk.Combobox(preset_frame, values=presets, state="readonly", width=10)
        self.preset_combo.set(current_preset)
        self.preset_combo.pack(side=tk.LEFT, padx=5)

        user_frame = tk.LabelFrame(frame, text="User Preset Values", padx=5, pady=5)
        user_frame.pack(fill=tk.X, pady=5)

        labels = ["Focus", "Short", "Long", "Cycles"]
        self.user_entries = []

        current_user = self.settings.get("timer.user", [0.0, 0.0, 0.0, 0.0])
        if not any(current_user):
            current_user = [25, 5, 15, 4]

        for i, label in enumerate(labels):
            row = tk.Frame(user_frame)
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=label, width=8, anchor=tk.W, font=("Helvetica", 9)).pack(
                side=tk.LEFT
            )
            entry = tk.Entry(row, width=8)
            entry.insert(0, str(current_user[i]))
            entry.pack(side=tk.LEFT, padx=5)
            self.user_entries.append(entry)

    def create_audio_frame(self, parent):
        """Секция путей к аудиофайлам."""
        frame = tk.LabelFrame(parent, text="Audio Paths", padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)

        self.path_work = tk.Entry(frame, width=35)
        self.path_work.insert(0, self.settings.get("system.path_to_focus_track", "work.mp3"))
        self.path_work.grid(row=0, column=0, padx=2, pady=2, sticky=tk.EW)
        tk.Button(
            frame, text="...", command=lambda: self.browse_file(self.path_work), width=3
        ).grid(row=0, column=1, pady=2)

        self.path_rest = tk.Entry(frame, width=35)
        self.path_rest.insert(0, self.settings.get("system.path_to_rest_track", "rest.mp3"))
        self.path_rest.grid(row=1, column=0, padx=2, pady=2, sticky=tk.EW)
        tk.Button(
            frame, text="...", command=lambda: self.browse_file(self.path_rest), width=3
        ).grid(row=1, column=1, pady=2)

        frame.columnconfigure(0, weight=1)

    def create_theme_frame(self, parent):
        """
        Секция выбора и настройки темы.
        Изменения:
        1. Порядок цветов соответствует config.py.
        2. Добавлены дружелюбные названия для интерфейса.
        """
        frame = tk.LabelFrame(parent, text="Theme", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=5)

        theme_frame = tk.Frame(frame)
        theme_frame.pack(fill=tk.X, pady=5)

        tk.Label(theme_frame, text="Theme: ", width=8, anchor=tk.W).pack(side=tk.LEFT)

        themes = ["light", "dark", "user"]
        current_theme = self.settings.get("appearence.themes.current_preset", "dark")
        self.theme_combo = ttk.Combobox(theme_frame, values=themes, state="readonly", width=10)
        self.theme_combo.set(current_theme)
        self.theme_combo.pack(side=tk.LEFT, padx=5)

        self.theme_combo.bind("<<ComboboxSelected>>", self._on_theme_change)

        self.user_colors_frame = tk.LabelFrame(frame, text="User Colors", padx=5, pady=5)

        if current_theme == "user":
            self.user_colors_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        else:
            self.user_colors_frame.pack_forget()

        current_user_theme = self.settings.get("appearence.themes.user", {})

        # Исправление #1 и #2: Порядок как в config.py + дружелюбные названия
        color_labels = [
            ("status_rest", "Отдых (текст)"),
            ("status_pause", "Пауза (текст)"),
            ("status_focus", "Фокус (текст)"),
            ("background_top", "Фон верхний"),
            ("background_bot", "Фон нижний"),
            ("button_bg", "Кнопки (фон)"),
            ("button_fg", "Кнопки (текст)"),
            ("button_pressed_bg", "Кнопки нажатые (фон)"),
            ("button_pressed_fg", "Кнопки нажатые (текст)"),
        ]

        self.user_theme_vars = {}
        for key, label in color_labels:
            row = tk.Frame(self.user_colors_frame)
            row.pack(fill=tk.X, pady=1)

            tk.Label(row, text=label, width=20, anchor=tk.W, font=("Helvetica", 9)).pack(
                side=tk.LEFT
            )

            default_colors = {
                "status_rest": "#3BBF77",
                "status_pause": "#808080",
                "status_focus": "#3B77BC",
                "background_top": "#1E1E1E",
                "background_bot": "#2D2D2D",
                "button_bg": "#3D3D3D",
                "button_fg": "#FFFFFF",
                "button_pressed_bg": "#3B77BC",
                "button_pressed_fg": "#FFFFFF",
            }
            current_color = current_user_theme.get(key, default_colors[key])

            entry = tk.Entry(row, width=10)
            entry.insert(0, current_color)
            entry.pack(side=tk.LEFT, padx=5)
            self.user_theme_vars[key] = entry

            btn = tk.Button(
                row, text="🎨", command=lambda k=key, e=entry: self._pick_color(e), width=3
            )
            btn.pack(side=tk.LEFT)

    def _on_theme_change(self, event):
        """Показывает/скрывает редактор цветов user темы."""
        selected = self.theme_combo.get()
        if selected == "user":
            self.user_colors_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        else:
            self.user_colors_frame.pack_forget()

    def _pick_color(self, entry):
        """Открывает выбор цвета."""
        current = entry.get()
        color = colorchooser.askcolor(color=current)[1]
        if color:
            entry.delete(0, tk.END)
            entry.insert(0, color)

    def create_quick_settings_frame(self, parent):
        """Секция управления видимостью и состоянием быстрых настроек."""
        frame = tk.LabelFrame(parent, text="Quick Settings", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=5)

        qs_map = {
            "always_on_top": "system.always_on_top_enabled",
            "pause_on_end": "system.pause_on_end_enabled",
            "sound_player": "system.sound_player_enabled",
            "media_api": "system.media_api_enabled",
        }

        for vis_key, state_key in qs_map.items():
            vis_val = self.settings.get(f"system.quick_settings.{vis_key}", False)
            vis_var = tk.BooleanVar(value=vis_val)

            state_val = self.settings.get(state_key, False)
            state_var = tk.BooleanVar(value=state_val)

            row_frame = tk.Frame(frame)
            row_frame.pack(fill=tk.X, pady=1)

            tk.Label(
                row_frame,
                text=vis_key.replace("_", " ").title(),
                width=14,
                anchor=tk.W,
                font=("Helvetica", 9),
            ).pack(side=tk.LEFT)

            tk.Checkbutton(row_frame, text="Show", variable=vis_var, indicatoron=True).pack(
                side=tk.LEFT
            )
            tk.Checkbutton(row_frame, text="On", variable=state_var, indicatoron=True).pack(
                side=tk.LEFT
            )

            self.qs_vars[vis_key] = {
                "vis": vis_var,
                "state": state_var,
                "state_key": state_key,
                "vis_key": vis_key,
            }

    def browse_file(self, entry_widget):
        """Открывает диалог выбора файла."""
        filename = filedialog.askopenfilename(
            filetypes=[("MP3 Files", "*.mp3"), ("All Files", "*.*")]
        )
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)

    def save_and_close(self):
        """Сохраняет все изменения и закрывает окно."""
        selected_preset = self.preset_combo.get()
        self.settings.set_val("timer.current_preset", selected_preset)

        try:
            user_values = [float(e.get()) for e in self.user_entries]
            self.settings.set_val("timer.user", user_values)
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for User Preset")
            return

        selected_theme = self.theme_combo.get()
        self.settings.set_val("appearence.themes.current_preset", selected_theme)

        if selected_theme == "user":
            user_theme_colors = {}
            for key, entry in self.user_theme_vars.items():
                user_theme_colors[key] = entry.get()
            self.settings.set_val("appearence.themes.user", user_theme_colors)

        self.settings.set_val("system.path_to_focus_track", self.path_work.get())
        self.settings.set_val("system.path_to_rest_track", self.path_rest.get())

        for key, data in self.qs_vars.items():
            self.settings.set_val(f"system.quick_settings.{data['vis_key']}", data["vis"].get())
            self.settings.set_val(data["state_key"], data["state"].get())

        self.settings.save()
        self.rebuild_callback()
        self.destroy()
