import cv2
import argparse

from ultralytics import YOLO
import yolov5
import supervision as sv
import numpy as np


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="YOLOv8 live")
    parser.add_argument(
        "--webcam-resolution",
        default=[640, 384],
        nargs=2,
        type=int
    )
    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()
    frame_width, frame_height = args.webcam_resolution

    cap = cv2.VideoCapture("rtsp://UVIG:VIG5682881@192.168.0.74")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

    # model = YOLO("yolov8n.pt")
    model = yolov5.load("./content/Plates/best.pt")
    # model = YOLO("./content/Plates/best.pt")

    box_annotator = sv.BoxAnnotator(
        thickness=2,
        text_thickness=2,
        text_scale=1
    )
    #
    # zone_polygon = (ZONE_POLYGON * np.array(args.webcam_resolution)).astype(int)
    # zone = sv.PolygonZone(polygon=zone_polygon, frame_resolution_wh=tuple(args.webcam_resolution))
    # zone_annotator = sv.PolygonZoneAnnotator(
    #     zone=zone,
    #     color=sv.Color.green(),
    #     thickness=2,
    #     text_thickness=4,
    #     text_scale=2
    # )
    index = 9

    detections = None
    labels = None

    while True:
        # Получаем ret = статус и frame = кадр
        ret, frame = cap.read()
        index += 1
        # model = разметка нейронной схемы
        # result = model(frame, agnostic_nms=True)[0]
        if ret:
            # frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

            if index == 10:
                index = 0
                result = model(frame)
                # detections = sv.Detections.from_yolov8(result)
                detections = sv.Detections.from_yolov5(result)
                # print(detections)
                labels = [f"CarNumber" for _, _, _, _, _ in detections]
                # labels = [f"{model.model.named_modules()} {confidence:0.2f}" for _, confidence, class_id, _ in detections]

            # метод дорисовывает поля и вероятность
            frame = box_annotator.annotate(
                scene=frame,
                detections=detections,
                labels=labels
            )

                # поиск зон в кадре
                # zone.trigger(detections=detections)
                # frame = zone_annotator.annotate(scene=frame)

            cv2.imshow("yolov5", frame)


        if (cv2.waitKey(30) == 27):
            break


if __name__ == "__main__":
    main()
