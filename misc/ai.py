import yolov5
import supervision as sv
import threading
import cv2


CLASS_ID = ['_', 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 'A', 'B', 'C', 'E', 'H', 'K', 'M', 'P', 'T', 'X', 'Y']
CONF_LVL = 0.7  # вероятность


def pasr_detection(xyxy: list, id_char: list, confidence: list):

    global CLASS_ID, CONF_LVL

    number = list()

    # Проходим по всем элементам номера
    for case in xyxy:
        number.append(case[0])

    # Объединяем для упорядочивания вывода номера
    zip_res = zip(number, id_char, confidence)
    zip_list = list(zip_res)

    # Сортируем от меньшего к большему (то же что от левого объекта к правому)
    zip_list.sort()
    number_list = list()

    # Формируем номер
    for _, ind, conf in zip_list:
        if conf > CONF_LVL:
            number_list.append(str(CLASS_ID[ind]))

    return number_list


class AiClass:
    def __init__(self):
        self.model_plates = yolov5.load("./content/Plates/best.pt")
        self.model_number = yolov5.load("./content/Nums/last.onnx")

        self.lock_thread = threading.Lock()

    def find_plate(self, frame):

        box_annotator = sv.BoxAnnotator(
            thickness=1,
            text_thickness=1,
            text_scale=1
        )

        with self.lock_thread:
            result = self.model_plates(frame)
            # Находим все объекты на кадре
            detect_plates = sv.Detections.from_yolov5(result)

            numbers = list()

            for it in detect_plates.xyxy:
                numbers.append(self.recon_number(frame, it))

            print(numbers)

            labels = ["".join(num) for num in numbers]

            # Добавляем разметку на кадр
            ret_frame = box_annotator.annotate(
                scene=frame,
                detections=detect_plates,
                labels=labels
            )

        return ret_frame

    def recon_number(self, frame, array) -> list:
        """ Возвращает номер в виде списка элементов номера """
        ret_value = list()

        try:

            # print(f"[{array.data[1]}:{array.data[3]}, {array.data[0]}:{array.data[2]}]")
            crop_img = frame[int(array.data[1]):int(array.data[3]), int(array.data[0]):int(array.data[2])]

            # Делаем серого цвета вырезанный участок для распознания
            crop_img = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)

            # Меняем размер под размеры нейронной сети
            crop_img = cv2.resize(crop_img, (160, 160))
            # Отправляем на распознание
            result = self.model_number(crop_img, (160, 160))
            # Выгружаем данные
            res = sv.Detections.from_yolov5(result)

            # Отправляем на сортировку данных
            ret_value = pasr_detection(res.xyxy, res.class_id, res.confidence)

        except Exception as ex:
            print(f"Исключение: {ex}")

        return ret_value
