# ПР01. Граф turtlesim и разрыв по ROS_DOMAIN_ID

Среда: Docker-образ `tiryoh/ros2-desktop-vnc:lyrical-20260906T0836` на macOS arm64,
Ubuntu 26.04.1, ROS 2 Lyrical, RMW `rmw_fastrtps_cpp` (подробно — `environment.json`).
Опыт проведён 2026-09-24. Пара доменов: рабочий **16**, «чужой» **17**.

Все терминалы — процессы внутри одного контейнера `ros2`. В каждом перед командой
выполнялся `source /opt/ros/lyrical/setup.bash` и задавался `ROS_DOMAIN_ID`.

- A: `ros2 run turtlesim turtlesim_node` — всё время в домене 16.
- B: `ros2 run turtlesim turtle_teleop_key` — перезапускался: 16 → 17 → 16.
- C: наблюдение через CLI.

`turtle_teleop_key` читает клавиатуру из TTY. Агент запускал его под псевдотерминалом
(`script`) и подавал escape-последовательности стрелок через FIFO. Это те же байты, что
посылает клавиатура. Управление стрелками вживую повторяется на рабочем столе (noVNC)
в Terminator.

Сырой вывод команд: `graph-healthy.txt`, `test-broken.txt`, `test-fixed.txt`,
`pose-broken.txt`, `pose-fixed.txt`, `domains-broken.txt`, `domains-fixed.txt`,
`teleop-fixed.txt`, `doctor.txt`.

## 1. Исправный граф (оба участника в домене 16)

Стрелки двигают черепаху: до нажатий `ros2 topic echo /turtle1/pose --once` показывал
`x: 5.544…, y: 5.544…, theta: 0.0` (точка появления). После серии «вверх/влево/вверх»
показал `x: 11.088…, y: 5.743…, theta: 0.096` (черепаха упёрлась в правую стену).

```text
$ ros2 node list --no-daemon --spin-time 2
/teleop_turtle
/turtlesim

$ ros2 topic list -t
/parameter_events [rcl_interfaces/msg/ParameterEvent]
/rosout [rcl_interfaces/msg/Log]
/turtle1/cmd_vel [geometry_msgs/msg/Twist]
/turtle1/color_sensor [turtlesim_msgs/msg/Color]
/turtle1/pose [turtlesim_msgs/msg/Pose]

$ ros2 topic type /turtle1/pose
turtlesim_msgs/msg/Pose
```

Полный `ros2 node info` обеих нод — в `graph-healthy.txt`.

### Ноды и их роли

| Нода | Роль | Публикует | Подписана на |
|---|---|---|---|
| `/turtlesim` | симулятор: окно, модель черепахи | `/turtle1/pose`, `/turtle1/color_sensor`, `/rosout`, `/parameter_events` | `/turtle1/cmd_vel`, `/parameter_events` |
| `/teleop_turtle` | пульт: превращает стрелки в команды скорости | `/turtle1/cmd_vel`, `/rosout`, `/parameter_events` | — |

Кроме того, у `/turtlesim` есть сервисы `/spawn`, `/kill`, `/clear`, `/reset`,
`/turtle1/set_pen`, `/turtle1/teleport_absolute`, `/turtle1/teleport_relative` и
action-сервер `/turtle1/rotate_absolute`. Клиент этого action — `/teleop_turtle`
(клавиши g|b|v|c|d|e|r|t).

### Топики и типы

| Топик | Тип | Кто → кому |
|---|---|---|
| `/turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | `/teleop_turtle` → `/turtlesim` |
| `/turtle1/pose` | `turtlesim_msgs/msg/Pose` | `/turtlesim` → подписчики (CLI) |
| `/turtle1/color_sensor` | `turtlesim_msgs/msg/Color` | `/turtlesim` → подписчики |
| `/rosout` | `rcl_interfaces/msg/Log` | все ноды → журнал |
| `/parameter_events` | `rcl_interfaces/msg/ParameterEvent` | события параметров |

В Lyrical тип позы — `turtlesim_msgs/msg/Pose`. В Jazzy было бы `turtlesim/msg/Pose`.

### Частота `/turtle1/pose`

`timeout -s INT 12s ros2 topic hz /turtle1/pose`: замер с 07:21:24Z по 07:21:37Z UTC
(~12 с). Черепаха неподвижна у стены.

```text
average rate: 62.708   (window: 62)
...
average rate: 62.520
	min: 0.010s max: 0.022s std dev: 0.00179s window: 688
