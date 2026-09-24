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

CI (`.github/workflows/ci.yml`) проверяет JSON среды и комплектность evidence через
зафиксированный course kit `v1-w03`. Живой опыт выполняется локально.
