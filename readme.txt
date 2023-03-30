
Список камер
CAM1=rtsp://UVIG:VIG5682881@192.168.20.226/h264
CAM2=rtsp://UVIG:VIG5682881@192.168.0.55
CAM3=rtsp://UVIG:VIG5682881@192.168.0.88
CAM4=rtsp://UVIG:VIG5682881@192.168.0.74
CAM5=rtsp://UVIG:VIG5682881@192.168.0.93
CAM6=rtsp://UVIG:VIG5682881@192.168.10.169/h264
CAM7=rtsp://admin:admin@192.168.48.188

Команды

остановить  запрос к камере
192.168.48.34:80/stop.cam?name=cam3

запустить камеру
192.168.48.34:80/start.cam?name=cam3

получить кадр (CAM:3 где 3 это номер камеры)
192.168.48.34:80/action.do?version=4.9.4&video_in=CAM:3&command=frame.video

Библиотеки которые нужно подгрузить

requests
flask
configparser
functools

OpenCV версия
pip install opencv-python==4.5.5.64