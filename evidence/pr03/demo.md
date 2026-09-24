# ПР03. Нода `patrol`: поза, таймер, команда

Среда: Docker `tiryoh/ros2-desktop-vnc:lyrical-20260906T0836`, ROS 2 Lyrical,
`ROS_DOMAIN_ID=16`. Опыт проведён 2026-09-24. turtlesim запускался launch-файлом из ПР02:
`ros2 launch turtle_bringup sim.launch.py`. Сырой вывод: `pkg-create.txt`,
`build-minimal.txt`, `minimal-node.txt`, `build.txt`, `tests.txt`, `run-broken.txt`,
`run-fixed.txt`, `stop.txt`.

## 1. Минимальная нода

```text
$ ros2 pkg create --build-type ament_python --license Apache-2.0 \
    --node-name patrol patrol --dependencies rclpy geometry_msgs
```

В `package.xml` добавлена зависимость `turtlesim_msgs`: в Lyrical тип позы —
`turtlesim_msgs/msg/Pose` (`ros2 topic type /turtle1/pose` в `run-broken.txt`).
Сначала `patrol.py` содержал только `rclpy.init` → `Node('patrol')` → `rclpy.spin`
(`minimal-node.txt`):

```text
$ ros2 node list --no-daemon --spin-time 2
/patrol
$ ros2 node info /patrol
  Subscribers:
  Publishers:
    /parameter_events, /rosout            # только служебные
```

Нода есть в графе, но своих входов и выходов у неё нет.

## 2. Устройство ноды (`src/patrol/patrol/patrol.py`)

- `Patrol.__init__`: `latest_pose = None`. Подписка на `/turtle1/pose` сохраняется в поле
  `self.pose_sub`. Издатель `Twist` публикует в **относительное** имя `cmd_vel`. Таймер
  с периодом `0.1` с хранится в `self.timer`.
- `on_pose` (callback подписки) только запоминает последнее сообщение.
- `on_timer` (callback таймера) публикует `choose_command(self.latest_pose)`.
- `choose_command(pose)` — чистая функция: без ROS-вызовов и побочных эффектов. `None` →
  нулевой Twist, любая поза → `linear.x=0.5`, `angular.z=0.3`.

Тесты (`tests.txt`): `python3 -m pytest src/patrol/test` дал `7 passed, 1 skipped`.
В том числе три unit-теста `choose_command`: нет позы → все поля 0; обычная поза →
0.5/0.3, остальные поля 0; команда не зависит от значений позы. Остальные тесты —
линтеры flake8, pep257, mypy, xmllint; copyright пропущен генератором пакета.
`colcon test` по `turtle_bringup` и `patrol`: `13 tests, 0 errors, 0 failures, 2 skipped`.

Сгенерированный `test_mypy.py` проверял текущий каталог. При запуске из корня workspace
mypy видел `build/patrol/setup.py` и `build/turtle_bringup/setup.py` и падал с
`Duplicate module named "setup"`. Теперь тест передаёт mypy каталог своего пакета.

## 3. Сбой: публикация в относительный `cmd_vel` (`run-broken.txt`)

```text
$ ros2 run patrol patrol
$ ros2 node info /patrol
  Subscribers:
    /turtle1/pose: turtlesim_msgs/msg/Pose
  Publishers:
    /cmd_vel: geometry_msgs/msg/Twist
$ ros2 topic info /cmd_vel --verbose
Publisher count: 1      Node name: patrol     Endpoint type: PUBLISHER
Subscription count: 0
$ ros2 topic info /turtle1/cmd_vel --verbose
Publisher count: 0
Subscription count: 1   Node name: turtlesim  Endpoint type: SUBSCRIPTION
$ ros2 topic echo /turtle1/pose --once ; sleep 3 ; ros2 topic echo /turtle1/pose --once
x: 5.544444561004639  y: 5.544444561004639  theta: 0.0  linear_velocity: 0.0   # оба раза
$ timeout -s INT 5s ros2 topic echo /cmd_vel --once
linear: {x: 0.5, …}  angular: {…, z: 0.3}
```

