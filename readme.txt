Команды

остановить  запрос к камере
127.0.0.1:80/stop.cam?name=cam3

запустить камеру
127.0.0.1:80/start.cam?name=cam3

получить кадр (CAM:3 где 3 это номер камеры)
127.0.0.1:80/action.do?version=4.9.4&video_in=CAM:3&command=frame.video

Библиотеки которые нужно подгрузить

requests
flask
configparser
functools

OpenCV версия
pip install opencv-python==4.5.5.64