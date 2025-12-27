import os
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox as mb

# pip install keyboard
# sends PLAY/PAUSE media to system API, may ask root
from keyboard import send as send_to_system_api
from pygame import mixer

from config import SettingsManager

# TO DO:

# Добавить кнопку настроек, внутрь них:
# 1. настройки тем: темная светлая
# 2. Настройка пути к файлам .mp3
# 3.1 отдельная галочка для воспроизводить ли звук
# 3.2 отдельная галочка для отсылать ли play в system api
# 3.3 галочки посмотреть в config.py в system
# 4. Перенести все entry в настройки с ползунками
# Сделать автоматическое считывание из Entry при изменении, не по Reset.
# entry.bind("<FocusOut>", lambda e: print("После редак:", entry.get()))
# 4.1 Sound оставить в главном окошке
# 5 Сделать отдельные reset кнопки одна для циклов другая для в целом настроек на дефолт
# 6. Галочку для паузы между фазами до подтверждения старта пользователем
# 7. сохранять и парсить .json для настроек, а не .txt
# 8. Always on top опция
# 9. Собрать все if настроек в декоратор

# Добавить кнопки перехода на следующую фазу и предыдущую,

# Изменить отображение количества пройденных циклов (добавить)

# Почистить код хехе

# Собрать в .exe с иконкой


