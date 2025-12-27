import json
from pathlib import Path
from typing import Any, Callable, Dict


class SettingsManager:
    def __init__(self):
        self.config_path = Path("settings.json")
        self.default_settings = {
            "window": {
                "width": 336,
                "height": 255,
                "padxy": 5,
                "padxy_s": 2,
                "padxy_ss": 0,
                "entry_width": 5,
                "pad_x_status_label": 0,
                "pad_y_status_label": 0,
            },
            "timer": {
                "small": [10, 2, 6, 4],
                "medium": [25, 5, 15, 4],
                "big": [45, 9, 27, 4],
                "user": [],
                "current_preset": "medium",
            },
            "appearence": {
                "themes": {
                    "light": {
                        "status_rest": "#3BBF77",
                        "status_pause": "#808080",
                        "status_focus": "#3B77BC",
                        "background_top": "#FFFFFF",
                        "background_bot": "#F0F0F0",
                    },
                    "dark": {
                        "status_rest": "#012B00",
                        "status_pause": "#252525",
                        "status_focus": "#002249",
                        "background_top": "#1E1E1E",
                        "background_bot": "#2D2D2D",
                    },
                    "user": {
                        "status_rest": "#3BBF77",
                        "status_pause": "#808080",
                        "status_focus": "#3B77BC",
                        "background_top": "#1E1E1E",
                        "background_bot": "#2D2D2D",
                    },
                    "current_preset": "dark",
                },
                "fonts": {
                    "status": ["Times", "24", "bold"],
                    "minutes": ["Times", "32", "bold"],
                    "buttons": ["Helvetica", "10"],
                    "labels": ["Helvetica", "10"],
                },
                "status_title": {
                    "pause": "⏸PAUSE",
                    "focus": "▶FOCUS",
                    "rest": "REST",
                },
                "quick_settings_minutes_entries_labels": [
                    "Focus:",
                    "Short:",
                    "Long:",
                    "Cycles:",
                ],
                "quick_settings_buttons_labels": {
                    "always_on_top": "Always on Top",
                    "pause_on_end": "Pause on End",
                    "sound_player": "♫ Sound",
                    "media_api": "Media",
                    "reset_timer": "↺ Reset",
                    "next_previous_buttons": ["<<", ">>"],
                    "settings": "⚙",
                    "exit": "Exit",
                },
            },
            "system": {
                "path_to_focus_track": "work.mp3",
                "path_to_rest_track": "rest.mp3",
                "always_on_top_enabled": False,
                "sound_player_enabled": False,
                "media_api_enabled": True,
                "pause_on_end_enabled": False,
                "quick_settings": {
                    "minutes_entries": True,
                    "always_on_top": False,
                    "pause_on_end": False,
                    "sound_player": True,
                    "media_api": True,
                    "reset_timer": True,
                    "next_previous_buttons": True,
                },
            },
        }
        self.settings = {}
        # Callback для уведомления об изменениях настроек
        self.callbacks = []

    def load(self) -> Dict[str, Any]:
        """Load settings from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as file:
                    self.settings = json.load(file)
            else:
                self.settings = self.default_settings.copy()
        except (json.JSONDecodeError, IOError) as err:
            self.settings = self.default_settings.copy()
            print(f"Settings load error:\n{err}")
        return self.settings

    def save(self) -> None:
        """Save settings to settings.json"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as file:
                json.dump(self.settings, file, indent=4, ensure_ascii=False)
        except IOError as err:
            print(f"Save settings error:\n{err}")
        else:
            print("Settings saved!")

    def get(self, key: str, default: Any = None) -> Any:
        """Get value, accept nested keys by dots"""
        keys = key.split(".")
        value = self.settings
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            print(f"ERROR when getting setting {keys}")
            return default

    def set_val(self, key: str, value_to_save: Any) -> None:
        """Set value, accept nested keys by dots"""
        keys = key.split(".")
        ref = self.settings
        for k in keys[:-1]:
            ref = ref[k]
        ref[keys[-1]] = value_to_save

        # Уведомляем всех подписчиков об изменениях
        for callback in self.callbacks:
            callback(key, value_to_save)

    def add_callback(self, callback: Callable) -> None:
        """Добавление callback для уведомления об изменениях"""
        self.callbacks.append(callback)

    def remove_callback(self, callback: Callable) -> None:
        """Удаление callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def set_timer_preset(self, preset_name: str, values: list | None = None) -> None:
        """Установка пресета таймера"""
        if preset_name not in ["small", "medium", "big", "user"]:
            return

        # Если переключаемся на user и переданы значения
        if preset_name == "user" and values:
            self.set_val("timer.user", values)

        # Устанавливаем текущий пресет
        self.set_val("timer.current_preset", preset_name)
        self.save()

    def toggle_setting(self, setting_key: str) -> bool:
        """Переключение boolean настройки"""
        current_value = self.get(setting_key)
        if isinstance(current_value, bool):
            new_value = not current_value
            self.set_val(setting_key, new_value)
            self.save()
            return new_value
        return current_value

    # ----------------- НИЖЕ ДЛЯ ГУИ ОБЛЕГЧАЮЩИЕ МЕТОДЫ
    def get_current_theme_colors(self):
        """Получение цветов текущей темы"""
        theme_name = self.get("appearence.themes.current_preset", "dark")
        theme = self.get(f"appearence.themes.{theme_name}", {})

        return {
            "status_rest": theme.get("status_rest", "#3BBF77"),
            "status_pause": theme.get("status_pause", "#808080"),
            "status_focus": theme.get("status_focus", "#3B77BC"),
            "background_top": theme.get("background_top", "#1E1E1E"),
            "background_bot": theme.get("background_bot", "#2D2D2D"),
        }

    def get_current_fonts(self):
        """Получение текущих шрифтов"""
        fonts = self.get("appearence.fonts", {})

        # Вспомогательная функция для получения шрифта или значения по умолчанию
        def get_font(key, default):
            value = fonts.get(key, default)
            # Если значение - пустой список, используем значение по умолчанию
            if isinstance(value, list) and len(value) == 0:
                value = default
            # Гарантируем, что возвращается кортеж
            return tuple(value)

        return {
            "status": get_font("status", ["Times", "24", "bold"]),
            "minutes": get_font("minutes", ["Times", "32", "bold"]),
            "buttons": get_font("buttons", ["Helvetica", "10"]),
            "labels": get_font("labels", ["Helvetica", "10"]),
        }
