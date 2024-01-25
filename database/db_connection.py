import configparser
import os
import datetime
import threading

import pymysql
import pymysql.cursors

LOCK_TH_INI = threading.Lock()

DB_SETTINGS = {
    'status': False,
    'host': '0.0.0.0',
    'user': 'user',
    'password': 'pass',
    'charset': 'cp1251'
    }


def take_db_settings() -> bool:
    """ Функция загружает данные из settings.ini """
    global DB_SETTINGS

    settings_file = configparser.ConfigParser()

    if os.path.isfile("./settings.ini"):
        try:
            with LOCK_TH_INI:  # Блокируем потоки
                settings_file.read("settings.ini", encoding="utf-8")

            DB_SETTINGS['host'] = str(settings_file["BASE"]["HOST"])
            DB_SETTINGS['user'] = str(settings_file["BASE"]["USER"])
            DB_SETTINGS['password'] = str(settings_file["BASE"]["PASSWORD"])
            DB_SETTINGS['charset'] = str(settings_file["BASE"]["CHARSET"])

            DB_SETTINGS['status'] = True

        except Exception as ex:
            print(f"{datetime.datetime.now()}: {ex}")
    else:
        print(f"{datetime.datetime.now()}\ttake_db_settings\tФАЙЛ SETTINGS.INI НЕ НАЙДЕН!")

    return DB_SETTINGS['status']


def connect_db():

    if not DB_SETTINGS['status']:
        res = take_db_settings()


    pool = pymysql.connect(host=DB_SETTINGS['host'],
                                  user=DB_SETTINGS['user'],
                                  password=DB_SETTINGS['password'],
                                  charset=DB_SETTINGS['charset'],
                                  cursorclass=pymysql.cursors.DictCursor)

    return pool
