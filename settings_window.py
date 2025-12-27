import tkinter as tk
from tkinter import messagebox as mb


class SettingsWindow:
    def __init__(self, parent, settings_manager, apply_callback):
        self.settings = settings_manager
        self.apply_callback = apply_callback

        # Создаем окно настроек
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("400x600")
        self.window.resizable(False, False)

        # Переменные для хранения временных значений
        self.temp_values = {}
        self._setup_variables()

        # Создаем интерфейс
        self._create_widgets()

        # Загружаем текущие значения
        self._load_current_values()

        # Блокируем взаимодействие с родительским окном
        self.window.transient(parent)
        self.window.grab_set()

        self.window.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _setup_variables(self):
        """Настройка переменных для хранения временных значений"""
        # Таймерные значения
        self.timer_entries = []
        self.timer_vars = [tk.StringVar() for _ in range(4)]

        # Quick settings
        self.quick_settings_vars = {}
        quick_settings = self.settings.get("system.quick_settings", {})
        for key in quick_settings:
            self.quick_settings_vars[key] = tk.BooleanVar(value=quick_settings[key])

        # Тема
        self.theme_var = tk.StringVar()

        # Пользовательские цвета темы
        self.user_theme_vars = {
            "status_rest": tk.StringVar(value="#3BBF77"),
            "status_pause": tk.StringVar(value="#808080"),
            "status_focus": tk.StringVar(value="#3B77BC"),
            "background_top": tk.StringVar(value="#1E1E1E"),
            "background_bot": tk.StringVar(value="#2D2D2D"),
        }

    def _create_widgets(self):
        """Создание виджетов окна настроек"""
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canvas с прокруткой
        canvas = tk.Canvas(main_frame)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Раздел Timer Settings
        timer_frame = tk.LabelFrame(scrollable_frame, text="Timer Settings", padx=10, pady=10)
        timer_frame.pack(fill=tk.X, pady=(0, 10))

        labels = self.settings.get(
            "appearence.quick_settings_minutes_entries_labels",
            ["Focus:", "Short:", "Long:", "Cycles:"],
        )

        for i, label_text in enumerate(labels):
            frame = tk.Frame(timer_frame)
            frame.pack(fill=tk.X, pady=2)

            tk.Label(frame, text=label_text, width=10).pack(side=tk.LEFT)
            entry = tk.Entry(frame, textvariable=self.timer_vars[i], width=10)
            entry.pack(side=tk.RIGHT)
            self.timer_entries.append(entry)

        # Quick Settings
        quick_frame = tk.LabelFrame(scrollable_frame, text="Quick Settings", padx=10, pady=10)
        quick_frame.pack(fill=tk.X, pady=(0, 10))

        quick_labels = self.settings.get("appearence.quick_settings_buttons_labels", {})

        for key, var in self.quick_settings_vars.items():
            if key in ["minutes_entries", "next_previous_buttons"]:
                continue  # Эти настройки обрабатываются отдельно

            label_text = quick_labels.get(key, key.replace("_", " ").title())
            cb = tk.Checkbutton(quick_frame, text=label_text, variable=var)
            cb.pack(anchor=tk.W, pady=2)

        # Theme Settings
        theme_frame = tk.LabelFrame(scrollable_frame, text="Theme Settings", padx=10, pady=10)
        theme_frame.pack(fill=tk.X, pady=(0, 10))

        # Радиокнопки выбора темы
        themes = [("Light", "light"), ("Dark", "dark"), ("Custom", "user")]
        for text, value in themes:
            rb = tk.Radiobutton(
                theme_frame,
                text=text,
                variable=self.theme_var,
                value=value,
                command=self._on_theme_change,
            )
            rb.pack(anchor=tk.W)

        # Поля для пользовательской темы
        self.user_theme_frame = tk.Frame(theme_frame)

        color_labels = [
            ("Rest Status Color:", "status_rest"),
            ("Pause Status Color:", "status_pause"),
            ("Focus Status Color:", "status_focus"),
            ("Top Background:", "background_top"),
            ("Bottom Background:", "background_bot"),
        ]

        for label_text, key in color_labels:
            frame = tk.Frame(self.user_theme_frame)
            frame.pack(fill=tk.X, pady=2)

            tk.Label(frame, text=label_text, width=20).pack(side=tk.LEFT)
            entry = tk.Entry(frame, textvariable=self.user_theme_vars[key], width=10)
            entry.pack(side=tk.RIGHT)

        # Кнопки Apply и Cancel
        button_frame = tk.Frame(scrollable_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Button(button_frame, text="Cancel", command=self._on_cancel, width=10).pack(
            side=tk.RIGHT, padx=5
        )
        tk.Button(button_frame, text="Apply", command=self._on_apply, width=10).pack(
            side=tk.RIGHT, padx=5
        )

        # Упаковка canvas
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _load_current_values(self):
        """Загрузка текущих значений из настроек"""
        # Загружаем значения таймера
        timer_values = self.settings.get("timer.user", [])
        if timer_values:
            for i, value in enumerate(timer_values):
                if i < 4:
                    self.timer_vars[i].set(str(value))

        # Загружаем текущую тему
        current_theme = self.settings.get("appearence.themes.current_preset", "dark")
        self.theme_var.set(current_theme)

        # Загружаем цвета пользовательской темы
        user_theme = self.settings.get("appearence.themes.user", {})
        for key, var in self.user_theme_vars.items():
            if key in user_theme:
                var.set(user_theme[key])

        # Показываем/скрываем поля пользовательской темы
        self._on_theme_change()

    def _on_theme_change(self):
        """Обработка изменения темы"""
        if self.theme_var.get() == "user":
            self.user_theme_frame.pack(fill=tk.X, pady=(10, 0))
        else:
            self.user_theme_frame.pack_forget()

    def _on_apply(self):
        """Применение настроек"""
        try:
            # Сохраняем значения таймера
            timer_values = []
            for var in self.timer_vars:
                value = var.get().strip()
                if value:
                    timer_values.append(float(value))
                else:
                    timer_values.append(0.0)

            self.settings.set_val("timer.user", timer_values)

            # Сохраняем quick settings
            for key, var in self.quick_settings_vars.items():
                self.settings.set_val(f"system.quick_settings.{key}", var.get())

            # Сохраняем тему
            theme_name = self.theme_var.get()
            self.settings.set_val("appearence.themes.current_preset", theme_name)

            # Сохраняем пользовательскую тему
            if theme_name == "user":
                user_theme = {}
                for key, var in self.user_theme_vars.items():
                    user_theme[key] = var.get()
                self.settings.set_val("appearence.themes.user", user_theme)

            # Сохраняем в файл
            self.settings.save()

            # Вызываем callback для обновления главного окна
            self.apply_callback()

            # Закрываем окно
            self.window.destroy()

        except ValueError as e:
            mb.showerror("Error", f"Invalid value: {str(e)}")

    def _on_cancel(self):
        """Отмена изменений"""
        self.window.destroy()
