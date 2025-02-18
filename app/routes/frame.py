from flask import Blueprint, request, jsonify, Response, make_response
import datetime
from misc.allow_ip import AllowedIP
from misc.logger import Logger
from misc.consts import ERROR_ACCESS_IP, ERROR_READ_REQUEST, ERROR_ON_SERVER, CameraClass
from misc.models import REQUEST_DICT

logger = Logger()

frame_blue = Blueprint("frame_router", __name__)

allow_ip = AllowedIP()
allow_ip.read_file(logger)


@frame_blue.route('/action.do', methods=['GET'])
def take_frame():
    """ Запрашиваем у потока последний кадр """
    print(f"Someone takes ask frame: {datetime.datetime.now()}")

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
        cam_name = 'cam' + cam_name[cam_name.find(':') + 1:]

        try:
            frame = CameraClass.get_frame(cam_name)
        except Exception as ex:
            frame = ''
            logger.add_log(f"EXCEPTION\ttake_frame()\tНе удалось получить кадр из камеры: {ex}")

        return Response(frame, mimetype='image/jpeg')

    return jsonify(json_replay)


# @frame_blue.route('/action.save', methods=['GET'])
# def save_frame_asterisk():
#     """ Запрашиваем у потока последний кадр и сохраняем его в папку согласно настройкам settings.ini """
#
#     ret_value = {"RESULT": "ERROR", "STATUS_CODE": 400, "DESC": "", "DATA": list()}
#
#     user_ip = request.remote_addr
#
#     # получаем данные из параметров запроса
#     res_request = request.args
#     # print(res_request)
#     answer_id = str(res_request.get('answer_id'))
#     caller_id = str(res_request.get('caller_id'))
#
#     logger.event(f"Обращение к rtsp от адреса {user_ip}. Абонент {caller_id} связался с {answer_id}")
#
#     db_request_cams = CamerasDB().find_camera(caller_id)
#
#     if db_request_cams['RESULT'] != "SUCCESS":
#         logger.error(db_request_cams)
#         return jsonify(db_request_cams)
#
#     try:
#         for it in db_request_cams.get('DATA'):
#
#             frame = CameraClass.get_frame(it.get('FName'))
#             # Получаем дату и генерируем полный путь к файлу
#             date_time = str(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
#             file_name = f"{it.get('FName')}-{caller_id}-{date_time}.jpg"
#             file_path = f"{set_ini['photo_path']}{file_name}"
#
#             with open(file_path, 'wb') as file:
#                 # Сохраняем кадр в файл
#                 file.write(frame)
#
#             logger.event(f"Успешно создан файл: {file_name}")
#
#             # Добавляем событие в БД
#             db_add = EventDB().add_photo(caller_id, answer_id, it.get('FName'), file_name)
#
#             if db_add:
#                 ret_value['DATA'].append({"file_name": file_name})
#                 ret_value["RESULT"] = "SUCCESS"
#                 ret_value['STATUS_CODE'] = 200
#             else:
#                 logger.warning(f"Не удалось внести данные в БД: {res_request}")
#                 ret_value['DESC'] = ret_value['DESC'] + f"Не удалось внести данные в БД: {file_name}."
#
#     except Exception as ex:
#         logger.exception(f"Не удалось получить/сохранить кадр из камеры: {ex}")
#
#     return make_response(jsonify(ret_value), ret_value['STATUS_CODE'])


# @frame_blue.route('/action.update_cams', methods=['POST'])
# def update_cameras():
#     """ Даём команду RTSP серверу на обновления списка работающих камер """
#
#     ret_value = {"RESULT": "ERROR", "DESC": '', "DATA": dict()}
#
#     try:
#         # Запрашиваем у БД список камер
#         new_cams = CamerasDB().take_cameras()
#         set_ini['CAMERAS'] = new_cams.get('DATA')
#
#         CAM_DICT = create_cams_threads(set_ini['CAMERAS'], CAM_DICT)
#         CameraClass.update(create_cams_threads(set_ini['CAMERAS']))
#
#         ret_value['RESULT'] = "SUCCESS"
#     except Exception as ex:
#         logger.exception(f"Исключение вызвало: {ex}")
#         ret_value['DESC'] = f"Исключение в работе сервиса: {ex}"
#
#     return jsonify(ret_value)
