import tkinter as tk
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
        self.geometry("640x550")
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
        """
        frame = tk.LabelFrame(parent, text="Theme", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=5)

        theme_frame = tk.Frame(frame)
        theme_frame.pack(fill=tk.X, pady=5)

        tk.Label(theme_frame, text="Theme: ", width=8, anchor=tk.W).pack(side=tk.LEFT)

        themes = self.settings.get_available_themes()
        current_theme = self.settings.get("appearence.themes.current_preset", "dark")
        self.theme_combo = ttk.Combobox(theme_frame, values=themes, state="readonly", width=10)
        self.theme_combo.set(current_theme)
        self.theme_combo.pack(side=tk.LEFT, padx=5)

        self.theme_combo.bind("<<ComboboxSelected>>", self._on_theme_selected)

        add_btn = tk.Button(theme_frame, text="+ Add Theme", command=self._add_new_theme, width=10)
        add_btn.pack(side=tk.LEFT, padx=5)

        delete_btn = tk.Button(
            theme_frame, text="🗑 Delete", command=self._delete_current_theme, width=8
        )
        delete_btn.pack(side=tk.LEFT, padx=2)

        self.user_colors_frame = tk.LabelFrame(frame, text="User Colors", padx=5, pady=5)

        self.user_colors_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        color_labels = [
            ("status_rest", "Rest (text)"),
            ("status_pause", "Pause (text)"),
            ("status_focus", "Focus (text)"),
            ("background_top", "Top BG"),
            ("background_bot", "Bottom BG"),
            ("button_bg", "Buttons (BG)"),
            ("button_fg", "Buttons (text)"),
            ("button_pressed_bg", "Pressed buttons (BG)"),
            ("button_pressed_fg", "Pressed buttons (text)"),
        ]

        self.user_theme_vars = {}
        for key, label in color_labels:
            row = tk.Frame(self.user_colors_frame)
            row.pack(fill=tk.X, pady=1)

            tk.Label(row, text=label, width=20, anchor=tk.W, font=("Helvetica", 9)).pack(
                side=tk.LEFT
            )

            entry = tk.Entry(row, width=10)
            entry.pack(side=tk.LEFT, padx=5)
            self.user_theme_vars[key] = entry

            btn = tk.Button(
                row, text="🎨", command=lambda k=key, e=entry: self._pick_color(e), width=3
            )
            btn.pack(side=tk.LEFT)

        self._load_theme_colors_into_ui(current_theme)

    def _load_theme_colors_into_ui(self, theme_name):
        """Загружает цвета выбранной темы в поля ввода."""
        current_theme_data = self.settings.get(f"appearence.themes.{theme_name}", {})

        # Если тема не найдена в настройках (например, только что создана в памяти но не сохранена),
        # пробуем получить текущие активные цвета
        if not current_theme_data:
            current_theme_data = self.settings.get_current_theme_colors()

        default_colors = self.settings.get("appearence.themes.dark", {})

        for key, entry in self.user_theme_vars.items():
            current_color = current_theme_data.get(key, default_colors.get(key, "#000000"))
            entry.delete(0, tk.END)
            entry.insert(0, current_color)

    def _on_theme_selected(self, event=None):
        """Обработчик смены темы в Combobox."""
        selected_theme = self.theme_combo.get()
        self._load_theme_colors_into_ui(selected_theme)

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
            user_values = []
            for i, e in enumerate(self.user_entries):
                val = float(e.get())
                if i == 3:  # Cycles - индекс 3
                    if val < 1:
                        raise ValueError("Cycles must be at least 1")
                    user_values.append(int(val))
                else:
                    user_values.append(val)

            self.settings.set_val("timer.user", user_values)
        except ValueError as e:
            messagebox.showerror("Error", f"Please enter valid numbers for User Preset\n{e}")
            return

        selected_theme = self.theme_combo.get()
        self.settings.set_val("appearence.themes.current_preset", selected_theme)

        theme_colors = {}
        for key, entry in self.user_theme_vars.items():
            theme_colors[key] = entry.get()

        self.settings.add_theme(selected_theme, theme_colors)

        self.settings.set_val("system.path_to_focus_track", self.path_work.get())
        self.settings.set_val("system.path_to_rest_track", self.path_rest.get())

        for key, data in self.qs_vars.items():
            self.settings.set_val(f"system.quick_settings.{data['vis_key']}", data["vis"].get())
            self.settings.set_val(data["state_key"], data["state"].get())

        self.settings.save()
        self.rebuild_callback()
        self.destroy()

    def _add_new_theme(self):
        """Открывает диалог для создания новой темы."""
        dialog = tk.Toplevel(self)
        dialog.title("Add New Theme")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text="Theme Name:", font=("Helvetica", 10)).pack(pady=10)

        name_entry = tk.Entry(dialog, width=30)
        name_entry.pack(pady=5)
        name_entry.focus()

        def create_theme():
            theme_name = name_entry.get().strip().lower().replace(" ", "_")

            if not theme_name:
                messagebox.showwarning("Warning", "Theme name cannot be empty")
                return

            if theme_name in self.settings.get_available_themes():
                messagebox.showwarning("Warning", f"Theme '{theme_name}' already exists")
                return

            current_colors = self.settings.get_current_theme_colors()

            self.settings.add_theme(theme_name, current_colors)

            themes = self.settings.get_available_themes()
            self.theme_combo.config(values=themes)
            self.theme_combo.set(theme_name)

            self._load_user_theme_colors(theme_name)

            dialog.destroy()
            messagebox.showinfo("Success", f"Theme '{theme_name}' created!")

        tk.Button(dialog, text="Create", command=create_theme).pack(pady=10)

    def _delete_current_theme(self):
        """Удаляет текущую выбранную тему."""
        current_theme = self.theme_combo.get()

        if current_theme in ["light", "dark"]:
            messagebox.showwarning("Warning", "Cannot delete built-in themes (light/dark)")
            return

        confirm = messagebox.askyesno(
            "Confirm Delete", f"Are you sure you want to delete theme '{current_theme}'?"
        )

        if confirm:
            if self.settings.remove_theme(current_theme):
                themes = self.settings.get_available_themes()
                self.theme_combo.config(values=themes)
                self.theme_combo.set(themes[0])  # Выбираем первую доступную
                messagebox.showinfo("Success", f"Theme '{current_theme}' deleted!")
            else:
                messagebox.showerror("Error", "Cannot delete this theme")

    def _load_user_theme_colors(self, theme_name: str):
        """Загружает цвета выбранной темы в поля ввода."""
        current_user_theme = self.settings.get(f"appearence.themes.{theme_name}", {})

        default_colors = self.settings.get("appearence.themes.dark", {})

        for key, entry in self.user_theme_vars.items():
            current_color = current_user_theme.get(key, default_colors[key])
            entry.delete(0, tk.END)
            entry.insert(0, current_color)
