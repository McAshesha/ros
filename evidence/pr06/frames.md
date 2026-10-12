# ПР06. Фреймы и владельцы преобразований

Источник размеров: `models/course_ackermann/model.sdf` из kit v1-w06,
SHA256 `6eda53e1c566f7f0a7e09d7afe1e5a6f3b98397175a7e57dede9a84c6d14d0fe`.
Модель: `src/course_description/urdf/vehicle.urdf.xacro`.
СИ; REP-103: X вперёд, Y влево, Z вверх. Начало base_link совпадает с модельным
фреймом SDF на высоте осей колёс. SDF pose модели в мире (Z=0.18) не добавлен
к локальным offsets: world/map/odom в ПР06 не публикуются.

## Геометрия

База 0.8 м, колея 0.62 м, радиус колеса 0.12 м, ширина 0.07 м; эти первые три
величины — аргументы Xacro и launch. Корпус 1.05 × 0.52 × 0.22 м, центр геометрии
и массы (0, 0, 0.12), масса 12 кг. Колёса 0.8 кг каждое, кулаки 0.2 кг каждый,
сенсоры по 0.1/3 кг; всего 15.7 кг.

Visual и collision заданы отдельно. Размеры боксов камеры/лидара/IMU условные для
визуализации: исходный SDF задаёт их poses, но не visual/collision. Все три сенсора
в исходнике совпадают по положению, поэтому на скриншоте накладываются.
Инерции вычислены по размерам box/cylinder. Цилиндр колеса развёрнут вдоль Y в
visual/collision, его тензор выражен в неповёрнутом wheel_link (iyy — осевой момент).
Скопированные Gazebo-плагины отсутствуют.

## Дерево

Владелец **каждой** связи ниже — единственный `robot_state_publisher`.
Во время проверки колёс отдельный `ros2 topic pub` публикует только `/joint_states`,
не tf. RViz и диагностические инструменты лишь подписчики.

| Parent | Child | Joint / канал | Ожидаемый XYZ, м / вращение |
|---|---|---|---|
| base_link | camera_link | camera_joint fixed, /tf_static | (0.28, 0, 0.38), RPY=0 |
| base_link | lidar_link | lidar_joint fixed, /tf_static | (0.28, 0, 0.38), RPY=0 |
| base_link | imu_link | imu_joint fixed, /tf_static | (0.28, 0, 0.38), RPY=0 |
| base_link | front_left_knuckle_link | front_left_steering_joint revolute, /tf | (0.40, 0.31, 0), поворот вокруг Z |
| base_link | front_right_knuckle_link | front_right_steering_joint revolute, /tf | (0.40, −0.31, 0), поворот вокруг Z |
| front_left_knuckle_link | front_left_wheel_link | front_left_wheel_joint continuous, /tf | (0, 0, 0), вращение вокруг Y |
| front_right_knuckle_link | front_right_wheel_link | front_right_wheel_joint continuous, /tf | (0, 0, 0), вращение вокруг Y |
| base_link | rear_left_wheel_link | rear_left_wheel_joint continuous, /tf | (−0.40, 0.31, 0), вращение вокруг Y |
| base_link | rear_right_wheel_link | rear_right_wheel_joint continuous, /tf | (−0.40, −0.31, 0), вращение вокруг Y |

При нулевых joint_states вращения равны 0. Без joint_states fixed-сенсоры доступны
сразу, а подвижные колёса в tf не обязаны появиться. Это не разрыв URDF-дерева.
KDL предупреждает об инерции корневого звена; здесь это не мешает RSP публиковать tf,
поскольку динамика не рассчитывается.

## Собрать

```bash
colcon build --symlink-install
xacro src/course_description/urdf/vehicle.urdf.xacro > log/vehicle.urdf
check_urdf log/vehicle.urdf
ros2 launch course_description display.launch.py
ros2 run tf2_ros tf2_echo base_link lidar_link
ros2 run tf2_tools view_frames
```

`check_urdf`: Successfully Parsed XML, корень base_link, 7 непосредственных детей.
`tf2_echo`: Translation [0.280, 0.000, 0.380], Quaternion [0, 0, 0, 1].
RViz `Fixed Frame=base_link`, `Global Status: Ok`; реальный скриншот `rviz.png`.
Для видимости колёс вручную переданы все шесть нулевых joint_states (команда README).
Полное исправное дерево: `frames_2026-10-12_15.34.12.gv/.pdf`.

## Сломать

Ветка `pr06-defect`, коммит `33b86c86eac598216b89ce830dd23d4b88f79d29`.
Единственное изменение — `lidar_joint` parent с base_link на camera_link, offset
остался (0.28, 0, 0.38).

`check_urdf` всё ещё exit=0: дерево формально связное и ацикличное. Но
`test_sensor_parent_and_offset[lidar_link]` падает: ожидался base_link, получен
camera_link (1 failed, 7 passed). Живой `tf2_echo base_link lidar_link` показывает
[0.560, 0.000, 0.760] — два одинаковых offsets сложились. Дефектное дерево:
`frames_2026-10-12_15.36.54.gv/.pdf`.

## Доказать

Старый launch остановлен SIGINT, выполнен `git switch main`, затем тот же launch,
тот же tf2_echo и тот же тест. В `tf-fixed.txt`: [0.280, 0.000, 0.380], 8 model-тестов
passed, check_urdf exit=0. В main дефекта нет. Финальные тесты всех пакетов:
62 tests, 0 errors, 0 failures, 4 skipped; пропуски — copyright от генератора.

`model-check.txt` содержит реальные выводы команд исправной модели и повторные
проверки до/после. Все launch-процессы останавливались перед перезапуском;
после последней проверки node list пустой. Единственного издателя `/tf_static`
подтверждает `tf-qos.txt`.

## QoS и время

В том же работающем RSP поздний reliable/transient_local echo получил три fixed
преобразования (exit=0), поздний reliable/volatile echo — timeout (exit=124).
GID издателя до и после совпадает; во время проверки RSP не перезапускался.
Подвижные преобразования во время публикации joint_states обновлялись на `/tf`;
fixed имеют timestamp стартовой публикации и доступны через transient-local историю.
При выборе map/odom как Fixed Frame ошибка ожидаема: таких фреймов здесь нет.
