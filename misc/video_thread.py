import time
import datetime
import argparse

import cv2
import os
import threading
from misc.logger import Logger
from misc.ai import AiClass


TH_CAM_ERROR_LOCK = threading.Lock()


class ThreadVideoRTSP:
    """ Класс получения видео из камеры"""
    def __init__(self, cam_name: str, url: str, plate_recon: AiClass):
        self.url = url
        self.cam_name = cam_name

        self.last_frame = b''

        self.th_do_frame_lock = threading.Lock()

        self.allow_read_frame = True
        self.no_exception_in_read_frame = True  # Случай если было исключение в работе с получением кадра
        self.do_frame = False

        self.url_frame = f'./temp/frame_{self.cam_name}.jpg'

        self.thread_is_alive = False
        self.thread_object = None

        self.plate_recon = plate_recon

    def start(self, logger: Logger):

        if not self.thread_is_alive:
            self.allow_read_frame = True
            self.no_exception_in_read_frame = True

            logger.add_log(f"EVENT\tПопытка подключиться к камере: {self.cam_name} - {self.url}")

            with self.th_do_frame_lock:
                self.thread_object = threading.Thread(target=self.__start, args=[logger, ])
                self.thread_object.start()
                self.thread_is_alive = True
        else:
            logger.add_log(f"WARNING\tНе удалось запустить поток для камеры {self.cam_name} - {self.url}, "
                           f"занят другим делом.")

    def __start(self, logger: Logger):
        """ Функция подключения и поддержки связи с камерой """

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

                with self.th_do_frame_lock:
                    if self.do_frame and ret:
                        # Начинаем сохранять кадр в файл
                        frame_fail_cnt = 0

                        # cv2.imwrite(self.url_frame, frame)
                        # Дорисовываем квадрат на кадре
                        self.plate_recon.find_plate(frame)

                        frame = cv2.resize(frame, (0, 0), fx=0.9, fy=0.9)
                        # Преобразуем кадр в .jpg
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
                                           f"Слишком много неудачных кадров, повторное переподключение к камере.")
                            break
                    else:
                        frame_fail_cnt = 0
        except Exception as ex:
            logger.add_log(f"EXCEPTION\tThreadVideoRTSP.__start\t"
                           f"Исключение вызвала ошибка в работе с видео потоком для камеры {self.cam_name}: {ex}")
            self.no_exception_in_read_frame = False

        logger.add_log(f"WARNING\tThreadVideoRTSP.start()\t"
                        f"{self.cam_name} - Камера отключена: {self.url}")
        self.thread_is_alive = False

        try:
            # Освобождаем
            capture.release()
        except Exception as ex:
            logger.add_log(f"EXCEPTION\tThreadVideoRTSP.start()\t"
                            f"{self.cam_name} - Исключение вызвал метод освобождения capture.release(): {ex}")

        # Если разрешено чтение кадров переподключаем камеру
        if self.allow_read_frame:
            self.start(logger)
        # cv2.destroyAllWindows()

    def stop(self):
        """ Остановить бесконечный цикл __start() """
        self.allow_read_frame = False

    def take_frame(self, valid_frame: bool):
        """ Функция выгружает байт-код кадра из файла """
        global TH_CAM_ERROR_LOCK

        if valid_frame:
            with self.th_do_frame_lock:
                # with open(self.url_frame, "rb") as file:
                #     frame = file.read()
                return self.last_frame
        else:
            with TH_CAM_ERROR_LOCK:
                with open('./cam_error.jpg', "rb") as file:
                    frame = file.read()

        return frame

    def create_frame(self, logger: Logger):
        """ Функция задает флаг на создание кадра в файл """
        ret_value = True

        try:
            with self.th_do_frame_lock:

                if self.thread_object.is_alive:
                    self.do_frame = True
                else:
                    self.thread_is_alive = False
                    self.start(logger)

        except Exception as ex:
            logger.add_log(f"EXCEPTION\tThreadVideoRTSP.create_frame\tИсключение вызвала попытка проверить поток: {ex}")

        wait_time = 0

        # Цикл ожидает пока поток __start() изменит self.do_frame на False
        while True:

            with self.th_do_frame_lock:  # Блокируем потоки
                if not self.do_frame:
                    break
                elif wait_time == 40:  # Счетчик
                    ret_value = False
                    break

            time.sleep(0.03)
            wait_time += 1

        return ret_value


def create_cams_threads(cams_from_settings: dict, logger: Logger, plate_recon: AiClass) -> dict:
    """ Функция создает словарь с объектами класса ThreadVideoRTSP и запускает от их имени потоки """
    cameras = dict()

    for key in cams_from_settings:
        cameras[key] = ThreadVideoRTSP(str(key), cams_from_settings[key], plate_recon)
        cameras[key].start(logger)

    return cameras
