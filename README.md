# Робототехника (НГУ) — практические работы по ROS 2

Корень репозитория — ROS 2 workspace: `src/` (пакеты), `evidence/prNN/` (результаты
проверок), `AI_USAGE.md` (декларация использования ИИ).

## Среда

- ROS 2 Lyrical, Ubuntu 26.04.1, RMW `rmw_fastrtps_cpp`.
- Docker-образ `tiryoh/ros2-desktop-vnc:lyrical-20260906T0836`
  (`sha256:23bbfbd0bac264da8ef39fb599b9d58b209b06603b49e979eba8021286c56b6e`), macOS arm64.
  Workspace смонтирован в контейнер как `/home/ubuntu/robotics_ws`, рабочий стол — noVNC.
- Домены: рабочий `16`, для опыта с разрывом — `17`.

## Course kit

```bash
curl -fsSLO https://ros.lms.ci.nsu.ru/downloads/robotics-course-kit-v1-w06-6eda53e1c566.tar.gz
curl -fsSLO https://ros.lms.ci.nsu.ru/downloads/robotics-course-kit-v1-w06-6eda53e1c566.tar.gz.sha256.txt
sha256sum -c robotics-course-kit-v1-w06-6eda53e1c566.tar.gz.sha256.txt
mkdir -p .course-kit && tar -xzf robotics-course-kit-v1-w06-6eda53e1c566.tar.gz -C .course-kit
```

## ПР01. Окружение и граф turtlesim

В каждом из трёх терминалов (A, B, C) одного контейнера:

```bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=16
```

1. Отчёт среды (C, из корня репозитория):
   ```bash
   mkdir -p evidence/pr01
   ros2 doctor --report > evidence/pr01/doctor.txt 2>&1
   ```
2. Исправный граф:
   ```bash
   ros2 run turtlesim turtlesim_node        # A
   ros2 run turtlesim turtle_teleop_key     # B, стрелки двигают черепаху
   # C:
   ros2 node list --no-daemon --spin-time 2
   ros2 topic list -t
   ros2 node info /turtlesim
   POSE_TYPE=$(ros2 topic type /turtle1/pose)   # turtlesim_msgs/msg/Pose
   ros2 topic echo /turtle1/pose --once
   ros2 topic hz /turtle1/pose                  # >= 10 с, затем Ctrl+C
   ```
3. Сбой: в B `Ctrl+C`, затем `export ROS_DOMAIN_ID=17` и снова запустить teleop. В C:
   ```bash
   export ROS_DOMAIN_ID=17
   ros2 node list --no-daemon --spin-time 2
   timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once > evidence/pr01/pose-broken.txt 2>&1
   printf 'exit=%s\n' "$?"     # ожидается exit=124
   ```
4. Исправление: в B `Ctrl+C`, `export ROS_DOMAIN_ID=16`, снова запустить teleop. В C — та же
   проверка с `ROS_DOMAIN_ID=16` и файлом `pose-fixed.txt` (ожидается `exit=0`).
5. Проверка сдачи:
   ```bash
   python3 -m json.tool evidence/pr01/environment.json > /dev/null
   python3 .course-kit/v1/tools/check_practice.py PR01 --submission .
   ```

## ПР02. Пакет `turtle_bringup` и launch turtlesim

Пакет `src/turtle_bringup` (ament_python) устанавливает `launch/sim.launch.py`,
который запускает готовую ноду `turtlesim_node`.

```bash
source /opt/ros/lyrical/setup.bash
set -o pipefail
colcon build --symlink-install --packages-select turtle_bringup 2>&1 | tee evidence/pr02/build.txt
source install/setup.bash
export ROS_DOMAIN_ID=16
ros2 launch turtle_bringup sim.launch.py            # A; остановка — Ctrl+C
# B: одна команда движения
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist '{linear: {x: 1.0}, angular: {z: 0.5}}'
# сбой имени: издатель без подписчика
ros2 topic pub --rate 1 --wait-matching-subscriptions 0 /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 1.0}, angular: {z: 0.5}}'
ros2 topic info /cmd_vel --verbose                  # C: Subscription count: 0
# исправление: только имя /cmd_vel -> /turtle1/cmd_vel, та же проверка
```

Проверка сдачи:

```bash
python3 -m py_compile src/turtle_bringup/launch/sim.launch.py
python3 .course-kit/v1/tools/check_practice.py PR02 --submission .
```

## ПР03. Нода `patrol`

Пакет `src/patrol` (ament_python), команда `patrol`. Подписка на `/turtle1/pose` хранит
последнюю позу. Таймер 0.1 с публикует `geometry_msgs/msg/Twist` в относительный
`cmd_vel`: нулевой до первой позы, затем `linear.x=0.5`, `angular.z=0.3`. Выбор команды
вынесен в чистую функцию `choose_command`.

