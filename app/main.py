import time
import ctypes
from misc.video_thread import create_cams_threads, ThreadVideoRTSP
from flask import Flask, request, jsonify, Response, make_response
import datetime

from misc.logger import Logger
from misc.utility import SettingsIni
from misc.allow_ip import AllowedIP

from database.add_event import EventDB
from database.cameras import CamerasDB

import logging
from misc.consts import ERROR_ACCESS_IP, ERROR_READ_REQUEST, ERROR_ON_SERVER, CameraClass
from routes.frame import frame_blue
from routes.allow_ip import allow_ip_blue

OLD_CAM_LIST = list()

app = Flask(__name__)  # Create flask app
app.config['JSON_AS_ASCII'] = False
# Block for message from flask
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app.register_blueprint(frame_blue)
app.register_blueprint(allow_ip_blue)


def web_flask(logger: Logger, settings_ini: SettingsIni):
    """ Главная функция создания сервера Фласк. """
    # Получаем настройки
    set_ini = settings_ini.take_settings()

    if set_ini['cameras_from_db'] == '1':
        res = CamerasDB().take_cameras()
        set_ini['CAMERAS'] = res.get('DATA')

    allow_ip = AllowedIP()
    allow_ip.read_file(logger)

    logger.add_log(f"SUCCESS\tweb_flask\tСервер CAM_API_Flask начал свою работу")  # log

    CameraClass.update(create_cams_threads(set_ini['CAMERAS']))


def main():

    # Подгружаем данные из settings.ini
    settings = SettingsIni()
    result = settings.create_settings()

    fail_col = '\033[91m'
    # end_c = '\033[0m'

    # Проверка успешности загрузки данных
    if not result["result"]:
        print(f"{fail_col}")
        print(f"Ошибка запуска сервиса - {result['desc']}")
        input()
        raise Exception("Service error")

    port = settings.settings_ini["port"]

    # Меняем имя терминала
    # ctypes.windll.kernel32.SetConsoleTitleW(f"RTSP - REST CAM_API port: {port}")

    # Обьявляем логирование
    logger = Logger(settings.take_log_path())

    web_flask(logger, settings)
    set_ini = settings.take_settings()

    # RUN SERVER FLASK  ------
    app.run(debug=False, host=set_ini["host"], port=int(set_ini["port"]))


if __name__ == '__main__':
    main()
