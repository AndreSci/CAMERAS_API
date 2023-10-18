from flask import Blueprint, request, jsonify, Response
from misc.logger import Logger
from misc.allow_ip import AllowedIP
from misc.consts import ERROR_ACCESS_IP

logger = Logger()
allow_ip = AllowedIP()

frame_app = Blueprint("frame", __name__)


@frame_app.route('/action.do', methods=['GET'])
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
            logger.exception(f"Не удалось получить кадр из камеры: {ex}")

        return Response(frame, mimetype='image/jpeg')

    return jsonify(json_replay)
