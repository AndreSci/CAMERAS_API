from misc.video_thread import create_cams_threads, ThreadVideoRTSP
from flask import Flask, request, jsonify, Response, make_response
import datetime

from misc.logger import Logger
from misc.utility import SettingsIni
from misc.allow_ip import AllowedIP

from database.add_event import EventDB
from database.cameras import CamerasDB

import logging

ERROR_ACCESS_IP = 'access_block_ip'
ERROR_READ_REQUEST = 'error_read_request'
ERROR_ON_SERVER = 'server_error'

CAM_DICT = dict()
OLD_CAM_LIST = list()
REQUEST_DICT = {"RESULT": "ERROR", "STATUS_CODE": 400, "DESC": '', "DATA": dict()}


def web_flask(logger: Logger, settings_ini: SettingsIni):
    """ Главная функция создания сервера Фласк. """
    global CAM_DICT

    app = Flask(__name__)  # Объявление сервера

    app.config['JSON_AS_ASCII'] = False

    # Блокируем сообщения фласк
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # Получаем настройки
    set_ini = settings_ini.take_settings()

    if set_ini['cameras_from_db'] == '1':
        res = CamerasDB().take_cameras()
        set_ini['CAMERAS'] = res.get('DATA')

    allow_ip = AllowedIP()
    allow_ip.read_file(logger)

    logger.add_log(f"SUCCESS\tweb_flask\tСервер CAM_API_Flask начал свою работу")  # log

    CAM_DICT = create_cams_threads(set_ini['CAMERAS'])

    # IP FUNCTION

    @app.route('/DoAddIp', methods=['POST'])
    def add_ip():
        json_replay = REQUEST_DICT

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
                json_replay['STATUS_CODE'] = 200
                json_replay["DESC"] = f"IP - {new_ip} добавлен с доступом {activity}"
            else:
                logger.add_log(f"ERROR\tDoCreateGuest\tНе удалось прочитать Json из request")
                json_replay["DESC"] = "Ошибка. Не удалось прочитать Json из request."

        return jsonify(json_replay)

    @app.route('/action.do', methods=['GET'])
    def take_frame():
        """ Запрашиваем у потока последний кадр """

        json_replay = REQUEST_DICT

        user_ip = request.remote_addr

        # Проверяем разрешён ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = ERROR_ACCESS_IP

            logger.add_log(f"WARNING\ttake_frame()\tОшибка доступа по ip: {user_ip}, ip не имеет разрешения.")
        else:
            # получаем данные из параметров запроса
            res_request = request.args

            cam_name = str(res_request.get('video_in'))
            cam_name = 'CAM' + cam_name[cam_name.find(':') + 1:]

            try:
                # Команда на запись кадра в файл
                valid_frame = CAM_DICT[cam_name].create_frame()
                # Получить кадр
                frame = CAM_DICT[cam_name].take_frame(valid_frame)
            except Exception as ex:
                frame = ''
                logger.add_log(f"EXCEPTION\ttake_frame()\tНе удалось получить кадр из камеры: {ex}")

            return Response(frame, mimetype='image/jpeg')

        return jsonify(json_replay)

    @app.route('/action.save', methods=['GET'])
    def save_frame_asterisk():
        """ Запрашиваем у потока последний кадр и сохраняем его в папку согласно настройкам settings.ini """

        ret_value = {"RESULT": "ERROR", "STATUS_CODE": 400, "DESC": "", "DATA": list()}

        user_ip = request.remote_addr

        # получаем данные из параметров запроса
        res_request = request.args
        # print(res_request)
        answer_id = str(res_request.get('answer_id'))
        caller_id = str(res_request.get('caller_id'))

        logger.event(f"Обращение к rtsp от адреса {user_ip}. Абонент {caller_id} связался с {answer_id}")

        db_request_cams = CamerasDB().find_camera(caller_id)

        if db_request_cams['RESULT'] != "SUCCESS":
            logger.error(db_request_cams)
            return jsonify(db_request_cams)

        try:
            for it in db_request_cams.get('DATA'):
                # Команда на запись кадра
                valid_frame = CAM_DICT[it.get('FName')].create_frame()
                # Получить кадр
                frame = CAM_DICT[it.get('FName')].take_frame(valid_frame)
                # Получаем дату и генерируем полный путь к файлу
                date_time = str(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
                file_name = f"{it.get('FName')}-{caller_id}-{date_time}.jpg"
                file_path = f"{set_ini['photo_path']}{file_name}"

                with open(file_path, 'wb') as file:
                    # Сохраняем кадр в файл
                    file.write(frame)

                logger.event(f"Успешно создан файл: {file_name}")

                # Добавляем событие в БД
                db_add = EventDB().add_photo(caller_id, answer_id, it.get('FName'), file_name)

                if db_add:
                    ret_value['DATA'].append({"file_name": file_name})
                    ret_value["RESULT"] = "SUCCESS"
                    ret_value['STATUS_CODE'] = 200
                else:
                    logger.warning(f"Не удалось внести данные в БД: {res_request}")
                    ret_value['DESC'] = ret_value['DESC'] + f"Не удалось внести данные в БД: {file_name}."

        except Exception as ex:
            logger.exception(f"Не удалось получить/сохранить кадр из камеры: {ex}")

        return make_response(jsonify(ret_value), ret_value['STATUS_CODE'])

    @app.route('/action.update_cams', methods=['POST'])
    def update_cameras():
        """ Даём команду RTSP серверу на обновления списка работающих камер """
        global CAM_DICT
        ret_value = {"RESULT": "ERROR", "DESC": '', "DATA": dict()}

        try:
            # Запрашиваем у БД список камер
            new_cams = CamerasDB().take_cameras()
            set_ini['CAMERAS'] = new_cams.get('DATA')

            CAM_DICT = create_cams_threads(set_ini['CAMERAS'], CAM_DICT)

            ret_value['RESULT'] = "SUCCESS"
        except Exception as ex:
            logger.exception(f"Исключение вызвало: {ex}")
            ret_value['DESC'] = f"Исключение в работе сервиса: {ex}"

        return jsonify(ret_value)


    # RUN SERVER FLASK  ------
    app.run(debug=False, host=set_ini["host"], port=int(set_ini["port"]))
