# ПР05. Одна команда запуска, QoS и повтор MCAP

Опыт 2026-10-07, ROS 2 Lyrical в контейнере `ros2`, ROS_DOMAIN_ID=16.
Нода turtlesim глобальная; `/robot_a/patrol`, `/robot_a/pose_relay` и
`/robot_a/pose_subscriber` запускаются через `course_bringup/patrol.launch.py`.
Имена внутри нод относительные; входы позы и выход patrol переназначаются на
глобальную черепаху. Это не связывает надёжность сенсорного потока с контроллером:
patrol получает исходную позу, а эксперимент проводится на выходе relay.

## Собрать и сломать

```bash
ros2 launch course_bringup patrol.launch.py namespace:=robot_a \
  subscriber_reliability:=reliable record:=false
```

В `qos-before.txt`: граф содержит три ноды `/robot_a/*` и `/turtlesim`;
`topic list` показывает `/robot_a/sensor_pose`; `topic info --verbose` показывает
издателя BEST_EFFORT и подписчика RELIABLE. Recorder отсутствует (pgrep exit=1).
Подписчик каждую секунду пишет `received=0`, DDS предупреждает
`offering incompatible QoS ... Last incompatible policy: RELIABILITY`.

Та же диагностика через независимого CLI-подписчика:

```bash
timeout -s INT 3s ros2 topic echo /robot_a/sensor_pose \
  --qos-reliability reliable --once
# reliable_echo_exit=124
```

Причина: reliable-подписчик требует гарантию доставки, которую best_effort-издатель
не предлагает. Обнаружение топика работает, но совместимости конечных точек нет.
Одно наличие имени и совпадение типа не доказывает доставку.

## Исправить и записать

Первый launch остановлен SIGINT, затем:

```bash
ros2 launch course_bringup patrol.launch.py namespace:=robot_a \
  subscriber_reliability:=best_effort record:=true bag_dir:=evidence/pr05/bag
```

Запись запускается условно через `IfCondition(record)`, а не Python `if` от
LaunchConfiguration. Аргумент `bag_dir` передаётся recorder, он записывает только
сенсорный топик в MCAP; в Lyrical используется явный `--topics`.

`qos-after.txt`: издатель и подписчики BEST_EFFORT; CLI echo с best_effort завершился
с exit=0 и вернул Pose. Живая частота ~62.492 Гц; счётчик отдельного подписчика
вырос до 1104. На `/turtle1/cmd_vel` видна команда patrol (0.5 м/с, 0.3 рад/с).

Launch остановлен SIGINT: все дочерние процессы, включая recorder, завершились
штатно. В `ros2 bag info`:

- Storage id: mcap;
- длительность 18.062218911 с;
- 1120 сообщений;
- один топик `/robot_a/sensor_pose`, тип `turtlesim_msgs/msg/Pose`.

`bag-metadata.yaml` скопирован из финализированного `bag/metadata.yaml`, а сама запись
сохранена в `bag/`. Это один и тот же набор входных сообщений для обеих replay-проверок.

## Проверить тот же bag до/после

Живой launch полностью остановлен. Запущены только player и отдельный подписчик:

```bash
ros2 bag play evidence/pr05/bag --loop \
  --qos-profile-overrides-path config/qos-overrides.yaml
ros2 run course_bringup pose_subscriber --ros-args \
  -r __ns:=/robot_a -p reliability:=reliable
```

Override закрепляет best_effort у player: без него профиль проигрывателя мог бы
скрыть исходную несовместимость. `topic info` показывает ровно одного издателя —
rosbag2_player, BEST_EFFORT. В графе нет relay, patrol и turtlesim.

Повтор того же reliable echo: timeout, `replay_reliable_exit=124`; отдельный
подписчик остаётся на `received=0`. Вывод дописан в `qos-before.txt`.

Подписчик остановлен и запущен с `reliability:=best_effort`, player продолжает
циклически проигрывать ту же запись. Тот же best_effort echo завершается с exit=0;
счётчик подписчика растёт до 853. Вывод в `qos-after.txt`.
Частота за короткое окно ~59.536 Гц: окно захватило паузу на границе повторения bag;
это не отсутствие доставки. В обоих опытах профиль CLI задаётся явно, чтобы
автоматический выбор QoS не скрывал дефект.

После опыта player и подписчик остановлены; `ros2 node list --no-daemon` пуст.

## Тесты

`tests.txt`: patrol — 32 passed, 1 skipped; course_bringup — 10 passed, 1 skipped;
colcon по всем трём пакетам — 49 tests, 0 errors, 0 failures, 3 skipped.
Пропущенные copyright-тесты отключены генератором ROS-пакетов.
Проверены профили QoS, ошибочная reliability, разрешение относительных имён,
счётчик подписчика, launch-аргументы, условный recorder и совпадение override-файлов.
Предыдущие тесты параметров patrol проходят без изменений.

Первый пробный вызов pytest сразу по двум пакетам столкнулся с одинаковыми именами
сгенерированных test_*.py. Исправлен способ запуска: pytest отдельно для каждого
пакета, как делает colcon. Финальный tests.txt содержит повторную успешную проверку.
