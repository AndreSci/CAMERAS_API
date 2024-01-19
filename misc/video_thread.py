# Стабильно работает с 10 камерами если в настройках камеры стоит частота кадров 14
# Stable work with 10 cameras when cameras settings set FPS = 14
import time
import copy
import cv2
import threading

from misc.logger import Logger


TH_CAM_ERROR_LOCK = threading.Lock()
OLD_CAM_LIST = list()
logger_vt = Logger()

cv2.CAP_PROP_BUFFERSIZE = 4
cv2.CAP_PROP_FPS = 14

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

    def start(self):
        # Если поток имеет флаг False создаем новый
        self.load_no_signal_pic()

        if not self.thread_is_alive:
            with self.th_do_frame_lock:
                self.thread_is_alive = True
                self.thread_object = threading.Thread(target=self.__start, args=[logger_vt, ], daemon=True)
                self.thread_object.start()
        else:
            logger_vt.add_log(f"WARNING\tНе удалось запустить поток для камеры {self.cam_name} - {self.url}, "
                           f"занят другим делом.")

    def __start(self, logger: Logger):
        """ Функция подключения и поддержки связи с камерой """

        while self.allow_read_cam:
            time.sleep(1)
            self.allow_read_frame.set(False)
            logger.event(f"Попытка подключиться к камере: {self.cam_name} - {self.url}")

            capture = cv2.VideoCapture(self.url)
            capture.set(cv2.CAP_PROP_BUFFERSIZE, 4)


            if capture.isOpened():
                self.allow_read_frame.set(True)
                logger.event(f"Создано подключение к {self.cam_name} - {self.url}")

            frame_fail_cnt = 0

            try:
                while self.allow_read_frame.get():

                    if capture.isOpened():
                        ret, frame = capture.read()  # читать всегда кадр
                        # cv2.imshow(self.cam_name, frame)
                        # cv2.waitKey(20)
                        if self.do_frame.get() and ret:
                            # Начинаем сохранять кадр
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
                            # Расчет на скорость видео потока не выше 30 кадров
                            time.sleep(0.03)
                            frame_fail_cnt += 1

                            # Если много неудачных кадров останавливаем поток и пытаемся переподключить камеру
                            if frame_fail_cnt == 150:
                                logger.warning(f"{self.cam_name} - "
                                               f"Слишком много неудачных кадров, повторное подключение к камере.")
                                break
                        else:
                            frame_fail_cnt = 0

                    # TODO продолжаем тестировать воздействие time.sleep на получение кадров
                    time.sleep(0.0005)

            except Exception as ex:
                logger.exception(f"Исключение вызвала ошибка в работе с видео потоком для камеры {self.cam_name}: {ex}")

            logger.warning(f"{self.cam_name} - Камера отключена: {self.url}")

            capture.release()

        self.thread_is_alive = False

    def load_no_signal_pic(self):
        """ Функция подгружает кадр с надписью NoSignal """
        with open('./cam_error.jpg', "rb") as file:
            self.no_frame = file.read()

    def take_frame(self, valid_frame: bool) -> bytes:
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

    def create_frame(self):
        """ Функция задает флаг на создание кадра """
        ret_value = True

        self.do_frame.set(True)

        wait_time = 0

        # Проверяем жив ли поток для связи с камерой
        if not self.thread_object.is_alive:
            logger_vt.add_log(f"ERROR\tThreadVideoRTSP.create_frame()1\t"
                           f"Поток обработки кадров для {self.cam_name} не найден.")
            self.start()

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

    def stop(self) -> bool:
        """ Ожидает завершения потока 2 секунды после чего отправляет ответ False """

        try:
            self.allow_read_cam = False
            self.allow_read_frame.set(False)

            index = 0

            while self.thread_is_alive:
                time.sleep(0.01)

                if index == 200:
                    logger_vt.warning(f"Не удалось дождаться завершения работы камеры: {self.cam_name} : {self.url} "
                                   f"- отправлено "
                                   f"в список старых камер")

                    return False
                index += 1
            return True
        except Exception as ex:
            logger_vt.exception(f"Исключение вызвало: {ex}")

        return False


def create_cams_threads(new_cams_db: dict, old_cams: dict = None) -> dict:
    """ Функция создает словарь с объектами класса ThreadVideoRTSP и запускает от их имени потоки """
    global OLD_CAM_LIST

    new_cams = dict()
    copy_old_cams = dict()
    del_cams = dict()

    if old_cams:  # Для обновления списка камер

        copy_old_cams = old_cams.copy()

        del_old_cams(copy_old_cams, new_cams_db, old_cams)

        compare_cams(copy_old_cams, del_cams, new_cams, new_cams_db)

    else:
        new_cams = new_cams_db


    # Создаем потоки для камер
    for key in new_cams:
        copy_old_cams[key] = ThreadVideoRTSP(str(key), new_cams[key])
        copy_old_cams[key].start()

    if new_cams:
        logger_vt.event(f"Добавлены камеры: {new_cams}")
        logger_vt.event(f"Удалены камеры: {del_cams}")
    else:
        logger_vt.event(f"Новых камер не обнаружено!")

    return copy_old_cams


def compare_cams(copy_old_cams, del_cams, new_cams, new_cams_db):
    """ Сравниваем камеры по параметрам, если изменился адрес к камере, отключаем камеру """
    global OLD_CAM_LIST

    for cam in new_cams_db:
        if cam in copy_old_cams:
            # Сравниваем url камер и останавливаем камеры если они отличаются
            if copy_old_cams[cam].url != new_cams_db[cam]:

                res_stop = copy_old_cams[cam].stop()
                # Если не дождался завершения работы потока
                if not res_stop:
                    OLD_CAM_LIST.append(copy_old_cams[cam])

                del_cams[cam] = copy_old_cams[cam].url

                # Удаляем камеру из общего словаря потоков камер
                copy_old_cams.pop(cam)

                # Добавляем в новый словарь для дальнейшего создания потоков камер
                new_cams[cam] = new_cams_db[cam]
        else:
            new_cams[cam] = new_cams_db[cam]


def del_old_cams(copy_old_cams, new_cams_db, old_cams):
    """ Отключаем все камеры которых нет в новом списке """
    global OLD_CAM_LIST

    for cam in old_cams:
        # Завершаем все камеры которых нет в списке
        if cam not in new_cams_db:
            res_stop = copy_old_cams[cam].stop()
            # Если не дождался завершения работы потока
            if not res_stop:
                OLD_CAM_LIST.append(copy_old_cams[cam])
            copy_old_cams.pop(cam)
