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
curl -fsSLO https://ros.lms.ci.nsu.ru/downloads/robotics-course-kit-v1-w03-7fbfd3e8161a.tar.gz
curl -fsSLO https://ros.lms.ci.nsu.ru/downloads/robotics-course-kit-v1-w03-7fbfd3e8161a.tar.gz.sha256.txt
sha256sum -c robotics-course-kit-v1-w03-7fbfd3e8161a.tar.gz.sha256.txt
mkdir -p .course-kit && tar -xzf robotics-course-kit-v1-w03-7fbfd3e8161a.tar.gz -C .course-kit
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

## CI

`.github/workflows/ci.yml` проверяет JSON среды ПР01, собирает `turtle_bringup` и
проверяет установленный `sim.launch.py`. Затем скачивает зафиксированный course kit
`v1-w03` и запускает checker текущей ПР. Живой опыт с GUI выполняется локально.
