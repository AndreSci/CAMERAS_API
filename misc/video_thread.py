import time
import copy
import cv2
import threading

from misc.logger import Logger


TH_CAM_ERROR_LOCK = threading.Lock()


class ThreadAccessControl:
    def __init__(self):
        self.allow_read_frame = False
        self.lock = threading.Lock()

    def get(self) -> bool:
        with self.lock:
            return self.allow_read_frame

    def set(self, val: bool) -> None:
        with self.lock:
            self.allow_read_frame = val


class ThreadVideoRTSP:
    """ Класс получения видео из камеры"""
    def __init__(self, cam_name: str, url: str):
        self.url = url
        self.cam_name = cam_name

        self.last_frame = b''
        self.no_frame = b''

        self.th_do_frame_lock = threading.Lock()

        self.allow_read_frame = ThreadAccessControl()
        self.allow_read_cam = True
        self.do_frame = ThreadAccessControl()

        self.thread_is_alive = False
        self.thread_object = threading.Thread

        self.miss_frame_index = 0

        # FPS = 1/X
        # X = desired FPS
        self.FPS = 1/30
        self.FPS_MS = int(self.FPS * 1000)

    def start(self, logger: Logger):
        # Если поток имеет флаг False создаем новый
        self.load_no_signal_pic()

        if not self.thread_is_alive:
            with self.th_do_frame_lock:
                self.thread_is_alive = True
                self.thread_object = threading.Thread(target=self.__start, args=[logger, ], daemon=True)
                self.thread_object.start()
        else:
            logger.add_log(f"WARNING\tНе удалось запустить поток для камеры {self.cam_name} - {self.url}, "
                           f"занят другим делом.")

    def __start(self, logger: Logger):
        """ Функция подключения и поддержки связи с камерой """

        while self.allow_read_cam:
            self.allow_read_frame.set(False)
            logger.add_log(f"EVENT\tThreadVideoRTSP.start()1\t"
                           f"Попытка подключиться к камере: {self.cam_name} - {self.url}")
            capture = cv2.VideoCapture(self.url)
            capture.set(cv2.CAP_PROP_BUFFERSIZE, 4)

            if capture.isOpened():
                self.allow_read_frame.set(True)
                logger.add_log(f"SUCCESS\tThreadVideoRTSP.start()2\t"
                                    f"Создано подключение к {self.cam_name} - {self.url}")

            frame_fail_cnt = 0

            try:
                while self.allow_read_frame.get():

                    if capture.isOpened():
                        ret, frame = capture.read()  # читать всегда кадр
                        # cv2.imshow(self.cam_name, frame)
                        # cv2.waitKey(20)

                        if self.do_frame.get() and ret:
                            # Начинаем сохранять кадр в файл
                            frame_fail_cnt = 0

                            # cv2.imwrite(self.url_frame, frame)

                            ret_jpg, frame_jpg = cv2.imencode('.jpg', frame)

                            if ret_jpg:
                                # Сохраняем кадр в переменную
                                with self.th_do_frame_lock:
                                    self.last_frame = frame_jpg.tobytes()

                            self.do_frame.set(False)

                        elif not ret:
                            # Собираем статистику неудачных кадров
                            time.sleep(0.02)
                            frame_fail_cnt += 1

                            # Если много неудачных кадров останавливаем поток и пытаемся переподключить камеру
                            if frame_fail_cnt == 50:
                                logger.add_log(f"WARNING\tThreadVideoRTSP.start()3\t"
                                                f"{self.cam_name} - "
                                               f"Слишком много неудачных кадров, повторное подключение к камере.")
                                break
                        else:
                            frame_fail_cnt = 0

                    time.sleep(self.FPS)

            except Exception as ex:
                logger.add_log(f"EXCEPTION\tThreadVideoRTSP.start()4\t"
                               f"Исключение вызвала ошибка в работе с видео потоком для камеры {self.cam_name}: {ex}")

            logger.add_log(f"WARNING\tThreadVideoRTSP.start()5\t"
                            f"{self.cam_name} - Камера отключена: {self.url}")

            capture.release()

    def load_no_signal_pic(self):
        """ Функция подгружает кадр с надписью NoSignal """
        with open('./cam_error.jpg', "rb") as file:
            self.no_frame = file.read()

    def take_frame(self, valid_frame: bool):
        """ Функция выгружает байт-код кадра из файла """
        global TH_CAM_ERROR_LOCK

        if valid_frame:
            with self.th_do_frame_lock:
                return copy.copy(self.last_frame)
        else:
            # Добавляем в счетчик неудачных кадров
            self.miss_frame_index += 1
            # Если счетчик неудачных кадров дошел до заданного значение блокируем чтение кадров
            if self.miss_frame_index == 100:
                self.allow_read_frame.set(False)

            return self.no_frame

    def create_frame(self, logger: Logger):
        """ Функция задает флаг на создание кадра в файл """
        ret_value = True

        self.do_frame.set(True)

        wait_time = 0

        # Проверяем жив ли поток для связи с камерой
        if not self.thread_object.is_alive:
            logger.add_log(f"ERROR\tThreadVideoRTSP.create_frame()1\t"
                           f"Поток обработки кадров для {self.cam_name} не найден.")
            self.start(logger)

        # Цикл ожидает пока поток __start() изменит self.do_frame на False
        # Время ожидание 450 мс. (в среднем получение одного кадра должно быть ~30мс.)
        # На практике ожидание кадра меньше 450 мс. вызывает частые кадры "NO SINGAL"
        while True:

            if not self.do_frame.get():
                break
            elif wait_time == 15:  # Счетчик
                ret_value = False
                break

            time.sleep(0.03)
            wait_time += 1

        return ret_value


def create_cams_threads(cams_from_settings: dict, logger: Logger) -> dict:
    """ Функция создает словарь с объектами класса ThreadVideoRTSP и запускает от их имени потоки """
    cameras = dict()

    for key in cams_from_settings:
        cameras[key] = ThreadVideoRTSP(str(key), cams_from_settings[key])
        cameras[key].start(logger)

    return cameras