```bash
source /opt/ros/lyrical/setup.bash
colcon build --symlink-install --packages-select patrol
source install/setup.bash
python3 -m pytest src/patrol/test
ros2 launch turtle_bringup sim.launch.py                         # A
ros2 run patrol patrol                                           # B: сбой, публикует в /cmd_vel
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel   # B: исправление
ros2 topic info /turtle1/cmd_vel --verbose                       # C
ros2 topic hz /turtle1/cmd_vel                                   # C: ~10 Гц
python3 .course-kit/v1/tools/check_practice.py PR03 --submission .
```

## ПР04. Параметры `patrol`

Параметры `linear_speed` (0.5, допустимо 0–1 м/с), `turn_rate` (0.3, −1–1 рад/с) и
`publish_hz` (10.0, 1–30 Гц). Набор значений проверяет чистая функция `validate_values`
в on-set callback до изменения состояния. Post-set callback обновляет поля и при новой
частоте останавливает и удаляет старый таймер, затем создаёт новый с периодом `1/publish_hz`.

```bash
python3 -m pytest src/patrol/test
ros2 launch turtle_bringup sim.launch.py                         # A
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel   # B
ros2 param get /patrol publish_hz                                # C
ros2 param set /patrol publish_hz 5.0                            # C: принято, ~5 Гц
ros2 param set /patrol publish_hz 0.0                            # C: отклонено, остаётся 5.0
ros2 topic hz /turtle1/cmd_vel
python3 .course-kit/v1/tools/check_practice.py PR04 --submission .
```

Дефект (проверка частоты отключена) лежит в отдельной ветке `pr04-defect`.

## ПР05. Launch, QoS и replay

`course_bringup` поднимает глобальный turtlesim и ноды `patrol`, `pose_relay`,
`pose_subscriber` в выбранном namespace. `patrol` использует относительный вход
`turtle1/pose` (в корне прежнее полное имя), launch переназначает его на `/turtle1/pose`,
а выход `cmd_vel` — на `/turtle1/cmd_vel`. Relay публикует `sensor_pose` с best_effort.

```bash
# До: reliable несовместим с best_effort, сообщений нет.
ros2 launch course_bringup patrol.launch.py namespace:=robot_a \
  subscriber_reliability:=reliable record:=false
# После остановки первого запуска: best_effort и запись одного потока в MCAP.
# bag_dir должен быть новым, существующая запись не перезаписывается.
ros2 launch course_bringup patrol.launch.py namespace:=robot_a \
  subscriber_reliability:=best_effort record:=true bag_dir:=my_bag
# Остановить launch через Ctrl+C, затем воспроизвести сохранённый bag:
ros2 bag play evidence/pr05/bag --loop \
  --qos-profile-overrides-path config/qos-overrides.yaml
# В другом терминале сравнить reliable и best_effort:
timeout 3s ros2 topic echo /robot_a/sensor_pose --qos-reliability reliable --once
timeout 3s ros2 topic echo /robot_a/sensor_pose --qos-reliability best_effort --once
```

Аргументы: `namespace`, `record`, `bag_dir`, `subscriber_reliability`.
При `record=false` recorder не запускается (`IfCondition`). Override для replay закреплён
за `/robot_a/sensor_pose`; для другого namespace нужно изменить ключ в YAML.
Реальные логи и единственная запись: `evidence/pr05/`, разбор — `demo.md`.

## ПР06. Модель и tf

`course_description` содержит Xacro Ackermann-модели по размерам SDF из kit w06.
X вперёд, Y влево, Z вверх, метры/килограммы/секунды. Параметры: `wheelbase=0.8`,
`track=0.62`, `wheel_radius=0.12`. Сенсоры fixed от `base_link`, колёса подвижные.

```bash
ros2 launch course_description display.launch.py
# Без GUI для проверки tf:
ros2 launch course_description display.launch.py rviz:=false
# Для отображения колёс в уже работающем RViz, отдельный терминал:
ros2 topic pub -r 10 /joint_states sensor_msgs/msg/JointState \
  '{header: auto, name: [front_left_steering_joint, front_right_steering_joint, front_left_wheel_joint, front_right_wheel_joint, rear_left_wheel_joint, rear_right_wheel_joint], position: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}'
```

Не запускайте два display.launch одновременно. RViz использует Fixed Frame `base_link`.
Размеры датчиков для визуализации условные: SDF задаёт их poses, но не геометрию.
Инерции рассчитаны по геометрии, а не скопированы в неверный frame из SDF.
Дефект parent лидара — отдельная ветка `pr06-defect`, в main его нет.
Разбор, таблица фреймов, QoS и скриншот: `evidence/pr06/`.

## CI

`.github/workflows/ci.yml` проверяет JSON среды ПР01, ставит зависимости через
`rosdep`, собирает все пакеты, проверяет установленные launch-файлы и запускает
`colcon test` и отдельные pytest. Для ПР06 разворачивает установленный Xacro и запускает
`check_urdf`. После этого скачивает kit `v1-w06` и запускает checker PR06.
Живые опыты и RViz проверяются локально.
