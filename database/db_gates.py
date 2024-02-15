from database.db_connection import DBConnection


class GatesDB(DBConnection):
    """ Получает из БД данные всех рэле и связи с домофонами (caller_id)"""
    def update(self) -> dict:

        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": {}}

        try:
            with self.connection.cursor() as cur:
                # Получаем список камер
                # cur.execute("select * from UNKNOWN_TABLE")
                # res = cur.fetchall()

                # Тестовая заглушка
                ret_value['RESULT'] = "SUCCESS"
                ret_value['DATA'] = {100: {'host': '192.168.48.174', 'port': 177}}  # Пример как должны выглядеть данные
        except Exception as ex:
            ret_value["DESC"] = f"Исключение вызвало: {ex}"

        return ret_value