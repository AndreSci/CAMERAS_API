#!/usr/bin/python3.11

import requests

# Адрес и порта расположения RTSP server
HOST = "192.168.15.10"
PORT = 8093

LOG_PATH = None  # Возможно указать путь в строке - пример: "/home/asterisk/logs/"
# (предварительно требуется создание полного пути)

def do_request(caller_id, answer_id) -> dict:
    """ Функция отправляет запрос на RTSP сервер """
    ret_value = {"RESULT": 'ERROR', 'DESC': '', 'DATA': dict()}

    try:
        res = requests.get(f"http://{HOST}:{PORT}/action.save?caller_id={caller_id}&answer_id={answer_id}",
                           timeout=2)

        if res.status_code == 200:
            ret_value['RESULT'] = 'SUCCESS'
        else:
            ret_value['DESC'] = 'Сервер ответил неожиданным статус кодом'
            ret_value['DATA'] = {'status_code': res.status_code, 'text': res.text, 'json': res.json()}

    except Exception as ex:
        print(f"EXCEPTION\tREQUEST_SCRIPT\tИсключение вызвало: {ex}")

    return ret_value

if __name__ == "__main__":
    print("INFO\tREQUEST_SCRIPT\tstart SCRYPT")
    # m_caller_id = sys.argv[1]
    # m_answer_id = sys.argv[2]

    m_caller_id = 205
    m_answer_id = 108

    print(f"INFO\tREQUEST_SCRIPT\t"
          f"Произведен запуск скрипта с параметрами: caller_id: {m_caller_id} - answer_id: {m_answer_id}")

    print(f"INFO\tREQUEST_SCRIPT\t{do_request(m_caller_id, m_answer_id)}")
