import socket
from database.db_gates import GatesDB

DICT_GATES_ADDRESS = {}
# DICT_GATES_ADDRESS = {100: {'host': '192.168.48.174', 'port': 177}}
TIME_OUT_REQUEST = 5  # sec.

# В модуле реле присутствует 2 реле
DICT_GATES_OPEN = {0: b"#01000100", 1: b"#01000101"}
# STR_GATE_OPEN_FIRST = b"#01000100"
# STR_GATE_OPEN_SECOND = b"#01000101"


class Gates:
    @staticmethod
    def open(numb_gate: int, caller_id: int) -> dict:
        """ Функция подключения и получения данных из сокета
         В модуле реле присутствует 2 реле
         (numb_gate = 0 or 1)
         Данные получает из глобальной переменной в которую предварительно
         загружены адреса реле в соответствии с CALLER_ID(номер домофона)"""

        ret_value = {'success': False, 'desc': ''}

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_main:
                socket_main.settimeout(TIME_OUT_REQUEST)
                socket_main.connect((DICT_GATES_ADDRESS[caller_id]['host'], DICT_GATES_ADDRESS[caller_id]['port']))

                socket_main.sendall(DICT_GATES_OPEN[numb_gate])

                res = socket_main.recv(1024)

                if res == b"#010000":
                    ret_value['success'] = True
                else:
                    ret_value['desc'] = f"Что-то пошло не так, реле ответило кодом: {res}"

        except Exception as ex:
            ret_value['desc'] = f"Ошибка в работе связи с рэле: {ex}"

        return ret_value

    @staticmethod
    def update_data() -> bool:
        """ Обновляет данные рэле, подгружает из БД """
        global DICT_GATES_ADDRESS

        res = GatesDB().update()

        if res.get('RESULT') == 'SUCCESS':
            DICT_GATES_ADDRESS = res.get('DATA')
            return True

        return False


if __name__ == "__main__":
    # print(Gates.update_data())
    DICT_GATES_ADDRESS = {100: {'host': '192.168.48.174', 'port': 177}}
    print(Gates.open(0, 100))
    print(Gates.open(1, 100))
