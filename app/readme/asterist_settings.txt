Инструкция по настройки астериска для вызова python скрипта с параметрами.
Скрипт предназначен для отправки http запроса на указанный сервер.

Инструкция по настройки астериска для вызова скрипта.
1. открываем файл /etc/asterisk/sip.conf
  - создаем абонентов
    пример:
        [general]
        context=default
        allowoverlap=no
        udpbindaddr=0.0.0.0
        tcpenable=no
        tcpbindaddr=0.0.0.0
        transport=udp
        srvlookup=yes
        videosupport=yes
        maxcallbitrate=6144
        disallow=all
        allow=g722
        allow=g726
        allow=g711
        allow=alaw
        allow=h264

        [301]
        # client
        type=friend
        host=dynamic
        secret=1301
        dtmf=dtmf-info
        [302]
        # client
        type=friend
        host=dynamic
        secret=2302
        dtmf=dtmf-info

2. открываем файл /etc/asterisk/extensions.conf
  - создаем сценарии связи абонентов
    пример:
        [general]
        static=yes
        writeprotect=no
        priorityjumping=no
        autofallthrough=yes
        clearglobalvars=no

        ;User 301 =========================================
        exten => 301,1,set(_GLOBAL301=${CALLERID(num)})
            same => n,Set(__DYNAMIC_FEATURES=readDTMF301)
            same => n,Dial(SIP/301,45)
            same => n,Hangup()
        ;END ===============================================
        ;User 302 ==========================================
        exten => 302,1,set(_GLOBAL302=${CALLERID(num)})
            same => n,Set(__DYNAMIC_FEATURES=readDTMF302)
            same => n,Dial(SIP/302,45)
            same => n,Hangup()
        ;END ===============================================

  - в примере наблюдаются глобальные переменные с наследованием в разные области астериска через указатель нижнее подчёркивание _ (это нужно для передачи переменной в файл features.conf)
    _GLOBAL301 - последующее обращение к глобальной переменной выполняется без знака _ пример: ${GLOBAL301},
    ему присваивается номер звонящего абонента ${CALLERID(num)}.

    Set(__DYNAMIC_FEATURES=readDTMF301) объявляет метод ожидающий нажатие клавиши
    (readDTMF301 объект в файле features.conf)

3. открываем файл /etc/asterisk/features.conf
  - создаем объект запускающий скрипт python по вводу числа
    пример:
        [applicationmap]
        readDTMF301 => 1,self/callee,AGI(/etc/asterisk/scripts/your_script.py,${CALLERID(num)},${GLOBAL301})
        readDTMF302 => 1,self/callee,AGI(/etc/asterisk/scripts/your_script.py,${CALLERID(num)},${GLOBAL302})

  - в примере указывается AGI с параметрами путь к скрипту и через запятую, БЕЗ ПРОБЕЛОВ, параметры которые мы хотим передать
    ${GLOBAL301} это наша глобальная переменная из файла extensions.conf
    примечание: ${CALLERID(num)} это id абонента вводящий число, это могут быть оба абонента...
