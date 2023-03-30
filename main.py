from misc.video_thread import ThreadVideoRTSP
from misc.video_thread import create_cams_threads
from flask import Flask, request, jsonify, Response

from misc.logger import Logger
from misc.utility import SettingsIni
from misc.allow_ip import AllowedIP

import logging

ERROR_ACCESS_IP = 'access_block_ip'
ERROR_READ_REQUEST = 'error_read_request'
ERROR_ON_SERVER = 'server_error'


def block_flask_logs():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)


def web_flask(logger: Logger, settings_ini: SettingsIni):
    """ Главная функция создания сервера Фласк. """

    app = Flask(__name__)  # Объявление сервера

    app.config['JSON_AS_ASCII'] = False

    # Блокируем сообщения фласк
    block_flask_logs()

    set_ini = settings_ini.take_settings()

    allow_ip = AllowedIP()
    allow_ip.read_file(logger)

    logger.add_log(f"SUCCESS\tweb_flask\tСервер WEB_RUM_Flask начал свою работу")  # log

    cam_list = create_cams_threads(set_ini['CAMERAS'])

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
        """ Удаляет заявку на создание пропуска если FStatusID = 1 \n
        принимает user_id, inn и fid заявки """

        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        # logger.add_log(f"EVENT\taction.do\tзапрос от ip: {user_ip}", print_it=False)

        # Проверяем разрешён ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = ERROR_ACCESS_IP

            logger.add_log(f"WARNING\ttake_frame()\tОшибка доступа по ip: {user_ip}, ip не имеет разрешения.")
        else:
            # получаем данные из параметров запроса
            res_request = request.args

            # cam_name = str(res_request.get('cam_name'))
            cam_name = str(res_request.get('video_in'))
            cam_name = 'cam' + cam_name[cam_name.find(':') + 1:]

            try:
                # Команда на запись кадра в файл
                valid_frame = cam_list[cam_name].create_frame()
                # Получить кадр
                frame = cam_list[cam_name].take_frame(valid_frame)
            except Exception as ex:
                frame = ''
                logger.add_log(f"EXCEPTION\ttake_frame()\tНе удалось получить кадр из камеры: {ex}")

            return Response(frame, mimetype='image/jpeg')

        return jsonify(json_replay)

    @app.route('/start.cam', methods=['GET'])
    def start_cam():
        """ Включает получение видео потока от указанной каменры """

        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tstart_cam()\tзапрос от ip: {user_ip}", print_it=False)

        # Проверяем разрешён ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = ERROR_ACCESS_IP
            logger.add_log(f"WARNING\tstart_cam()\tОшибка доступа по ip: {user_ip}, ip не имеет разрешения.")
        else:
            # получаем данные из параметров запроса
            res_request = request.args

            # cam_name = str(res_request.get('cam_name'))
            cam_name = str(res_request.get('name'))

            cam_list[cam_name].start()

            json_replay['RESULT'] = "SUCCESS"

        return jsonify(json_replay)

    @app.route('/stop.cam', methods=['GET'])
    def stop_cam():
        """ Удаляет заявку на создание пропуска если FStatusID = 1 \n
        принимает user_id, inn и fid заявки """

        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tstop_cam()\tзапрос от ip: {user_ip}", print_it=False)

        # Проверяем разрешён ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = ERROR_ACCESS_IP
            logger.add_log(f"WARNING\tstop_cam()\tОшибка доступа по ip: {user_ip}, ip не имеет разрешения.")
        else:
            # получаем данные из параметров запроса
            res_request = request.args

            # cam_name = str(res_request.get('cam_name'))
            cam_name = str(res_request.get('name'))

            cam_list[cam_name].stop()

            json_replay['RESULT'] = "SUCCESS"

        return jsonify(json_replay)

    # RUN SERVER FLASK  ------
    app.run(debug=False, host=set_ini["host"], port=int(set_ini["port"]))