Поза до `patrol` доходит: в `/cmd_vel` уже идёт 0.5/0.3, а не нулевая команда. Команда
публикуется, но в топик без подписчиков. Черепаха стоит.

**Почему `/cmd_vel`.** Имя без `/` относительное. Оно разрешается от пространства имён
ноды. `patrol` запущен в корне `/`, поэтому `cmd_vel` → `/cmd_vel`, а turtlesim слушает
`/turtle1/cmd_vel`.

## 4. Исправление: remap при запуске (`run-fixed.txt`)

Код не менялся, изменена только команда запуска:

```text
$ ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
$ ros2 node info /patrol
  Subscribers:  /turtle1/pose: turtlesim_msgs/msg/Pose
  Publishers:   /turtle1/cmd_vel: geometry_msgs/msg/Twist
$ ros2 topic info /cmd_vel --verbose
Unknown topic '/cmd_vel'
$ ros2 topic info /turtle1/cmd_vel --verbose
Publisher count: 1      Node name: patrol
Subscription count: 1   Node name: turtlesim
$ ros2 topic echo /turtle1/pose --once
x: 6.901154041290283  y: 8.173527717590332  theta: 2.184000015258789
linear_velocity: 0.5  angular_velocity: 0.30000001192092896
```

Черепаха едет по окружности радиуса v/ω = 0.5/0.3 ≈ 1.67.

### Частота команды

`timeout -s INT 11s ros2 topic hz /turtle1/cmd_vel`, с 12:12:29Z по 12:12:41Z UTC:

```text
average rate: 9.984   window: 9
...
average rate: 9.999
	min: 0.091s max: 0.110s std dev: 0.00214s window: 99
```

Итог: **≈ 10,0 Гц**, окно 99 интервалов (~10 с). Это соответствует таймеру 0.1 с.
Отдельные периоды — от 91 до 110 мс: таймер задаёт намерение, фактический момент вызова
определяет исполнитель. `hz_exit=124` — `hz` остановил `timeout` сигналом INT,
то же, что Ctrl+C.

## 5. Остановка (`stop.txt`)

```text
stop patrol (SIGINT) at 12:12:58.560
last  moving sample: 12:12:59.561 linear_velocity=0.5
first stopped sample: 12:12:59.576 linear_velocity=0.0
$ pgrep -x patrol  -> exit 1;  ros2 node list -> /turtlesim
```

Процесс `patrol` завершился сразу и без трейсбека (лог пуст). Черепаха продолжала ехать ещё
**~1,0 с**: turtlesim исполняет последнюю полученную команду около секунды и только
потом останавливается. Исчезновение издателя — не команда торможения. Нулевой Twist
никто не отправлял.

## 6. Роли `init`, `spin`, callback и `Ctrl+C`

| Шаг | Что делает |
|---|---|
| `rclpy.init(args=args)` | Создаёт контекст ROS: читает `--ros-args` (в том числе remap `-r cmd_vel:=…`) и окружение (`ROS_DOMAIN_ID`). Подключается к DDS. Без него ноду не создать. |
| `Patrol()` | Регистрирует ноду `/patrol`, подписку, издатель и таймер. Это только объявления: сами по себе они ничего не вызывают. |
| `rclpy.spin(node)` | Исполнитель (executor) в цикле ждёт готовую работу: пришло сообщение, истёк таймер. Он и вызывает соответствующий callback. Без `spin` сообщения копятся в очереди, а таймер не срабатывает. |
| callback (`on_pose`, `on_timer`) | Короткий обработчик события. Его вызывает исполнитель внутри `spin`, а не издатель. Он должен быстро вернуться: пока он работает, однопоточный исполнитель не вызывает другие обработчики. |
| `Ctrl+C` | SIGINT. `spin` прерывается `KeyboardInterrupt`, `except` его гасит, в `finally` вызываются `destroy_node()` и `try_shutdown()`. Нода уходит из графа, а последняя команда в turtlesim продолжает действовать ~1 с. |

Сама подписка ещё не означает, что поза получена. Поэтому до первого `on_pose`
`latest_pose is None`, и таймер публикует нулевую команду.
