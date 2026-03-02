import tkinter as tk
from tkinter import messagebox, ttk

from config import SettingsManager
from settings_window import SettingsWindow
from TIMER import Timer


class MyGUI:
    """Основной класс графического интерфейса приложения Pomodoro Timer."""

    def __init__(self):
        """Инициализация приложения, загрузка настроек и запуск основного цикла."""
        self.settings = SettingsManager()
        self.settings.load()
        self.timer = Timer(self.settings)

        self.root = tk.Tk()
        self.root.title("Pomodoro Timer")

        self.button_labels = self.settings.get(
            "appearence.quick_settings_buttons_labels",
            {
                "always_on_top": "Always on Top",
                "pause_on_end": "Pause on End",
                "sound_player": "♫ Sound",
                "media_api": "Media",
                "reset_timer": "↺ Reset",
                "next_previous_buttons": ["   <<   ", "   >>   "],
                "settings": "⚙",
                "exit": "Exit",
            },
        )

        # ✅ Инициализация переменных для job'ов
        self._rebuild_job = None
        self._tick_job = None
        self._resize_job = None
        self.qs_buttons = {}
        self.nav_buttons = []

        # ✅ Храним ссылки на все контейнеры для обновления
        self.all_frames = []

        # ✅ Загружаем размеры из настроек (или используем дефолтные)
        self._apply_window_geometry()

        # ✅ Регистрируем обработчик изменения размера окна
        self.root.bind("<Configure>", self._on_window_resize)

        self.settings.add_callback(self._on_settings_changed)

        self.timer.set_gui_callbacks(
            update_callback=self.update_timer_display,
            tick_callback=self.schedule_tick,
        )

        self._init_ui()
        self._apply_topmost_setting()

        if self.timer.process_status not in (3, 4):
            self.timer.start()

        # ✅ Регистрация обработчика закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.root.mainloop()

    def _apply_window_geometry(self):
        """Применяет размеры окна из настроек."""
        w = self.settings.get("window.width", 336)
        h = self.settings.get("window.height", 255)
        self.root.geometry(f"{w}x{h}")

    def _on_window_resize(self, event):
        """
        Обработчик изменения размера окна.
        Сохраняет размеры только если окно не свернуто/развернуто.
        """
        if event.widget == self.root and event.width > 0 and event.height > 0:
            if self._resize_job:
                self.root.after_cancel(self._resize_job)
            self._resize_job = self.root.after(500, self._save_window_size)

    def _save_window_size(self):
        """Сохраняет текущие размеры окна в настройки."""
        w = self.root.winfo_width()
        h = self.root.winfo_height()

        current_w = self.settings.get("window.width", 336)
        current_h = self.settings.get("window.height", 255)

        if abs(w - current_w) > 5 or abs(h - current_h) > 5:
            self.settings.set_val("window.width", w)
            self.settings.set_val("window.height", h)

    def _apply_topmost_setting(self):
        """Применяет атрибут 'поверх всех окон' на основе настроек."""
        top_enabled = self.settings.get("system.always_on_top_enabled", False)
        self.root.attributes("-topmost", top_enabled)

    def _on_settings_changed(self, key: str, value):
        """
        Обработчик изменений настроек.
        Оптимизирует перерисовку, вызывая обновление только нужных частей UI.
        """
        if "appearence.themes" in key or "system.quick_settings" in key:
            if self._rebuild_job:
                self.root.after_cancel(self._rebuild_job)
            self._rebuild_job = self.root.after(150, self._update_ui_config)
        elif key.startswith("window."):
            self.root.after(100, self._apply_window_geometry)
        elif key.startswith("timer."):
            self.root.after(100, self.update_timer_display)

    def schedule_tick(self, action, delay=None):
        """
        Планирует или отменяет следующий тик таймера через event loop Tkinter.

        Args:
            action: 'schedule' или 'cancel'.
            delay: Задержка в миллисекундах для планирования.
        """
        if action == "cancel":
            if self._tick_job:
                self.root.after_cancel(self._tick_job)
                self._tick_job = None
            return None
        elif action == "schedule":
            self._tick_job = self.root.after(delay, self.timer.count_tick)
            return self._tick_job
        return None

    def _init_ui(self):
        """Создает структуру интерфейса при первом запуске."""
        colors = self.settings.get_current_theme_colors()
        fonts = self.settings.get_current_fonts()

        self.top_frame = tk.Frame(self.root, bg=colors["background_top"])
        self.top_frame.pack(fill=tk.X, side=tk.TOP)
        self.all_frames.append(self.top_frame)
        self._create_status_section(self.top_frame, colors, fonts)

        self.bot_frame = tk.Frame(self.root, bg=colors["background_bot"])
        self.bot_frame.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM)
        self.all_frames.append(self.bot_frame)
        self._create_navigation_section(self.bot_frame, colors, fonts)
        self._create_quick_settings_section(self.bot_frame, colors, fonts)

    def _update_ui_config(self):
        """
        Обновляет конфигурацию UI (цвета, шрифты, видимость кнопок) без пересоздания виджетов.
        ✅ ИСПРАВЛЕНИЕ: Рекурсивное обновление всех фреймов и виджетов
        """
        colors = self.settings.get_current_theme_colors()
        fonts = self.settings.get_current_fonts()

        # ✅ Обновляем все фреймы рекурсивно
        self._update_all_frames_colors(self.root, colors)

        # ✅ Обновляем таймер
        self.update_timer_display()

        # ✅ Обновляем кнопки быстрых настроек
        self._update_quick_settings_buttons(colors, fonts)

        # ✅ Обновляем кнопки навигации
        self._update_all_button_colors(colors, fonts)

    def _update_all_frames_colors(self, widget, colors):
        """
        ✅ НОВОЕ: Рекурсивно обновляет цвета всех фреймов и их содержимого.
        """
        for child in widget.winfo_children():
            if isinstance(child, tk.Frame):
                # Определяем какой цвет фона применить
                if child in [self.top_frame] or self._is_child_of(child, self.top_frame):
                    bg_color = colors["background_top"]
                else:
                    bg_color = colors["background_bot"]

                child.config(bg=bg_color)

                # Рекурсивно обрабатываем вложенные виджеты
                self._update_all_frames_colors(child, colors)

            elif isinstance(child, tk.Label):
                # Обновляем фон и текст у меток
                parent_bg = child.master.cget("bg")
                child.config(bg=parent_bg, fg=colors["button_fg"])

            elif isinstance(child, tk.Button):
                # Кнопки обновляются отдельно в _update_all_button_colors
                pass

    def _is_child_of(self, child, parent):
        """Проверяет является ли виджет потомком указанного родителя."""
        current = child.master
        while current:
            if current == parent:
                return True
            if current == self.root:
                return False
            current = current.master
        return False

    def _update_all_button_colors(self, colors, fonts):
        """
        ✅ Обновляет цвета всех кнопок в интерфейсе.
        """
        # ✅ Обновляем кнопки навигации
        for btn in self.nav_buttons:
            try:
                btn.config(
                    bg=colors["button_bg"],
                    fg=colors["button_fg"],
                    activebackground=colors["button_pressed_bg"],
                    activeforeground=colors["button_pressed_fg"],
                    font=fonts["buttons"],
                )
            except Exception:
                pass

        # ✅ Обновляем кнопки быстрых настроек
        self._update_quick_settings_buttons(colors, fonts)

    def _update_quick_settings_buttons(self, colors, fonts):
        """
        Обновляет существующие кнопки быстрых настроек.
        ✅ ИСПРАВЛЕНИЕ: Проверяем наличие кнопки в словаре перед обновлением
        """
        if not hasattr(self, "qs_buttons") or not self.qs_buttons:
            return

        quick_settings_map = {
            "always_on_top": "system.always_on_top_enabled",
            "pause_on_end": "system.pause_on_end_enabled",
            "sound_player": "system.sound_player_enabled",
            "media_api": "system.media_api_enabled",
        }

        # ✅ Сначала скрываем все кнопки
        for btn in self.qs_buttons.values():
            btn.pack_forget()

        # ✅ Обновляем и показываем только видимые кнопки
        for key, sys_key in quick_settings_map.items():
            # ✅ ПРОВЕРКА: кнопка должна существовать в словаре
            if key not in self.qs_buttons:
                continue

            is_visible = self.settings.get(f"system.quick_settings.{key}", False)
            if is_visible:
                is_active = self.settings.get(sys_key, False)
                btn_text = self.button_labels.get(key, key.replace("_", " ").title())

                btn = self.qs_buttons[key]
                btn.config(
                    text=btn_text,
                    bg=colors["button_pressed_bg"] if is_active else colors["button_bg"],
                    fg=colors["button_pressed_fg"] if is_active else colors["button_fg"],
                    activebackground=colors["button_pressed_bg"],
                    activeforeground=colors["button_pressed_fg"],
                    relief=tk.SUNKEN if is_active else tk.RAISED,
                    font=fonts["buttons"],
                )
                btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
            # ✅ Если кнопка не видима - она остаётся скрытой (pack_forget выше)

    def _create_status_section(self, parent, colors, fonts):
        """Создает секцию отображения статуса и времени таймера."""
        status_container = tk.Frame(parent, bg=colors["background_top"], cursor="hand2")
        status_container.pack(anchor=tk.CENTER, pady=20)
        status_container.bind("<Button-1>", lambda e: self.toggle_start_pause())
        self.all_frames.append(status_container)

        status_info = self.timer.get_status_info()
        status_text = self.settings.get(
            f"appearence.status_title.{status_info['status_type']}", "TIMER"
        )
        status_color = colors[f"status_{status_info['status_type']}"]

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

        display_cycle = int(status_info["cycle_counter"]) + 1
        max_cycles = int(status_info["max_cycles"])

        self.lbl_cycles = tk.Label(
            status_container,
            text=f"Cycle: {display_cycle} / {max_cycles}",
            font=fonts["labels"],
            fg=colors["button_fg"],
            bg=colors["background_top"],
            cursor="hand2",
        )
        self.lbl_cycles.pack()
        self.lbl_cycles.bind("<Button-1>", lambda e: self.toggle_start_pause())

    def _create_navigation_section(self, parent, colors, fonts):
        """
        Создает секцию навигации.
        ✅ Сохраняет ссылки на кнопки в self.nav_buttons
        """
        nav_container = tk.Frame(parent, bg=colors["background_bot"])
        nav_container.pack(fill=tk.X, pady=10, padx=10)
        self.all_frames.append(nav_container)

        nav_container.columnconfigure(0, weight=1)
        nav_container.columnconfigure(1, weight=0)
        nav_container.columnconfigure(2, weight=1)

        # ✅ Очищаем список кнопок перед созданием новых
        self.nav_buttons = []

        settings_btn = self._create_button(
            nav_container,
            text=self.button_labels.get("settings", "⚙"),
            command=self.open_settings_window,
            colors=colors,
            fonts=fonts,
        )
        settings_btn.grid(row=0, column=0, sticky=tk.W, padx=5)
        self.nav_buttons.append(settings_btn)

        center_frame = tk.Frame(nav_container, bg=colors["background_bot"])
        center_frame.grid(row=0, column=1, padx=10)
        self.all_frames.append(center_frame)

        prev_btn = self._create_button(
            center_frame,
            text=self.button_labels.get("next_previous_buttons", ["   <<   ", "   >>   "])[0],
            command=lambda: self._step_phase_back(),
            colors=colors,
            fonts=fonts,
        )
        prev_btn.pack(side=tk.LEFT, padx=3)
        self.nav_buttons.append(prev_btn)

        reset_btn = self._create_button(
            center_frame,
            text=self.button_labels.get("reset_timer", "↺ Reset"),
            command=self.timer.reset,
            colors=colors,
            fonts=fonts,
        )
        reset_btn.pack(side=tk.LEFT, padx=3)
        self.nav_buttons.append(reset_btn)

        next_btn = self._create_button(
            center_frame,
            text=self.button_labels.get("next_previous_buttons", ["   <<   ", "   >>   "])[1],
            command=lambda: self._step_phase_forward(),
            colors=colors,
            fonts=fonts,
        )
        next_btn.pack(side=tk.LEFT, padx=3)
        self.nav_buttons.append(next_btn)

        exit_btn = self._create_button(
            nav_container,
            text=self.button_labels.get("exit", "Exit"),
            command=self._on_close,
            colors=colors,
            fonts=fonts,
        )
        exit_btn.grid(row=0, column=2, sticky=tk.E, padx=5)
        self.nav_buttons.append(exit_btn)

    def _step_phase_back(self):
        """Переключает таймер на предыдущую фазу и обновляет UI."""
        self.timer.step_in_phase(schedule_tick=True, step_back=True)
        self.root.after(50, self.update_timer_display)

    def _step_phase_forward(self):
        """Переключает таймер на следующую фазу и обновляет UI."""
        self.timer.step_in_phase(schedule_tick=True, step_back=False)
        self.root.after(50, self.update_timer_display)

    def _create_quick_settings_section(self, parent, colors, fonts):
        """
        Создает панель быстрых настроек.
        ✅ ИСПРАВЛЕНИЕ: Создаём все кнопки заранее, независимо от видимости
        """
        qs_frame = tk.Frame(parent, bg=colors["background_bot"])
        qs_frame.pack(fill=tk.X, padx=5, pady=5)
        self.all_frames.append(qs_frame)

        quick_settings_map = {
            "always_on_top": "system.always_on_top_enabled",
            "pause_on_end": "system.pause_on_end_enabled",
            "sound_player": "system.sound_player_enabled",
            "media_api": "system.media_api_enabled",
        }

        self.qs_buttons = {}

        # ✅ СОЗДАЁМ все кнопки заранее, даже если они скрыты
        for key, sys_key in quick_settings_map.items():
            is_visible = self.settings.get(f"system.quick_settings.{key}", False)
            is_active = self.settings.get(sys_key, False)
            btn_text = self.button_labels.get(key, key.replace("_", " ").title())

            btn = self._create_button(
                qs_frame,
                text=btn_text,
                command=lambda k=key, s=sys_key: self.toggle_quick_setting(k, s),
                colors=colors,
                fonts=fonts,
                is_pressed=is_active,
            )

            # ✅ Сохраняем ссылку на кнопку независимо от видимости
            self.qs_buttons[key] = btn

            # ✅ Показываем только если кнопка должна быть видима
            if is_visible:
                btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
            else:
                btn.pack_forget()  # Скрываем, но не уничтожаем

    def _create_button(self, parent, text, command, colors, fonts, is_pressed=False):
        """
        Фабрика кнопок с единым стилем.

        Args:
            is_pressed: Отображать кнопку в нажатом состоянии.
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
        """Переключает состояние быстрой настройки."""
        new_state = self.settings.toggle_setting(sys_key)

        if sys_key == "system.always_on_top_enabled":
            self.root.attributes("-topmost", new_state)

        colors = self.settings.get_current_theme_colors()
        fonts = self.settings.get_current_fonts()
        self.root.after(50, lambda: self._update_quick_settings_buttons(colors, fonts))

    def toggle_start_pause(self):
        """Переключает состояние таймера между Запуском и Паузой."""
        if self.timer.process_status in (3, 4):
            self.timer.start()
        else:
            self.timer.pause()

    def update_timer_display(self):
        """Обновляет текстовые метки таймера без пересоздания виджетов."""
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

            display_cycle = int(info["cycle_counter"]) + 1
            max_cycles = int(info["max_cycles"])
            self.lbl_cycles.config(text=f"Cycle: {display_cycle} / {max_cycles}")

            self.root.title(f"{status_text} - {info['minutes']}")

        except Exception as e:
            print(f"Error updating timer display: {e}")

    def _on_close(self):
        """
        Корректно закрывает приложение, останавливая таймер и аудио.
        """
        # ✅ Отменяем все запланированные задачи
        if self._tick_job:
            self.root.after_cancel(self._tick_job)
        if self._rebuild_job:
            self.root.after_cancel(self._rebuild_job)
        if self._resize_job:
            self.root.after_cancel(self._resize_job)

        # ✅ Сохраняем текущие размеры окна
        self._save_window_size()

        # ✅ Сохраняем настройки в файл
        self.settings.save()

        # ✅ Останавливаем аудио
        self.timer._stop_audio()

        self.root.quit()
        self.root.destroy()

    def open_settings_window(self):
        """Открывает окно настроек, предотвращая создание дубликатов."""
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Toplevel) and widget.title() == "Settings":
                widget.focus()
                return

        SettingsWindow(self.root, self.settings, self._update_ui_config)


if __name__ == "__main__":
    app = MyGUI()
