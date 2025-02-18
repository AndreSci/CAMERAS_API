import requests
import socket

RET_VALUE = {'RESULT': 'ERROR', 'DESC': '', 'DATA': dict()}


class Gate:
    def __init__(self, host: str, port: int, url: str = None):
        self.url = url
        self.host = host
        self.port = port

    def open(self):
        """ Отправляет команду по TCP протоколу на открытие прохода\проезда """
        ret_value = RET_VALUE

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((self.host, self.port))
                s.sendall('OPEN')  #TODO узнать данные для отправки и получения
                data = s.recv(1024)

                print(data)
        except TimeoutError as tex:
            print(f"Исключение по времени обращения по TCP ({tex}) {self.host}:{self.port}")
        except Exception as ex:
            print(f"Исключение вызвало: {ex}")

        return ret_value