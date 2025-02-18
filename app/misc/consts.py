ERROR_ACCESS_IP = 'access_block_ip'
ERROR_READ_REQUEST = 'error_read_request'
ERROR_ON_SERVER = 'server_error'
CAM_DICT = dict()

class CameraClass:
    @staticmethod
    def update(list_of_cams) -> None:
        global CAM_DICT
        CAM_DICT = list_of_cams

    @staticmethod
    def get() -> dict:
        return CAM_DICT

    @staticmethod
    def get_frame(cam_name: str) -> b'':
        # Команда на запись кадра в файл
        valid_frame = CAM_DICT[cam_name].create_frame()
        # Получить кадр
        return CAM_DICT[cam_name].take_frame(valid_frame)