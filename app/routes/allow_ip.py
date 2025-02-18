from flask import Blueprint, request, jsonify
from misc.logger import Logger
from misc.allow_ip import AllowedIP
from misc.models import REQUEST_DICT

logger = Logger()
allow_ip_route = AllowedIP()
allow_ip_route.read_file(logger)

allow_ip_blue = Blueprint("allow_ip", __name__)


@allow_ip_blue.route('/DoAddIp', methods=['POST'])
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