Команды

Имя камеры берется из settings.ini и пишется в нижнем регистре

остановить  запрос к камере
127.0.0.1:80/stop.cam?name=cam3

запустить камеру
127.0.0.1:80/start.cam?name=cam3

получить кадр (CAM:3 где 3 это номер камеры)
127.0.0.1:80/action.do?version=4.9.4&video_in=CAM:3&command=frame.video

создание события с кадром
127.0.0.1:80/action.save?caller_id=205&answer_id=108

Библиотеки которые нужно подгрузить

OpenCV версия
pip install opencv-python==4.5.5.64

PyTorch 2.0 + cuda 18
pip install numpy --pre torch torchvision torchaudio --force-reinstall --index-url https://download.pytorch.org/whl/nightly/cu118