class MyGUI:

    MINUT = 60

    def __init__(self):
        # Загрузить настройки
        self.sm = SettingsManager()
        self.sm.load()

        # Инициализировать миксер для проигрывания локальных медиафайлов
        mixer.init()

        self.WIDTH = 336  # 289
        self.HEIGHT = 255  # 255
        self.PADXY = 5  # в пикселях
        self.PADXY_s = 2
        self.PADXY_ss = 0  # в info - между минутами и статусом
        self.ENTRY_WIDTH = 5  # в символах
        self.FONT_STATUS = ("Times", "24", "bold")
        self.FONT_MINS = ("Times", "32", "bold")
        self.PADX_STATUS_LABEL = 0
        self.PADY_STATUS_LABEL = 0
        self.COLOR_REST = "#3BBF77"
        self.COLOR_PAUSE = "#808080"
        self.COLOR_WORK = "#3B77BC"

        self.PATH_TO_CHECK_PATHFILE = "path.txt"

        self.path_to_work = "Work.mp3"  # дефолтные пути
        self.path_to_rest = "Rest.mp3"

        self.sound_enabled = True
        self.sound_api_enabled = True
        self.pause_between_phases_needed = False  # False отключить паузу между фазами

        self.buttons_dict = {
            "End-pause": lambda: self.pause_between_phases_toggle(),
            "Media": lambda: self.sound_api_enabler(),
            "↺ Reset": lambda: self.reset(),
            "♫ Sound": lambda: self.sound_enabler(),
            "Exit": lambda: (mixer.quit(), self.main_window.destroy()),
        }
        self.STATUS_TITLE = {
            "pause": "⏸PAUSE",
            "focus": "▶FOCUS",
            "rest": "REST",
        }  # get("appearence.status_title")

        self.labels_settings_list = [
            "Focus:",
            "Small chill:",
            "Big chill:",
            "Cycles:",
        ]
        # default minutes values

        self.list_with_min_values = self.sm.get("timer.small")

        # Инициализация счетчиков
        # отслеживание в каком статусе поток 1 = rest, 2 = work,
        # 3 = pause from rest, 4 = pause from work (+ 4=start)
        self.process_status = 4
        self.seconds_till_next_phase = self.MINUT * self.list_with_min_values[0]
        self.cycle_counter = 0

        # Оформить окошко
        self.main_window = tk.Tk()
        self.main_window.title("Timer by @CHILLLICH")
        try:
            self.main_window.iconphoto(True, tk.PhotoImage(file="icons\\icon.png"))
        except Exception:
            print("Not found icon.png")

        # отслеживание статуса
        self.init_info()

        # Поля с настройками и всё к ним
        self.init_quick_settings()

        # кнопки старт, пауза, сброс, выход
        self.init_butt()

        self.update_status()

        self.process_path()

        if not os.path.exists(self.PATH_TO_CHECK_PATHFILE):
            self.sound_enabled = False
            self.butts[3].config(relief=tk.RAISED)

        tk.mainloop()

    # дисплей с текущим статусом
    def init_info(self):
        """
        Initialize info widgets.
        Show what stage/phase right now: REST/FOCUS/PAUSE.
        How long till next phase is.
        """
        # для статуса
        self.frame_info_status = tk.Frame(self.main_window)
        self.frame_info_status.pack(padx=self.PADXY, pady=self.PADXY_ss)

        self.output_status = tk.StringVar()
        self.output_status_label = tk.Label(
            self.frame_info_status,
            textvariable=self.output_status,
            font=self.FONT_STATUS,  # type: ignore
        )
        self.output_status_label.pack(
            side="top",
            padx=self.PADX_STATUS_LABEL,
            pady=self.PADY_STATUS_LABEL,
        )

        # для минут
        self.frame_info_minutes = tk.Frame(self.main_window)
        self.frame_info_minutes.pack(padx=self.PADXY, pady=self.PADXY_ss)

        # для
        self.output_cycle = tk.StringVar()
        self.label_mins_1 = tk.Label(self.frame_info_minutes, textvariable=self.output_cycle)
        # self.output_cycle.set()

        self.mins_output = tk.StringVar()
        self.label_mins_output_label = tk.Label(
            self.frame_info_minutes,
            textvariable=self.mins_output,
            font=self.FONT_MINS,  # type: ignore
        )

        self.label_mins_1.pack(side="top")
        self.label_mins_output_label.pack(side="top")

    # виджеты для настроек таймера
    def init_quick_settings(self):
        """Initializes quick-settings widgets"""
        # окна с текущей конфигурацией сколько минут отдых/фокус
        # c возможностью задать время
        # какой цикл из скольки и сколько минут отдых после них
        self.frame_set_n_info = tk.Frame(self.main_window)
        self.frame_set_n_info.pack(padx=self.PADXY, pady=self.PADXY)
        self.frame_settings_labels = []
        self.label_settings = []
        self.entry_settings = []

        self.label_settings_description = tk.Label(
            self.frame_set_n_info,
            text="Hit reset to specify amount of minutes for phases:",
        )
        self.label_settings_description.pack(side="top", padx=self.PADXY)

        for i in range(4):
            self.frame_settings_labels.append(tk.Frame(self.frame_set_n_info))
            self.frame_settings_labels[i].pack(side="left", padx=self.PADXY, pady=self.PADXY)
            self.label_settings.append(
                tk.Label(
                    self.frame_settings_labels[i],
                    text=self.labels_settings_list[i],
                )
            )
            self.label_settings[i].pack(padx=self.PADXY)
            self.entry_settings.append(
                tk.Entry(
                    self.frame_settings_labels[i],
                    width=self.ENTRY_WIDTH,
                    justify=tk.RIGHT,
                )
            )
            self.entry_settings[i].insert(0, self.list_with_min_values[i])
            self.entry_settings[i].pack(padx=(self.PADXY))

        self.bind_play_pause_to_frames()

    # Инит кнопок
    def init_butt(self):
        """Buttons initialization."""
        self.butts = []

        self.frame_butt = tk.Frame(self.main_window)

        # кнопки pause play не нужны
        items = list(self.buttons_dict.items())
        for k, v in items:
            butt = tk.Button(self.frame_butt, text=k, command=v)
            butt.pack(side="left", padx=self.PADXY, pady=self.PADXY)
            self.butts.append(butt)

        self.frame_butt.pack()

        if self.pause_between_phases_needed:
            self.butts[0].config(relief=tk.SUNKEN)
        if self.sound_api_enabled:
            self.butts[1].config(relief=tk.SUNKEN)
        if self.sound_enabled:
            self.butts[3].config(relief=tk.SUNKEN)

    def bind_play_pause_to_frames(self):
        """Create tag for children frames/widgets of init_info"""
        tag = "frames_for_info"
        frames_to_tag = self.frame_info_minutes, self.frame_info_status

        def add_tag_to_children(w):
            tags = tuple(t for t in w.bindtags() if t != tag)
            w.bindtags((tag,) + tags)
            for child in w.winfo_children():
                add_tag_to_children(child)

        for frame in frames_to_tag:
            add_tag_to_children(frame)
            frame.bind_class(tag, "<Button-1>", self.choose_pause_or_play)

    def choose_pause_or_play(self, event):
        if getattr(self, "_handling_click", False):
            return
        self._handling_click = True
        try:
            if self.process_status in (3, 4):
                self.start()
            elif self.process_status in (1, 2):
                self.pause()
        finally:
            self._handling_click = False

    def start(self):
        """Entry in execution flow, logic of flow"""
        self._handle_audio_api(unpause=True)

        # Статусы: 1=rest, 2=work, 3=pause from rest, 4=pause from work
        if self.process_status == 3:
            self.process_status = 1
            self._play_if_enabled(self.path_to_rest, check_busy=True)
        elif self.process_status == 4:
            self.process_status = 2
            self._play_if_enabled(self.path_to_work, check_busy=True)

        self.schedule_tick()

    def count_till_next_phase(self):
        """Counts for seconds and moves phases"""
        if self.seconds_till_next_phase > 0:
            self.seconds_till_next_phase -= 1
        else:
            self._transition_phase()

            if self.cycle_counter >= self.list_with_min_values[3]:
                self._reset_cycle()

            if self.sound_api_enabled:
                send_to_system_api("play/pause media")

            if self.pause_between_phases_needed:
                self.pause()

        self.schedule_tick()

    def update_status(self):
        """Updates status info"""
        mins, secs = (
            self.seconds_till_next_phase // self.MINUT,
            self.seconds_till_next_phase % self.MINUT,
        )
        self.mins_output.set(f"{mins}:{secs:02d}")

        # Конфигурация статусов
        status_config = {
            (3, 4): ("pause", self.COLOR_PAUSE),
            2: ("focus", self.COLOR_WORK),
            1: ("rest", self.COLOR_REST),
        }

        for status_keys, (title, color) in status_config.items():
            if self.process_status in (
                status_keys if isinstance(status_keys, tuple) else (status_keys,)
            ):
                self.output_status.set(self.STATUS_TITLE[title])
                self.frame_info_status["bg"] = self.frame_info_minutes["bg"] = color
                break

    def schedule_tick(self):
        """Tick creator"""
        self.update_status()
        self.id_to_cancel = self.main_window.after(1000, self.count_till_next_phase)

    def reset(self):
        """Resets flow and updates to specified values"""
        self._cancel_and_stop()

        try:
            self.list_with_min_values[:4] = [float(self.entry_settings[i].get()) for i in range(4)]
        except ValueError:
            mb.showerror("Error", "You must use float values in input fields!")
            return

        self.process_status, self.cycle_counter = 4, 0
        self.seconds_till_next_phase = int(self.MINUT * self.list_with_min_values[0])

        self.process_path()
        self.update_status()

    def pause(self):
        """pauses countdown"""
        self._handle_audio_api(pause_timer=True)
        self.process_status = {1: 3, 2: 4}.get(self.process_status, self.process_status)
        self.update_status()

    # ---------- Комбинированные вспомогательные методы ----------

    def _handle_audio_api(self, unpause=False, pause_timer=False):
        """Универсальная обработка аудио и API операций"""
        try:
            if self.sound_api_enabled:
                send_to_system_api("play/pause media")

            if unpause:
                mixer.music.unpause()

            if pause_timer:
                self.main_window.after_cancel(self.id_to_cancel)
                mixer.music.unpause()
                if mixer.music.get_busy():
                    mixer.music.pause()
        except Exception as err:
            context = "start" if unpause else "pause"
            print(f"Error in {context}:\n{err}")

    def _play_if_enabled(self, path, check_busy=False):
        """Воспроизведение аудио с проверками"""
        if self.sound_enabled and (not check_busy or not mixer.music.get_busy()):
            self.play_audio(path)

    def _transition_phase(self):
        """Переключение между фазами работы и отдыха"""
        if self.process_status == 1:  # REST -> WORK
            self.process_status = 2
            self.seconds_till_next_phase = int(self.list_with_min_values[0] * self.MINUT)
            self._play_if_enabled(self.path_to_work)
        elif self.process_status == 2:  # WORK -> REST
            self.process_status = 1
            self.cycle_counter += 1
            self.seconds_till_next_phase = int(self.list_with_min_values[1] * self.MINUT)
            self._play_if_enabled(self.path_to_rest)

    def _reset_cycle(self):
        """Сброс счетчика циклов"""
        try:
            self.main_window.after_cancel(self.id_to_cancel)
        except AttributeError:
            pass
        self.cycle_counter = 0
        self.seconds_till_next_phase = int(self.list_with_min_values[2] * self.MINUT)

    def _cancel_and_stop(self):
        """Отмена таймера и остановка музыки"""
        try:
            self.main_window.after_cancel(self.id_to_cancel)
            if mixer.music.get_busy():
                mixer.music.stop()
        except AttributeError:
            pass

    def universal_toggler(self, toggle, button, additional_func=None):
        """Switches 'toggle' and changes button relief"""
        if toggle:
            toggle = False
            button.config(relief=tk.RAISED)
            if additional_func:
                additional_func()
        else:
            toggle = True
            button.config(relief=tk.SUNKEN)

    def sound_enabler(self):
        """Enables/disables sound"""
        if self.sound_enabled:
            self.sound_enabled = False
            self.butts[3].config(relief=tk.RAISED)
            if mixer.music.get_busy():  # не потокобезопасен отключить если что
                mixer.music.stop()
        else:
            self.sound_enabled = True
            self.butts[3].config(relief=tk.SUNKEN)

    def sound_api_enabler(self):
        """Enables/disables system multimedia signals"""
        if self.sound_api_enabled:
            self.sound_api_enabled = False
            self.butts[1].config(relief=tk.RAISED)
        else:
            self.sound_api_enabled = True
            self.butts[1].config(relief=tk.SUNKEN)

    def pause_between_phases_toggle(self):
        """Enables/disables pause between phases"""
        if self.pause_between_phases_needed:
            self.pause_between_phases_needed = False
            self.butts[0].config(relief=tk.RAISED)
        else:
            self.pause_between_phases_needed = True
            self.butts[0].config(relief=tk.SUNKEN)

    # Другая функция для воспроизведения,
    # без диалогового окна но с зависимостью от pygame
    def play_audio(self, file_path):
        """Planning audio player"""
        if not self.sound_enabled:
            print("Audio is off.")
            return
        elif not os.path.exists(file_path):
            print(f"Audio file not found: {file_path}")
            # mb.showerror("Error",f"Audio file not found at: {file_path}")
            return

        try:
            self.in_thread = threading.Thread(
                target=self._play_audio_thread,
                args=(
                    file_path,
                    lambda erro: print("Audio thread error.\n", str(erro)),
                ),
                daemon=True,
            )
            # Добавить ли полноценную колбэк функцию, а не lambda?
            # mb.showerror("Error", "Error with sound-player.\n"+str(err))
            self.in_thread.start()
        except RuntimeError:
            print("Thread to play sound can't be created")
            mb.showerror("Error", "Thread to play sound can't be created")
        except Exception as err:
            print(err)
            mb.showerror("Error", "Error with sound-player.\n" + str(err))

    def _play_audio_thread(self, file_path, err_func=None):
        """To be done by thread, plays audio"""
        try:
            mixer.music.load(file_path)
            mixer.music.play()
            while mixer.music.get_busy():
                time.sleep(0.1)
        except Exception as err:
            if err_func:
                self.main_window.after(0, err_func, err)

    # Функция для воспроизведения файла
    # системным плеером с открытием окна (не используется)
    def play_audio_old(self, file_path):
        platform = sys.platform
        if platform == "win32":
            os.system(f'start "" "{file_path}"')
        elif platform == "darwin":  # macOS
            os.system(f'open "{file_path}"')
        else:  # Linux
            os.system(f'mpg123 "{file_path}"')

    def process_path(self):  # переписать, абсолютные пути не используются уже
        """Processing path to needed form"""
        if not os.path.exists(self.PATH_TO_CHECK_PATHFILE) or not self.sound_enabled:
            return
        paths = []
        try:
            self.file = open("path.txt", "r")
            for line in self.file:
                line = line.strip()
                if not line.startswith("#") and line:
                    if not os.path.isabs(line):
                        line = os.path.abspath(line)
                        paths.append(line)
                    else:
                        paths.append(line)
            if len(paths) == 2:

                self.path_to_rest = os.path.normpath(paths[0])
                self.path_to_work = os.path.normpath(paths[1])

            else:
                mb.showerror("Error", "You have more paths than two.")

        except Exception as err:
            mb.showerror("Error", "Error with path-reader\n" + str(err))
        else:
            print("Path read successfully.", self.path_to_rest, self.path_to_work)
        finally:
            self.file.close()


if __name__ == "__main__":
    mygui = MyGUI()
