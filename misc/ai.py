import yolov5
import supervision as sv
import threading
import cv2


class AiClass:
    def __init__(self):
        self.model = yolov5.load("./content/Plates/best.pt")

        self.lock_thread = threading.Lock()

    def find_plate(self, frame):

        box_annotator = sv.BoxAnnotator(
            thickness=2,
            text_thickness=2,
            text_scale=1
        )

        with self.lock_thread:
            result = self.model(frame)
            # Находим все объекты на кадре
            detections = sv.Detections.from_yolov5(result)

            # Создаем список имён для всех объектов
            labels = [f"CarNumber" for _, _, _, _, _ in detections]

            # Добавляем разметку на кадр
            ret_frame = box_annotator.annotate(
                scene=frame,
                detections=detections,
                labels=labels
            )

        return ret_frame
