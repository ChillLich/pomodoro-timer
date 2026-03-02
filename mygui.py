import tkinter as tk
from tkinter import messagebox, ttk

from config import SettingsManager
from settings_window import SettingsWindow
from TIMER import Timer


class MyGUI:
    def __init__(self):
        self.settings = SettingsManager()
        self.settings.load()
        self.timer = Timer(self.settings)

        self.root = tk.Tk()
        self.root.title("Pomodoro Timer")

        # ✅ Кэшируем лейблы из конфига один раз
        self.button_labels = self.settings.get(
            "appearence.quick_settings_buttons_labels",
            {
                "always_on_top": "Always on Top",
                "pause_on_end": "Pause on End",
                "sound_player": "♫ Sound",
                "media_api": "Media",
                "reset_timer": "↺ Reset",
                "next_previous_buttons": ["<<", ">>"],
                "settings": "⚙",
                "exit": "Exit",
            },
        )

        self._apply_window_geometry()

        self.settings.add_callback(self._on_settings_changed)

        self.timer.set_gui_callbacks(
            update_callback=self.update_timer_display,
            tick_callback=self.schedule_tick,
        )

        # ✅ Создаём UI один раз, потом только обновляем
        self._init_ui()

        if self.timer.process_status not in (3, 4):
            self.timer.start()

        self.root.mainloop()

    def _apply_window_geometry(self):
        w = self.settings.get("window.width", 336)
        h = self.settings.get("window.height", 255)
        self.root.geometry(f"{w}x{h}")
        self.root.minsize(350, 280)

    def _on_settings_changed(self, key: str, value):
        """
        ✅ Оптимизированный callback - обновляем только нужные части UI
        """
        if "appearence.themes" in key or "system.quick_settings" in key:
            # ✅ Debouncing - избегаем множественных перерисовок
            if hasattr(self, "_rebuild_job") and self._rebuild_job:
                self.root.after_cancel(self._rebuild_job)
            self._rebuild_job = self.root.after(150, self._init_ui)
        elif key.startswith("window."):
            self.root.after(100, self._apply_window_geometry)
        elif key.startswith("timer."):
            self.root.after(100, self.update_timer_display)

    def schedule_tick(self, action, delay=None):
        if action == "cancel":
            if hasattr(self, "_tick_job") and self._tick_job:
                self.root.after_cancel(self._tick_job)
                self._tick_job = None
            return None
        elif action == "schedule":
            self._tick_job = self.root.after(delay, self.timer.count_tick)
            return self._tick_job
        return None

    def _init_ui(self):
        """
        ✅ Создаёт UI один раз при инициализации или полной пересборке
        """
        # Очищаем только если это не первый вызов
        if hasattr(self, "_ui_initialized") and self._ui_initialized:
            for widget in self.root.winfo_children():
                widget.destroy()

        self._ui_initialized = True

        colors = self.settings.get_current_theme_colors()
        fonts = self.settings.get_current_fonts()

        # ✅ ИСПРАВЛЕНИЕ #5: Один фрейм для верхней части (без вложенности)
        self.top_frame = tk.Frame(self.root, bg=colors["background_top"])
        self.top_frame.pack(fill=tk.X, side=tk.TOP)

        # Статус и таймер
        self._create_status_section(self.top_frame, colors, fonts)

        # ✅ Нижняя часть
        self.bot_frame = tk.Frame(self.root, bg=colors["background_bot"])
        self.bot_frame.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM)

        # ✅ ИСПРАВЛЕНИЕ #3: Grid для правильного якорения кнопок
        self._create_navigation_section(self.bot_frame, colors, fonts)

        # Быстрые настройки
        self._create_quick_settings_section(self.bot_frame, colors, fonts)

    def _create_status_section(self, parent, colors, fonts):
        """
        ✅ Создаёт секцию статуса (исправляет проблему #5)
        """
        # ✅ Один контейнер вместо вложенных фреймов
        status_container = tk.Frame(parent, bg=colors["background_top"], cursor="hand2")
        status_container.pack(anchor=tk.CENTER, pady=20)
        status_container.bind("<Button-1>", lambda e: self.toggle_start_pause())

        status_info = self.timer.get_status_info()
        status_text = self.settings.get(
            f"appearence.status_title.{status_info['status_type']}", "TIMER"
        )
        status_color = colors[f"status_{status_info['status_type']}"]

        # Статус
        self.lbl_status = tk.Label(
            status_container,
            text=status_text,
            font=fonts["status"],
            fg=status_color,
            bg=colors["background_top"],
            cursor="hand2",
        )
        self.lbl_status.pack(pady=(0, 5))
        self.lbl_status.bind("<Button-1>", lambda e: self.toggle_start_pause())

        # Таймер
        self.lbl_timer = tk.Label(
            status_container,
            text=status_info["minutes"],
            font=fonts["minutes"],
            fg=status_color,
            bg=colors["background_top"],
            cursor="hand2",
        )
        self.lbl_timer.pack(pady=(0, 5))
        self.lbl_timer.bind("<Button-1>", lambda e: self.toggle_start_pause())

        # Циклы
        display_cycle = int(status_info["cycle_counter"]) + 1
        max_cycles = int(status_info["max_cycles"])

        self.lbl_cycles = tk.Label(
            status_container,
            text=f"Cycle: {display_cycle} / {max_cycles}",
            font=fonts["labels"],
            fg=colors["status_pause"],
            bg=colors["background_top"],
            cursor="hand2",
        )
        self.lbl_cycles.pack()
        self.lbl_cycles.bind("<Button-1>", lambda e: self.toggle_start_pause())

    def _create_navigation_section(self, parent, colors, fonts):
        """
        ✅ ИСПРАВЛЕНИЕ #3: Grid с weight для правильного распределения
        Settings - слева, Navigation - центр, Exit - справа
        """
        nav_container = tk.Frame(parent, bg=colors["background_bot"])
        nav_container.pack(fill=tk.X, pady=10, padx=10)

        # ✅ Grid с 3 колонками: left(1), center(0), right(1)
        nav_container.columnconfigure(0, weight=1)  # Settings - растягивается
        nav_container.columnconfigure(1, weight=0)  # Navigation - фиксировано
        nav_container.columnconfigure(2, weight=1)  # Exit - растягивается

        # Settings (слева)
        settings_btn = self._create_button(
            nav_container,
            text=self.button_labels.get("settings", "⚙"),
            command=self.open_settings_window,
            colors=colors,
            fonts=fonts,
        )
        settings_btn.grid(row=0, column=0, sticky=tk.W, padx=5)

        # Navigation (центр) - Reset, <<, >>
        center_frame = tk.Frame(nav_container, bg=colors["background_bot"])
        center_frame.grid(row=0, column=1, padx=10)

        self._create_button(
            center_frame,
            text=self.button_labels.get("reset_timer", "↺ Reset"),
            command=self.timer.reset,
            colors=colors,
            fonts=fonts,
        ).pack(side=tk.LEFT, padx=3)

        # ✅ ИСПРАВЛЕНИЕ #2: Кнопка << с правильным вызовом
        self._create_button(
            center_frame,
            text=self.button_labels.get("next_previous_buttons", ["<<", ">>"])[0],
            command=lambda: self._step_phase_back(),
            colors=colors,
            fonts=fonts,
        ).pack(side=tk.LEFT, padx=3)

        self._create_button(
            center_frame,
            text=self.button_labels.get("next_previous_buttons", ["<<", ">>"])[1],
            command=lambda: self._step_phase_forward(),
            colors=colors,
            fonts=fonts,
        ).pack(side=tk.LEFT, padx=3)

        # Exit (справа)
        exit_btn = self._create_button(
            nav_container,
            text=self.button_labels.get("exit", "Exit"),
            command=self._on_close,
            colors=colors,
            fonts=fonts,
        )
        exit_btn.grid(row=0, column=2, sticky=tk.E, padx=5)

    def _step_phase_back(self):
        """
        ✅ ИСПРАВЛЕНИЕ #2: Обёртка для step_in_phase с обновлением UI
        """
        self.timer.step_in_phase(schedule_tick=True, step_back=True)
        # ✅ Явно обновляем UI после ручного вызова
        self.root.after(50, self.update_timer_display)

    def _step_phase_forward(self):
        """
        Обёртка для step_in_phase вперёд
        """
        self.timer.step_in_phase(schedule_tick=True, step_back=False)
        self.root.after(50, self.update_timer_display)

    def _create_quick_settings_section(self, parent, colors, fonts):
        """
        ✅ ИСПРАВЛЕНИЕ #4: Использует лейблы из конфига
        """
        qs_frame = tk.Frame(parent, bg=colors["background_bot"])
        qs_frame.pack(fill=tk.X, padx=5, pady=5)

        quick_settings_map = {
            "always_on_top": "system.always_on_top_enabled",
            "pause_on_end": "system.pause_on_end_enabled",
            "sound_player": "system.sound_player_enabled",
            "media_api": "system.media_api_enabled",
        }

        for key, sys_key in quick_settings_map.items():
            is_visible = self.settings.get(f"system.quick_settings.{key}", False)
            if is_visible:
                is_active = self.settings.get(sys_key, False)

                # ✅ ИСПРАВЛЕНИЕ #4: Лейбл из конфига
                btn_text = self.button_labels.get(key, key.replace("_", " ").title())

                btn = self._create_button(
                    qs_frame,
                    text=btn_text,
                    command=lambda k=key, s=sys_key: self.toggle_quick_setting(k, s),
                    colors=colors,
                    fonts=fonts,
                    is_pressed=is_active,
                )
                btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

    def _create_button(self, parent, text, command, colors, fonts, is_pressed=False):
        """
        Создаёт кнопку с единым стилем
        """
        bg = colors["button_pressed_bg"] if is_pressed else colors["button_bg"]
        fg = colors["button_pressed_fg"] if is_pressed else colors["button_fg"]
        relief = tk.SUNKEN if is_pressed else tk.RAISED

        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=fonts["buttons"],
            bg=bg,
            fg=fg,
            relief=relief,
            activebackground=colors["button_pressed_bg"],
            activeforeground=colors["button_pressed_fg"],
            borderwidth=2,
        )
        return btn

    def toggle_quick_setting(self, key, sys_key):
        """
        Переключает состояние быстрой настройки
        """
        self.settings.toggle_setting(sys_key)
        # ✅ Не пересобираем весь UI, только обновляем кнопки
        self.root.after(100, self._init_ui)

    def toggle_start_pause(self):
        """
        Переключает Старт/Пауза
        """
        if self.timer.process_status in (3, 4):
            self.timer.start()
        else:
            self.timer.pause()

    def update_timer_display(self):
        """
        Обновляет только цифры и статус (без пересборки всего UI)
        """
        try:
            if not hasattr(self, "lbl_status") or not hasattr(self, "lbl_timer"):
                return

            info = self.timer.get_status_info()
            colors = self.settings.get_current_theme_colors()
            fonts = self.settings.get_current_fonts()

            status_text = self.settings.get(
                f"appearence.status_title.{info['status_type']}", "TIMER"
            )
            status_color = colors[f"status_{info['status_type']}"]

            self.lbl_status.config(text=status_text, fg=status_color, font=fonts["status"])
            self.lbl_timer.config(text=info["minutes"], fg=status_color, font=fonts["minutes"])

            # ✅ ИСПРАВЛЕНИЕ #1: Циклы отображаются корректно
            display_cycle = int(info["cycle_counter"]) + 1
            max_cycles = int(info["max_cycles"])
            self.lbl_cycles.config(text=f"Cycle: {display_cycle} / {max_cycles}")

            self.root.title(f"{status_text} - {info['minutes']}")

            top_enabled = self.settings.get("system.always_on_top_enabled", False)
            self.root.attributes("-topmost", top_enabled)

        except Exception as e:
            # ✅ Логирование ошибок вместо silent pass
            print(f"Error updating timer display: {e}")

    def _on_close(self):
        """
        ✅ Корректное закрытие приложения с очисткой ресурсов
        """
        if hasattr(self, "_tick_job") and self._tick_job:
            self.root.after_cancel(self._tick_job)
        self.timer._stop_audio()
        self.root.quit()
        self.root.destroy()

    def open_settings_window(self):
        """
        Открывает окно настроек (проверка на уже открытое)
        """
        # ✅ Проверяем все Toplevel окна
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Toplevel) and widget.title() == "Settings":
                widget.focus()
                return

        SettingsWindow(self.root, self.settings, self._init_ui)


if __name__ == "__main__":
    app = MyGUI()
