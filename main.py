from misc.video_thread import create_cams_threads
from flask import Flask, request, jsonify, Response
import datetime

from misc.logger import Logger
from misc.utility import SettingsIni
from misc.allow_ip import AllowedIP

from database.add_event import EventDB

import logging

ERROR_ACCESS_IP = 'access_block_ip'
ERROR_READ_REQUEST = 'error_read_request'
ERROR_ON_SERVER = 'server_error'


def web_flask(logger: Logger, settings_ini: SettingsIni):
    """ Главная функция создания сервера Фласк. """

    app = Flask(__name__)  # Объявление сервера

    app.config['JSON_AS_ASCII'] = False

    # Блокируем сообщения фласк
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    set_ini = settings_ini.take_settings()

    allow_ip = AllowedIP()
    allow_ip.read_file(logger)

    logger.add_log(f"SUCCESS\tweb_flask\tСервер CAM_API_Flask начал свою работу")  # log

    cam_list = create_cams_threads(set_ini['CAMERAS'], logger)

    # IP FUNCTION

    @app.route('/DoAddIp', methods=['POST'])
    def add_ip():
        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        # logger.add_log(f"EVENT\tDoAddIp\tзапрос от ip: {user_ip}")

        if not allow_ip.find_ip(user_ip, logger, 2):  # Устанавливаем activity_lvl=2 для проверки уровня доступа
            json_replay["DESC"] = "Ошибка доступа по IP"
        else:

            if request.is_json:
                json_request = request.json

                new_ip = json_request.get("ip")
                activity = int(json_request.get("activity"))

                allow_ip.add_ip(new_ip, logger, activity)

                json_replay["RESULT"] = "SUCCESS"
                json_replay["DESC"] = f"IP - {new_ip} добавлен с доступом {activity}"
            else:
                logger.add_log(f"ERROR\tDoCreateGuest\tНе удалось прочитать Json из request")
                json_replay["DESC"] = "Ошибка. Не удалось прочитать Json из request."

        return jsonify(json_replay)

    @app.route('/action.do', methods=['GET'])
    def take_frame():
        """ Запрашиваем у потока последний кадр """

        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr

        # Проверяем разрешён ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = ERROR_ACCESS_IP

            logger.add_log(f"WARNING\ttake_frame()\tОшибка доступа по ip: {user_ip}, ip не имеет разрешения.")
        else:
            # получаем данные из параметров запроса
            res_request = request.args

            cam_name = str(res_request.get('video_in'))
            cam_name = 'cam' + cam_name[cam_name.find(':') + 1:]

            try:
                # Команда на запись кадра в файл
                valid_frame = cam_list[cam_name].create_frame(logger)
                # Получить кадр
                frame = cam_list[cam_name].take_frame(valid_frame)
            except Exception as ex:
                frame = ''
                logger.add_log(f"EXCEPTION\ttake_frame()\tНе удалось получить кадр из камеры: {ex}")

            return Response(frame, mimetype='image/jpeg')

        return jsonify(json_replay)

    @app.route('/action.save', methods=['GET'])
    def save_frame_asterisk():
        """ Запрашиваем у потока последний кадр и сохраняем его в папку согласно настройкам settings.ini """

        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.event(f"Обращение к rtsp от адреса {user_ip}")
        # Проверяем разрешён ли доступ для IP
        # if not allow_ip.find_ip(user_ip, logger):
        #     json_replay["DESC"] = ERROR_ACCESS_IP
        #
        #     logger.warning(f"Ошибка доступа по ip: {user_ip}, ip не имеет разрешения.")
        # else:
        # получаем данные из параметров запроса
        res_request = request.args
        # print(res_request)
        cam_name = str(res_request.get('cam_number'))
        cam_name = 'cam' + cam_name[cam_name.find(':') + 1:]
        caller_id = str(res_request.get('caller_id'))

        try:
            # Команда на запись кадра
            valid_frame = cam_list[cam_name].create_frame(logger)
            # Получить кадр
            frame = cam_list[cam_name].take_frame(valid_frame)
            # Получаем дату и генерируем полный путь к файлу
            date_time = str(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
            file_name = f"{cam_name}-{caller_id}-{date_time}.jpg"
            file_path = f"{set_ini['photo_path']}{file_name}"

            with open(file_path, 'wb') as file:
                # Сохраняем кадр в файл
                file.write(frame)

            logger.event(f"Успешно создан файл: {file_name}")

            # Добавляем событие в БД
            db_add = EventDB.add_photo(caller_id, cam_name, file_name)

            if db_add:
                json_replay['DATA'] = {"file_name": file_name}
                json_replay["RESULT"] = "SUCCESS"
            else:
                logger.warning(f"Не удалось внести данные в БД: {res_request}")
                json_replay['DESC'] = "Не удалось внести данные в БД"

        except Exception as ex:
            logger.exception(f"Не удалось получить/сохранить кадр из камеры: {ex}")

        return jsonify(json_replay)


    # RUN SERVER FLASK  ------
    app.run(debug=False, host=set_ini["host"], port=int(set_ini["port"]))
