import configparser
import os
import datetime
import threading

import pymysql
import pymysql.cursors

LOCK_TH_INI = threading.Lock()


def take_db_settings():
    """ Функция загружает данные из settings.ini """
    conn_inf = dict()

    settings_file = configparser.ConfigParser()

    if os.path.isfile("./settings.ini"):
        try:
            with LOCK_TH_INI:  # Блокируем потоки
                settings_file.read("settings.ini", encoding="utf-8")

            conn_inf['host'] = str(settings_file["BASE"]["HOST"])
            conn_inf['user'] = str(settings_file["BASE"]["USER"])
            conn_inf['password'] = str(settings_file["BASE"]["PASSWORD"])
            conn_inf['charset'] = str(settings_file["BASE"]["CHARSET"])

        except Exception as ex:
            print(f"{datetime.datetime.now()}: {ex}")
            conn_inf = dict()
    else:
        print(f"{datetime.datetime.now()}: func - take_db_settings: ФАЙЛ SETTINGS.INI НЕ НАЙДЕН!")

    return conn_inf


def connect_db():
    conn_inf = take_db_settings()

    pool = pymysql.connect(host=conn_inf['host'],
                                  user=conn_inf['user'],
                                  password=conn_inf['password'],
                                  charset=conn_inf['charset'],
                                  cursorclass=pymysql.cursors.DictCursor)

    return pool
