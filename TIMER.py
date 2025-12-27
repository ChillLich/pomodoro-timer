from pathlib import Path

from keyboard import send as send_to_system_api
from pygame import mixer

"""🧪 Тестирование:
Протестируй следующие сценарии:

Автоматический переход - таймер сам переключает фазы

Ручное переключение - кнопки вперед/назад

Пауза и возобновление - в разных фазах

Сброс - с разными пресетами

Звуки - включай/выключай sound_player и media_api

Long break - после последнего цикла"""


class Timer:
    def __init__(self, settings_manager):
        self.settings = settings_manager
        self.MINUT = 60

        # Состояние таймера
        self.process_status = 4  # 1=rest, 2=work, 3=pause from rest, 4=pause from work
        self.seconds_till_next_phase = 0
        self.cycle_counter = 0
        self.id_to_cancel = None

        # Callback для обновления GUI
        self.update_callback = None
        self.tick_callback = None

        # Инициализация миксера
        mixer.init()

        # Регистрирация callback в settings manager
        self.settings.add_callback(self._on_settings_changed)

        # Загрузка начальных значений
        self._load_settings()

        # Устанавливаем начальное время
        self.seconds_till_next_phase = int(self.MINUT * self.list_with_min_values[0])

    def _load_settings(self):
        """Загрузка всех настроек из SettingsManager"""
        # Получаем текущий пресет
        preset_name = self.settings.get("timer.current_preset", "medium")

        # Получаем значения из текущего пресета
        self.list_with_min_values = self.settings.get(f"timer.{preset_name}", [25, 5, 15, 4])

        # Если это user пресет и он пустой, используем medium как fallback
        if preset_name == "user" and not self.list_with_min_values:
            self.list_with_min_values = self.settings.get("timer.medium", [25, 5, 15, 4])

        # Получаем пути.
        path_to_work_str = self.settings.get("system.path_to_focus_track", "work.mp3")
        path_to_rest_str = self.settings.get("system.path_to_rest_track", "rest.mp3")

        self.path_to_work = Path(path_to_work_str)
        self.path_to_rest = Path(path_to_rest_str)

        # Если пути относительные - преобразуем в абсолютные
        # (относительно текущей рабочей директории)
        if not self.path_to_work.is_absolute():
            self.path_to_work = self.path_to_work.resolve()
        if not self.path_to_rest.is_absolute():
            self.path_to_rest = self.path_to_rest.resolve()

    def _on_settings_changed(self, key: str, value):
        """Callback для получения уведомлений об изменении настроек"""
        if key.startswith("timer.") or key in [
            "system.path_to_focus_track",
            "system.path_to_rest_track",
        ]:
            self._load_settings()
        # Сбрасываем только если изменены настройки таймера
        if key.startswith("timer."):
            self.reset()

    def set_gui_callbacks(self, update_callback, tick_callback):
        """Установка callback функций для обновления GUI"""
        self.update_callback = update_callback
        self.tick_callback = tick_callback

    def start(self):
        """Запуск/возобновление таймера"""
        if self.process_status == 3:
            self.process_status = 1
        elif self.process_status == 4:
            self.process_status = 2

        self._handle_audio_api(unpause=True)

        self._schedule_tick()

    def pause(self):
        """Пауза таймера"""
        if self.id_to_cancel and self.tick_callback:
            self._handle_audio_api(pause=True)
            # Это конструкция идентична if/else с другими значениями в start(), но выебистая :)
            self.process_status = {1: 3, 2: 4}.get(self.process_status, self.process_status)
            self._call_update()

    def reset(self):
        """Сброс таймера"""
        self._cancel_tick()
        self._stop_audio()

        self.process_status = 4
        self.cycle_counter = 0
        self.seconds_till_next_phase = int(self.MINUT * self.list_with_min_values[0])
        self._call_update()
        return True

    def count_tick(self):
        """
        Необходимо вызывать каждую секунду для отсчета.
        Реализация отсчета через такой вызов позволяет управлять таймером целиком из GUI.
        Если необходимо вычесть секунду не сразу, то вызывать self._schedule_tick().
        Однако _schedule_tick не отсчитывает секунды
        """
        if self.seconds_till_next_phase > 0:
            self.seconds_till_next_phase -= 1
        else:
            # Здесь тик планируется итак. Поэтому schedule_tick=True не нужен
            self.step_in_phase()
        self._schedule_tick()

    def get_status_info(self):
        """Возвращает информацию о текущем статусе для GUI"""
        mins, secs = (
            self.seconds_till_next_phase // self.MINUT,
            self.seconds_till_next_phase % self.MINUT,
        )

        # Определение типа статуса
        if self.process_status in (3, 4):
            status_type = "pause"
        elif self.process_status == 2:
            status_type = "focus"
        else:  # 1
            status_type = "rest"

        return {
            "minutes": f"{mins}:{secs:02d}",
            "status_type": status_type,
            "cycle_counter": self.cycle_counter,
            "max_cycles": self.list_with_min_values[3],
        }

    def step_in_phase(self, schedule_tick=False, step_back=False):
        """
        Перемещает фазу. По-умолчанию вперед, а назад при заданных аргументах.
        Для перемещения назад необходимо передать:
        schedule_tick=True, step_back=True.
        Аргумент schedule_tick=True необходим всегда когда метод вызывается вручную.
        """
        if schedule_tick:
            self._cancel_tick()  # отменяет тик если он есть

        # Сменить статус если было на паузе. Гарантирует корректную работу с паузой.
        self.process_status = {3: 1, 4: 2}.get(self.process_status, self.process_status)

        self._transition_phase()
        self._calc_cycle_step(step_back=step_back)

        # Проверяем настройку pause_on_end_enabled при каждом использовании
        if self.settings.get("system.pause_on_end_enabled", False):
            self.pause()

        if schedule_tick:
            self._schedule_tick()
        else:
            self._call_update()

    def get_timer_values(self):
        """Получение текущих значений таймера, использовать только для отладки"""
        return self.list_with_min_values.copy()

    # Вспомогательные методы
    def _handle_audio_api(self, unpause=False, pause=False, play_track=None):
        """Обработка аудио операций

        Args:
            unpause: Разблокировать миксер (только для start)
            pause: Поставить на паузу таймер и аудио
            play_track: Воспроизвести указанный трек ('work' или 'rest')
        """
        try:
            if self.settings.get("system.media_api_enabled", True):
                send_to_system_api("play/pause media")

            if unpause:
                mixer.music.unpause()

            if pause:
                self._cancel_tick()
                if mixer.music.get_busy():
                    mixer.music.pause()

            if play_track:
                self._play_track(play_track)

        except Exception as err:
            context = "start" if unpause else "pause"
            if play_track:
                context = f"play_{play_track}"
            print(f"Error in {context}:\n{err}")

    def _play_track(self, track_type):
        """Воспроизведение указанного трека"""
        if not self.settings.get("system.sound_player_enabled", False):
            return

        self._stop_audio()

        file_path = self.path_to_work if track_type == "work" else self.path_to_rest

        if not file_path.exists():
            print(f"Audio file not found: {file_path}")
            return

        try:
            mixer.music.load(file_path)
            mixer.music.play()
        except Exception as err:
            print(f"Audio play error: {err}")

    def _transition_phase(self):
        """Переключение между фазами"""
        if self.process_status == 1:  # REST -> WORK
            self.process_status = 2
            self.cycle_counter += 1
            self.seconds_till_next_phase = int(self.list_with_min_values[0] * self.MINUT)
            self._handle_audio_api(play_track="work")
        elif self.process_status == 2:  # WORK -> REST
            self.process_status = 1
            self.seconds_till_next_phase = int(self.list_with_min_values[1] * self.MINUT)
            if self.cycle_counter == self.list_with_min_values[3] - 1:
                self.seconds_till_next_phase = int(self.list_with_min_values[2] * self.MINUT)
            self._handle_audio_api(play_track="rest")

    def _calc_cycle_step(self, step_back=False):
        """Сдвиг счетчика циклов при пересечении границы циклов."""
        # Вычитать единицу у счетчика циклов нужно только при переходе назад от W к R: R<-W
        # Статус уже переключен, т.к. _transition_phase вызывается раньше!
        if step_back and self.process_status == 1:
            self.cycle_counter -= 1
        if self.cycle_counter >= self.list_with_min_values[3] - 1 and self.process_status == 1:
            self.cycle_counter = 0
        elif self.cycle_counter < 0 and self.process_status == 2:
            self.cycle_counter = self.list_with_min_values[3] - 1
            # Этот вариант озвращат всегда большой перерыв
            self.seconds_till_next_phase = int(self.list_with_min_values[2] * self.MINUT)

    def _cancel_tick(self):
        """Отменить таймер"""
        if self.id_to_cancel and self.tick_callback:
            self.tick_callback("cancel", self.id_to_cancel)

    def _stop_audio(self):
        """Остановить музыку"""
        if mixer.music.get_busy():
            mixer.music.stop()

    def _schedule_tick(self):
        """
        Спланировать следующий тик, не считает их.
        Для подсчта использовать self.count_tick().
        """
        if self.tick_callback:
            self.id_to_cancel = self.tick_callback("schedule", 1000)
        self._call_update()

    def _call_update(self):
        """Вызвать callback для обновления GUI"""
        if self.update_callback:
            self.update_callback()

    def __del__(self):
        """Удаление таймера - отписываемся от callback"""
        if self.settings and hasattr(self.settings, "remove_callback"):
            self.settings.remove_callback(self._on_settings_changed)
