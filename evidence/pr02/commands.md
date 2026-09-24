# ПР02. Команды: терминал, пакет, launch, сбой имени топика

Среда из ПР01: Docker `tiryoh/ros2-desktop-vnc:lyrical-20260906T0836`, ROS 2 Lyrical,
`ROS_DOMAIN_ID=16`. Workspace `/home/ubuntu/robotics_ws` — корень Git-репозитория.
Опыт проведён 2026-09-24. Команды выполнялись в контейнере через `bash -c`, `set -x`
печатает каждую команду строкой `+ …`. Сырой вывод лежит в соседних файлах:
`workspace.txt`, `pkg-create.txt`, `build-empty.txt`, `build.txt`,
`launch-start-stop.txt`, `cmd-once.txt`, `cmd-broken.txt`, `cmd-fixed.txt`.

## 1. Три команды Linux

| Команда | Зачем | Мой результат |
|---|---|---|
| `cd "$(git rev-parse --show-toplevel)"; pwd` | Перейти в корень репозитория, где бы ни был терминал, и убедиться, где мы | `/home/ubuntu/robotics_ws` — это workspace, а не установка ROS |
| `ros2 pkg prefix turtlesim` | Узнать, где **установлен** пакет | `/opt/ros/lyrical`: turtlesim — часть системной установки. У своего пакета после сборки — `/home/ubuntu/robotics_ws/install/turtle_bringup` |
| `set -o pipefail; colcon build … 2>&1 \| tee evidence/pr02/build.txt` | Собрать пакет, показать лог на экране и одновременно сохранить его в файл, не потеряв код ошибки | `Summary: 1 package finished`, `build_exit=0`. Лог в `build.txt` |

(`workspace.txt`: `ls -a` показал скрытые `.git`, `.github`, `.gitignore`, `.course-kit`.
`printenv ROS_DISTRO ROS_DOMAIN_ID` → `lyrical`, `16`.)

**`>` против `|`.** `>` перенаправляет stdout команды **в файл** и перезаписывает его;
`2>&1` отправляет туда же stderr. `|` передаёт stdout **на вход следующей команде**: здесь
`tee`, который и печатает, и пишет в файл. Без `pipefail` код возврата конвейера — это
код последней команды (`tee`, почти всегда 0), и упавшая сборка выглядела бы успешной.

**`source` против запуска программы.** `source install/setup.bash` выполняет скрипт
**в текущем shell**: переменные (`AMENT_PREFIX_PATH`, `PYTHONPATH`, `PATH`) меняются
в этом же терминале, и после этого `ros2` находит пакет. Запуск `bash install/setup.bash`
или любой программы создаёт **дочерний процесс**: он получает копию окружения, и его
изменения исчезают вместе с ним. `source` не запускает ноды — после него граф пуст.

## 2. Пакет и сборка

```text
$ ros2 pkg create --build-type ament_python --license Apache-2.0 \
    turtle_bringup --dependencies launch launch_ros turtlesim
$ ls src/turtle_bringup
LICENSE  package.xml  resource  setup.cfg  setup.py  test  turtle_bringup
```

В `package.xml` и `setup.py` заменены описание и сопровождающий. Зависимости `launch`,
`launch_ros`, `turtlesim` сохранены.

Пустой пакет (`build-empty.txt`): `Finished <<< turtle_bringup`, `build_exit=0`.
После `source install/setup.bash`:

```text
$ ros2 pkg prefix turtle_bringup
/home/ubuntu/robotics_ws/install/turtle_bringup
$ ros2 node list --no-daemon --spin-time 2
(пусто)
```

Пакет найден, а нод нет: сборка и `source` не запускают процессы.

После добавления `launch/sim.launch.py` и записи в `data_files` (`build.txt`):

```text
$ ls -l "$(ros2 pkg prefix turtle_bringup)/share/turtle_bringup/launch"
sim.launch.py -> /home/ubuntu/robotics_ws/build/turtle_bringup/launch/sim.launch.py
$ python3 -m py_compile src/turtle_bringup/launch/sim.launch.py
py_compile_ok
```

`ros2 launch` ищет файл в `install/…/share/turtle_bringup/launch`, а не в `src`. Туда его
кладёт `data_files`. `--symlink-install` установил симлинк, поэтому правки в `src`
видны без пересборки.

## 3. Запуск и остановка launch (`launch-start-stop.txt`)

```text
$ ros2 launch turtle_bringup sim.launch.py        # терминал A
[INFO] [turtlesim_node-1]: process started with pid [21514]
$ ros2 node list --no-daemon --spin-time 2         # терминал C
/turtlesim
$ pgrep -a turtlesim_node
21514 /opt/ros/lyrical/lib/turtlesim/turtlesim_node --ros-args
# Ctrl+C (SIGINT) в A:
[WARNING] [launch]: user interrupted with ctrl-c (SIGINT)
[INFO] [turtlesim_node-1]: sending signal 'SIGINT' to process[turtlesim_node-1]
[INFO] [turtlesim_node-1]: process has finished cleanly [pid 21514]
$ pgrep -a turtlesim_node ; echo pgrep_exit=$?
pgrep_exit=1
$ ros2 node list --no-daemon --spin-time 2
(пусто)
```

