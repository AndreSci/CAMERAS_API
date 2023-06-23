import time
import copy
import cv2
import threading

from misc.logger import Logger


TH_CAM_ERROR_LOCK = threading.Lock()


class ThreadVideoRTSP:
    """ Класс получения видео из камеры"""
    def __init__(self, cam_name: str, url: str):
        self.url = url
        self.cam_name = cam_name

        self.last_frame = b''
        self.no_frame = b''

        self.th_do_frame_lock = threading.Lock()

        self.allow_read_frame = True
        self.do_frame = False

        self.thread_is_alive = False
        self.thread_object = None

    def start(self, logger: Logger):
        # Если поток имеет флаг False создаем новый
        self.load_no_signal_pic()

        if not self.thread_is_alive:
            self.allow_read_frame = True

            with self.th_do_frame_lock:
                self.thread_is_alive = True
                self.thread_object = threading.Thread(target=self.__start, args=[logger, ], daemon=True)
                self.thread_object.start()
        else:
            logger.add_log(f"WARNING\tНе удалось запустить поток для камеры {self.cam_name} - {self.url}, "
                           f"занят другим делом.")

    def __start(self, logger: Logger):
        """ Функция подключения и поддержки связи с камерой """

        while self.allow_read_frame:
            logger.add_log(f"EVENT\tПопытка подключиться к камере: {self.cam_name} - {self.url}")
            capture = cv2.VideoCapture(self.url)

            if capture.isOpened():
                logger.add_log(f"SUCCESS\tThreadVideoRTSP.start()\t"
                                    f"Создано подключение к {self.cam_name} - {self.url}")

            frame_fail_cnt = 0

            try:
                while self.allow_read_frame:

                    if not capture.isOpened():
                        break

                    ret, frame = capture.read()  # читать всегда кадр
                    # cv2.imshow(self.cam_name, frame)
                    # cv2.waitKey(20)

                    with self.th_do_frame_lock:
                        if self.do_frame and ret:
                            # Начинаем сохранять кадр в файл
                            frame_fail_cnt = 0

                            # cv2.imwrite(self.url_frame, frame)

                            ret_jpg, frame_jpg = cv2.imencode('.jpg', frame)

                            if ret_jpg:
                                # Сохраняем кадр в переменную
                                self.last_frame = frame_jpg.tobytes()

                            self.do_frame = False

                        elif not ret:
                            # Собираем статистику неудачных кадров
                            time.sleep(0.02)
                            frame_fail_cnt += 1

                            # Если много неудачных кадров останавливаем поток и пытаемся переподключить камеру
                            if frame_fail_cnt == 50:
                                logger.add_log(f"WARNING\tThreadVideoRTSP.start()\t"
                                                f"{self.cam_name} - "
                                               f"Слишком много неудачных кадров, повторное подключение к камере.")
                                break
                        else:
                            frame_fail_cnt = 0
            except Exception as ex:
                logger.add_log(f"EXCEPTION\tThreadVideoRTSP.__start\t"
                               f"Исключение вызвала ошибка в работе с видео потоком для камеры {self.cam_name}: {ex}")

            logger.add_log(f"WARNING\tThreadVideoRTSP.start()\t"
                            f"{self.cam_name} - Камера отключена: {self.url}")

            capture.release()

    def load_no_signal_pic(self):
        with open('./cam_error.jpg', "rb") as file:
            self.no_frame = file.read()

    def take_frame(self, valid_frame: bool):
        """ Функция выгружает байт-код кадра из файла """
        global TH_CAM_ERROR_LOCK

        if valid_frame:
            with self.th_do_frame_lock:
                return copy.copy(self.last_frame)
        else:
            return self.no_frame

    def create_frame(self):
        """ Функция задает флаг на создание кадра в файл """
        ret_value = True

        with self.th_do_frame_lock:
            self.do_frame = True

        wait_time = 0

        # Цикл ожидает пока поток __start() изменит self.do_frame на False
        while True:

            with self.th_do_frame_lock:  # Блокируем потоки
                if not self.do_frame:
                    break
                elif wait_time == 10:  # Счетчик
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
