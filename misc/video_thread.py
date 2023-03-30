import time
import datetime

import cv2
import os
import threading


TH_CAM_ERROR_LOCK = threading.Lock()


class ThreadVideoRTSP:
    """ Класс получения видео из камеры"""
    def __init__(self, cam_name: str, url: str):
        self.url = url
        self.cam_name = cam_name

        self.last_frame = b''

        self.th_do_frame_lock = threading.Lock()

        self.allow_read_frame = True
        self.do_frame = False

        self.url_frame = f'./temp/frame_{self.cam_name}.jpg'

        self.thread_is_alive = False
        self.thread_object = None

    def start(self):

        if not self.thread_is_alive:
            self.allow_read_frame = True

            print(f"EVENT\tПопытка подключиться к камере: {self.cam_name} - {self.url}")

            self.thread_object = threading.Thread(target=self.__start)
            self.thread_object.start()
            self.thread_is_alive = True
        else:
            print("WARNING\tНе удалось запустить поток, занят другим делом")

    def __start(self):
        """ Функция подключения и поддержки связи с камерой """
        capture = cv2.VideoCapture(self.url)

        if capture.isOpened():
            print(f"SUCCESS\tThreadVideoRTSP.start()\t"
                  f"Создано подключение к {self.cam_name} - {self.url}")

        frame_fail_cnt = 0

        while self.allow_read_frame:

            if not capture.isOpened():
                break

            ret, frame = capture.read()  # читать всегда кадр
            # cv2.imshow('frame', frame)

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
                        print(f"WARNING\tThreadVideoRTSP.start()\t"
                              f"{self.cam_name} - Слишком много неудачных кадров, повторное переподключение к камере.")
                        break
                else:
                    frame_fail_cnt = 0

        print(f"WARNING\tThreadVideoRTSP.start()\t"
              f"{self.cam_name} - Камера отключена: {self.url}")
        self.thread_is_alive = False

        try:
            # Освобождаем
            capture.release()
        except Exception as ex:
            print(f"EXCEPTION\tThreadVideoRTSP.start()\t"
                  f"{self.cam_name} - Исключение вызвал метод освобождения capture.release(): {ex}")

        # Если разрешено чтение кадров переподключаем камеру
        if self.allow_read_frame:
            self.start()
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
                elif wait_time == 40:  # Счетчик
                    ret_value = False
                    break

            time.sleep(0.03)
            wait_time += 1

        return ret_value


def create_cams_threads(cams_from_settings: dict) -> dict:
    """ Функция создает словарь с объектами класса ThreadVideoRTSP и запускает от их имени потоки """
    cameras = dict()

    for key in cams_from_settings:
        cameras[key] = ThreadVideoRTSP(str(key), cams_from_settings[key])
        cameras[key].start()

    return cameras
