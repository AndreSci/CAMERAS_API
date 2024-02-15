import socket
import time
import sys


TEST_HOST = "0.0.0.0"
TEST_PORT = 8080
TEST_PORTS_NEEDED = 1000


def check_server(host: str, port: int) -> bool:
    """ Проверяет порт, возвращает False если порт занят другой программой """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
        return False
    except socket.error as se:
        pass

    return True


def take_ports(host: str, port: int, ports_needed: int = 1) -> list[int]:
    """ Возвращает список доступных портов после стартового port.\n
    :param host: Хост, где искать порты.
    :param port: Порт от него искать свободные порты.
    :param ports_needed: Кол-во портов которые нужно найти."""

    ret_value = list()
    index = 0
    percent_step = 100 / ports_needed

    while index < ports_needed:
        str_percent = f"LOADING: {int(len(ret_value) * percent_step)}% "
        index += 1
        time.sleep(0.001)  # Для многопоточных скриптов

        if check_server(host, index + port):
            ret_value.append(index + port)
            sys.stdout.write(f"\r{str_percent} - Connection to {host} on port {index + port} is FREE")
        else:
            sys.stdout.write(f"\r{str_percent} - Connected to {host} on port {index + port} is BUSY")

        sys.stdout.flush()
        # максимальный порт 65535
        if index == 1000 or port + index >= 65535:
            print(f"Остановлено по достижению максимального кол-вы доступных итераций.")
            break

    time.sleep(2)
    sys.stdout.write(f"\rLOADING: 100% - Connection to {host} on port {index + port} is FREE\n")
    time.sleep(0.01)

    return ret_value


def main(host: str, port: int, ports_needed: int = 1) -> list[int]:
    """ Стартовая функция """
    return take_ports(host, port, ports_needed)


if __name__ == "__main__":
    print(main(TEST_HOST, TEST_PORT, TEST_PORTS_NEEDED))
    input()
