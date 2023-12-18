from database.db_connection import connect_db


class CamerasDB:

    @staticmethod
    def take_cameras() -> dict:

        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": {}}

        try:
            connection = connect_db()

            with connection.cursor() as cur:
                # Получаем список камер
                cur.execute("select FName, FRTSP from vig_sender.tcamera")

                res = cur.fetchall()

                for it in res:

                    ret_value['DATA'][it['FName']] = it['FRTSP']

                ret_value['RESULT'] = "SUCCESS"
        except Exception as ex:
            ret_value["DESC"] = f"Исключение вызвало: {ex}"

        return ret_value

    @staticmethod
    def add_camera(f_name: str, rtsp: str) -> dict:

        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": {}}

        try:
            connection = connect_db()

            with connection.cursor() as cur:
                # Получаем список камер
                cur.execute("select FName, FRTSP from vig_sender.tcamera")

                connection.commit()

                res = cur.rowcount

                if res > 0:
                    ret_value['RESULT'] = "SUCCESS"

        except Exception as ex:
            ret_value["DESC"] = f"Исключение вызвало: {ex}"

        return ret_value

    @staticmethod
    def find_camera(caller_id: str) -> dict:

        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": {}}

        try:
            connection = connect_db()

            with connection.cursor() as cur:
                # Получаем список камер с которых нужно получить кадры
                cur.execute(f"select tcamera.FName, tcamera.FRTSP "
                            f"from vig_sender.tasteriskcaller, vig_sender.tasteriskcamgroup, "
                            f"vig_sender.tcameragroups, vig_sender.tcamera "
                            f"where tasteriskcaller.FName = %s "
                            f"and tasteriskcaller.FID = tasteriskcamgroup.FAsteriskID "
                            f"and tcameragroups.FAsteriskCamGroupID = tasteriskcamgroup.FID "
                            f"and tcamera.FID = tcameragroups.FCameraID", (str(caller_id), ))

                res = cur.fetchall()

                if len(res) > 0:
                    ret_value['DATA'] = res
                    ret_value['RESULT'] = "SUCCESS"

        except Exception as ex:
            ret_value["DESC"] = f"Исключение вызвало: {ex}"

        return ret_value