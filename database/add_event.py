from misc.logger import Logger
from database.db_connection import connect_db


logger = Logger()


class EventDB:

    @staticmethod
    def add_photo(caller_id: str, answer_id: str, cam_id: str, file_name: str) -> bool:
        """ Функция создает ивент в БД с фотографией и информацией какой абонент предоставил доступ. """
        ret_value = False

        msg_event = f"Абонент {answer_id} предоставил доступ для {caller_id}."
        desc_event = f"{caller_id}/{cam_id}/{answer_id}"

        try:
            connection = connect_db()

            event_type_id = 20

            with connection.cursor() as cur:
                # Добавляем событие
                cur.execute(f"insert into vig_sender.tevent(FEventTypeID, FDateEvent, FDateRegistration, "
                            f"FOwnerName, FEventMessage, FEventDescription, FProcessed) "
                            f"values (%s, now(), now(), 'RTSP server (Asterisk)', %s, %s, 2)",
                            (event_type_id, msg_event, desc_event))
                connection.commit()

                cur.execute(f"select * from vig_sender.tevent where FEventTypeID = {event_type_id} "
                            f"and FProcessed = 2 order by FID desc")
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