```

Итог: **≈ 62,5 Гц** (688 сообщений за ~11 с). Это совпадает с ориентиром 60–62,5 Гц
(таймер turtlesim 16 мс). `hz_exit=124` — `hz` завершил `timeout` сигналом INT,
то же самое, что ручной Ctrl+C.

## 2. Сбой: teleop перезапущен в домене 17

Домены живых процессов (прочитаны из `/proc/<pid>/environ`), `domains-broken.txt`:

```text
pid=3802 ROS_DOMAIN_ID=16 /opt/ros/lyrical/lib/turtlesim/turtlesim_node
pid=4204 ROS_DOMAIN_ID=17 /opt/ros/lyrical/lib/turtlesim/turtle_teleop_key
```

Стрелки ← ← ↑ ↑ больше не меняют позу: до и после `theta: 0.09600000083446503`.

Проверка в C (домен 17), `test-broken.txt`:

```text
$ export ROS_DOMAIN_ID=17
$ ros2 node list --no-daemon --spin-time 2
/teleop_turtle
$ timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once > evidence/pr01/pose-broken.txt 2>&1
$ printf 'exit=%s\n' "$?"
exit=124
```

`POSE_TYPE=turtlesim_msgs/msg/Pose` — тип получен на шаге 1. `pose-broken.txt` пуст
(0 байт): за 5 секунд не пришло ни одного сообщения, ошибок импорта тоже нет.

## 3. Исправление: teleop перезапущен в домене 16

`domains-fixed.txt`:

```text
pid=3802 ROS_DOMAIN_ID=16 /opt/ros/lyrical/lib/turtlesim/turtlesim_node
pid=4486 ROS_DOMAIN_ID=16 /opt/ros/lyrical/lib/turtlesim/turtle_teleop_key
```

Та же проверка в C, изменены только домен и имя файла, `test-fixed.txt`:

```text
$ export ROS_DOMAIN_ID=16
$ ros2 node list --no-daemon --spin-time 2
/teleop_turtle
/turtlesim
$ timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once > evidence/pr01/pose-fixed.txt 2>&1
$ printf 'exit=%s\n' "$?"
exit=0
```

`pose-fixed.txt` содержит позу (`x: 11.088…, y: 5.743…, theta: 0.096`).
Стрелки снова управляют (`teleop-fixed.txt`): после двух нажатий «влево» `theta`
сменился с `0.096` на `-2.155`. Это +4 рад с переходом через ±π.

## 4. Сравнение «до / сбой / после»

| Стадия | turtlesim | teleop | CLI (C) | `node list` в домене C | echo `/turtle1/pose` | exit | Стрелки |
|---|---|---|---|---|---|---|---|
| До | 16 | 16 | 16 | `/teleop_turtle`, `/turtlesim` | поза приходит, ≈ 62,5 Гц | — | двигают |
| Сбой | 16 | 17 | 17 | только `/teleop_turtle` | пусто за 5 с | **124** | не двигают |
| После | 16 | 16 | 16 | `/teleop_turtle`, `/turtlesim` | поза пришла | **0** | двигают |

## 5. Причина

`ROS_DOMAIN_ID` задаёт номер DDS-домена. От него зависят UDP-порты обнаружения и
передачи данных, поэтому участники разных доменов не находят друг друга. Сообщение
доставляется только после обнаружения (discovery): издатель и подписчик должны встретиться
в одном домене. Teleop в домене 17 публиковал `/turtle1/cmd_vel`, но у этого топика не было
подписчика: симулятор находился в домене 16. Подписчик CLI в домене 17 видел только teleop
и не нашёл издателя `/turtle1/pose`, поэтому `echo` ждал до истечения таймаута (exit 124).

**Почему пришлось перезапускать teleop.** Домен читается из окружения один раз, при
создании контекста ноды (`rclpy.init`/`rclcpp::init`). `export ROS_DOMAIN_ID=16` в
терминале меняет окружение только для процессов, которые запустятся после этого.
Уже работающую ноду он не перенастраивает.

**Почему не меняли симулятор и установку.** Симулятор и так был в правильном домене 16,
и граф на шаге 1 работал в той же установке. Неисправность была не в ROS, а в параметре
запуска одного участника. Исправили именно её — вернули teleop в домен 16.