Открылось одно окно, и запустилась одна нода. Launch управляет дочерним процессом:
по Ctrl+C он передаёт SIGINT в turtlesim и ждёт его завершения. Затем launch запущен
повторно для опыта ниже.

## 4. Команда вызывает движение (`cmd-once.txt`)

```text
$ ros2 topic type /turtle1/cmd_vel
geometry_msgs/msg/Twist
$ ros2 topic echo /turtle1/pose --once
x: 5.544444561004639  y: 5.544444561004639  theta: 0.0
$ ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
    '{linear: {x: 1.0}, angular: {z: 0.5}}'
publishing #1: geometry_msgs.msg.Twist(linear=…(x=1.0, …), angular=…(…, z=0.5))
$ sleep 2; ros2 topic echo /turtle1/pose --once
x: 6.509308815002441  y: 5.796990871429443  theta: 0.5040000081062317
linear_velocity: 0.0  angular_velocity: 0.0
```

Ожидание: вперёд на ~1 м с поворотом влево (против часовой) на ~0,5 рад.
turtlesim исполняет одну команду около 1 с, потом останавливается. Факт: x +0,96,
y +0,25, theta 0 → 0,504, скорость после остановки 0. Совпадает.

## 5. Сбой имени топика и исправление

### Сбой: издатель в `/cmd_vel` (`cmd-broken.txt`)

```text
$ ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
    /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 1.0}, angular: {z: 0.5}}'
publishing #1 … publishing #9          # сообщения реально отправлялись
$ ros2 topic info /cmd_vel --verbose
Type: geometry_msgs/msg/Twist
Publisher count: 1        Node name: _ros2cli_21986   Endpoint type: PUBLISHER
Subscription count: 0
$ ros2 topic info /turtle1/cmd_vel --verbose
Type: geometry_msgs/msg/Twist
Publisher count: 0
Subscription count: 1     Node name: turtlesim        Endpoint type: SUBSCRIPTION
$ ros2 topic echo /turtle1/pose --once
x: 6.509308815002441  y: 5.796990871429443  theta: 0.5040000081062317
linear_velocity: 0.0  angular_velocity: 0.0          # поза не изменилась
```

Издатель есть, и он обнаружен графом, но подписчика у его топика нет. Черепаха стоит.
`ros2 node list` показывал только `/turtlesim`: CLI-издатель `_ros2cli_…` скрыт, потому
что его имя начинается с `_`.

### Исправление: изменено только имя, `/cmd_vel` → `/turtle1/cmd_vel` (`cmd-fixed.txt`)

```text
$ ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
    /turtle1/cmd_vel geometry_msgs/msg/Twist '{linear: {x: 1.0}, angular: {z: 0.5}}'
$ ros2 topic info /cmd_vel --verbose
Unknown topic '/cmd_vel'
$ ros2 topic info /turtle1/cmd_vel --verbose
Publisher count: 1        Node name: _ros2cli_22190   Endpoint type: PUBLISHER
Subscription count: 1     Node name: turtlesim        Endpoint type: SUBSCRIPTION
$ ros2 topic echo /turtle1/pose --once              # во время публикации
x: 5.842424392700195  y: 9.520895004272461  theta: 2.9839999675750732
linear_velocity: 1.0  angular_velocity: 0.5
# Ctrl+C издателя, через 3 с:
x: 4.819915294647217  y: 9.411680221557617  theta: -2.7791852951049805
linear_velocity: 0.0  angular_velocity: 0.0
```

Скорость, тип и домен остались прежними. Черепаха поехала по дуге (R = v/ω = 2 м), а после
остановки издателя встала.

### Сравнение

| | Топик издателя | Издатели / подписчики этого топика | Подписчик turtlesim | Поза |
|---|---|---|---|---|
| До (шаг 4) | `/turtle1/cmd_vel` | 1 / 1 | `/turtle1/cmd_vel` | меняется |
| Сбой | `/cmd_vel` | 1 / **0** | `/turtle1/cmd_vel` (0 издателей) | не меняется |
| После | `/turtle1/cmd_vel` | 1 / 1 | `/turtle1/cmd_vel` | меняется (v=1.0, ω=0.5) |

### Почему правильного типа недостаточно

Издатель и подписчик соединяются, только если совпадают **полное имя топика**, тип
(и хэш типа) и совместимые QoS, и при этом они в одном домене. Имя — ключ, по которому
DDS сопоставляет конечные точки. `/cmd_vel` и `/turtle1/cmd_vel` — два разных топика, хотя
тип одинаковый. Turtlesim подписан на `turtle1/cmd_vel` в своём пространстве имён, то есть
полное имя — `/turtle1/cmd_vel`.

**Обнаружение и доставка.** Обнаружение (discovery) прошло: издатель `_ros2cli_…` виден
в графе, `topic info` показывает его конечную точку. Но доставки нет: сообщения идут
только к подписчикам **того же** топика, а у `/cmd_vel` их 0. `publishing #N` в логе
значит «отправлено», а не «кем-то получено». Проверять надо конечные точки
(`topic info --verbose`) и эффект (поза), а не вывод издателя.
