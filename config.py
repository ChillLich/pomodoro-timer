import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional


class SettingsManager:
    def __init__(self):
        self.config_path = Path("settings.json")
        self.default_settings = {
            "window": {
                "width": 336,
                "height": 255,
                "padxy": 5,  # в пикселях
                "padxy_s": 2,
                "padxy_ss": 0,  # в info - между минутами и статусом
                "entry_width": 5,  # в символах
                "pad_x_status_label": 0,
                "pad_y_status_label": 0,
            },
            # default minutes values
            "timer": {
                "small": [10, 2, 6, 4],
                "medium": [25, 5, 15, 4],  # focus/work  # small chill  # big chill  # cycles amount
                "big": [45, 9, 27, 4],
                "user": [],
                "current_preset": "small",
            },
            "appearence": {
                "themes": {
                    "light": {
                        "status_rest": "#3BBF77",
                        "status_pause": "#808080",
                        "status_focus": "#3B77BC",
                        "bg": [],
                    },
                    "dark": {
                        "status_rest": "#012B00",
                        "status_pause": "#252525",
                        "status_focus": "#002249",
                        "bg": [],
                    },
                    "user": {},
                    "current_preset": "dark",
                },
                "fonts": {
                    "status": ["Times", "24", "bold"],
                    "minutes": ["Times", "32", "bold"],
                    "buttons": [],
                    "labels": [],
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
            return default

    def set_val(self, key: str, value_to_save: Any) -> None:
        """Set value, accept nested keys by dots"""
        keys = key.split(".")
        ref = self.settings
        for k in keys[:-1]:
            ref = ref[k]
        ref[keys[-1]] = value_to_save

    def reset_to_default(self, section: Optional[str] = None) -> None:
        """Reset full settings or section(for future) to default"""
        if section:
            if section in self.default_settings:
                self.settings[section] = self.default_settings[section].copy()
        else:
            self.settings = self.default_settings.copy()
