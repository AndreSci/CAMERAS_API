from misc.logger import Logger
from database.db_connection import connect_db


logger = Logger()


class EventDB:

    @staticmethod
    def add_photo(caller_id: int, cam_id: str, file_name: str) -> bool:

        ret_value = False

        msg_event = f"Абонент {caller_id} предоставил доступ."
        desc_event = f"{caller_id}/{cam_id}"

        try:
            connection = connect_db()

            with connection.cursor() as cur:
                # Добавляем событие
                cur.execute(f"insert into vig_sender.tevent(FEventTypeID, FDateEvent, FDateRegistration, "
                            f"FOwnerName, FEventMessage, FEventDescription, FProcessed) "
                            f"values (26, now(), now(), 'RTSP server (Asterisk)', %s, %s, 1)", (msg_event, desc_event))
                connection.commit()

                cur.execute(f"select * from vig_sender.tevent where FEventTypeID = 26 "
                            f"and FProcessed= 1 order by FID desc limit 1")
                res_sql = cur.fetchone()

                event_id = res_sql.get('FID')
                # Добавляем имя файла и связываем с событием
                cur.execute(f"insert into vig_sender.teventphoto(FEventID, FFileName, FDateTime) "
                            f"values (%s, %s, now())", (event_id, file_name))
                # Обновляем статус FProcessed = 0
                cur.execute(f"update vig_sender.tevent set FProcessed = 0 where FID = %s", event_id)
                connection.commit()

                logger.event(f"Добавлено событие в БД: {res_sql}")
                ret_value = True
        except Exception as ex:
            logger.exception(f"Исключение вызвало: {ex}")

        return ret_value