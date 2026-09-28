# ПР04. Параметры `patrol`: скорость, поворот, частота

Среда: Docker `tiryoh/ros2-desktop-vnc:lyrical-20260906T0836`, ROS 2 Lyrical,
`ROS_DOMAIN_ID=16`. Опыт проведён 2026-09-28. turtlesim запускался командой
`ros2 launch turtle_bringup sim.launch.py`, patrol — командой
`ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel`.

Сырой вывод: `run-healthy.txt` (исправная версия, 10 → 5 Гц), `run-broken.txt`
(ветка `pr04-defect`, передан 0), `tests-broken.txt` (тот же тест на ветке с дефектом),
`run-fixed.txt` (`main`, та же проверка), `tests.txt`, `services-actions.txt`.

## 1. Устройство (`src/patrol/patrol/patrol.py`, коммит `335f491`)

| Параметр | По умолчанию | Допустимо |
|---|---|---|
| `linear_speed` | 0.5 м/с | конечное число 0–1 |
| `turn_rate` | 0.3 рад/с | конечное число −1–1 |
| `publish_hz` | 10.0 Гц | конечное число 1–30 |

- `validate_values(publish_hz, linear_speed, turn_rate)` — чистая функция. Возвращает
  `(ok, reason)` и отклоняет не числа, NaN, ±inf и значения вне диапазона.
- `validate` — on-set callback. Собирает предложенный набор: новые значения берутся из
  запроса, остальные из текущих полей. Весь набор проверяется через `validate_values`.
  Состояние ноды callback не меняет: он только возвращает `SetParametersResult`.
- `apply` — post-set callback, вызывается только после принятия. Он обновляет поля.
  Если изменилась частота, вызывает `timer.cancel()` и `destroy_timer(старый)`, затем
  создаёт новый таймер с периодом `1/publish_hz`. Смена скорости таймер не трогает:
  `on_timer` каждый раз читает актуальные поля.
- Значения, заданные при запуске (`-p publish_hz:=…`), проверяются в `__init__` до
  создания таймера.

## 2. Собрать: 10 → 5 Гц (`run-healthy.txt`)

```text
$ ros2 param list /patrol
  linear_speed  publish_hz  start_type_description_service  turn_rate  use_sim_time
$ ros2 param get /patrol publish_hz
Double value is: 10.0
$ timeout -s INT 11s ros2 topic hz /turtle1/cmd_vel        # 12:25:57Z
average rate: 10.003
	min: 0.095s max: 0.105s std dev: 0.00176s window: 99
$ ros2 param set /patrol publish_hz 5.0
Set parameter successful
$ ros2 param get /patrol publish_hz
Double value is: 5.0
$ timeout -s INT 11s ros2 topic hz /turtle1/cmd_vel        # 12:26:11Z
average rate: 5.000
	min: 0.196s max: 0.205s std dev: 0.00221s window: 49
--- лог patrol:
[INFO] [patrol]: publish_hz 10.0 -> 5.0, timer period 0.200 s
```

`get` показывает принятое значение, `hz` — изменившийся поток: за те же ~10 с
99 интервалов по ~0,1 с сменились 49 интервалами по ~0,2 с.

## 3. Сломать: проверка частоты отключена, передан 0 (`run-broken.txt`)

Ветка `pr04-defect`, коммит `1504164` поверх `335f491`. Единственное изменение: в
`validate` вместо предложенной частоты проверяется текущая `self.publish_hz`. Поэтому
любое новое `publish_hz` принимается без проверки.

```text
$ ros2 param set /patrol publish_hz 5.0
Set parameter successful
$ timeout -s INT 6s ros2 topic hz /turtle1/cmd_vel
average rate: 4.999   window: 24
$ timeout -s INT 15s ros2 param set /patrol publish_hz 0.0   # 12:30:30Z
set_exit=124                                   # ответа нет, CLI остановлен timeout
$ ros2 node list --no-daemon --spin-time 2
/turtlesim                                     # /patrol исчез
$ pgrep -x patrol
pgrep_exit=1
$ timeout -s INT 6s ros2 topic hz /turtle1/cmd_vel
hz_exit=124                                    # ни одного сообщения
$ ros2 topic info /turtle1/cmd_vel
Publisher count: 0
Subscription count: 1
$ ros2 topic echo /turtle1/pose --once --field linear_velocity
0.0
--- лог patrol:
  File ".../rclpy/parameter_service.py", line 142, in _set_parameters_callback
  File ".../rclpy/node.py", line 1038, in _call_post_set_parameters_callback
  File "/home/ubuntu/robotics_ws/build/patrol/patrol/patrol.py", line 90, in apply
    self.timer = self.create_timer(1.0 / self.publish_hz, self.on_timer)
ZeroDivisionError: division by zero
[ros2run]: Process exited with failure 1
```

Воспроизводимый отказ: `0.0` принят, post-set callback к этому моменту уже остановил и
удалил старый таймер, а новый создать не смог: `1.0 / 0.0` → `ZeroDivisionError`.
Исключение вылетело из сервиса параметров в `rclpy.spin`, и процесс завершился. Клиент
`ros2 param set` ответа так и не получил. Поток команд оборвался, издателей в
`/turtle1/cmd_vel` 0, черепаха остановилась.

Тот же тест ноды на этой ветке (`tests-broken.txt`) — 4 failed, 3 passed:

```text
test_bad_rate_keeps_value_and_timer[0.0]   FAILED  ZeroDivisionError: division by zero
test_bad_rate_keeps_value_and_timer[-1.0]  FAILED  RCLError: failed to create timer: timer period must be non-negative
test_bad_rate_keeps_value_and_timer[nan]   FAILED  ValueError: cannot convert float NaN to integer
test_bad_set_is_rejected_as_a_whole        FAILED  ZeroDivisionError: division by zero
```

**Первопричина.** Предложенная частота вообще не проверялась, поэтому недопустимый 0 дошёл
до `apply`. Отказ возник уже там, когда активное состояние было наполовину разрушено:
старый таймер удалён, нового нет. Проверка должна отклонить набор в on-set callback, до любых
изменений.

## 4. Доказать: проверка возвращена, та же проверка (`run-fixed.txt`)

`main`, коммит `335f491`.

```text
$ ros2 param set /patrol publish_hz 5.0
Set parameter successful
$ timeout -s INT 15s ros2 param set /patrol publish_hz 0.0     # 12:31:37Z
Setting parameter failed: publish_hz=0.0 is outside [1.0, 30.0]
$ ros2 param set /patrol publish_hz -1.0
Setting parameter failed: publish_hz=-1.0 is outside [1.0, 30.0]
$ ros2 param set /patrol publish_hz .nan
Setting parameter failed: publish_hz=nan is outside [1.0, 30.0]
$ ros2 param set /patrol publish_hz 31.0
Setting parameter failed: publish_hz=31.0 is outside [1.0, 30.0]
$ ros2 param get /patrol publish_hz
Double value is: 5.0
$ ros2 node list --no-daemon --spin-time 2
/patrol
/turtlesim
$ timeout -s INT 11s ros2 topic hz /turtle1/cmd_vel            # 12:31:45Z
average rate: 4.998
	min: 0.196s max: 0.204s std dev: 0.00201s window: 49
$ ros2 topic info /turtle1/cmd_vel
Publisher count: 1
Subscription count: 1
```

Ноль отклонён с причиной, значение осталось 5.0, нода жива, поток продолжается на
~5 Гц. В логе ноды одна перестройка таймера `10.0 -> 5.0`. На отклонённые значения
перестроек нет. Тот же тест на `main` проходит полностью (`tests.txt`).

Допустимые изменения после отказа работают:

```text
$ ros2 param set /patrol linear_speed 0.8
Set parameter successful
$ ros2 param set /patrol linear_speed 1.5
Setting parameter failed: linear_speed=1.5 is outside [0.0, 1.0]
$ ros2 param get /patrol linear_speed
Double value is: 0.8
$ ros2 topic echo /turtle1/cmd_vel --once
linear: {x: 0.8, y: 0.0, z: 0.0}   angular: {x: 0.0, y: 0.0, z: 0.3}
$ ros2 topic echo /turtle1/pose --once
linear_velocity: 0.800000011920929   angular_velocity: 0.30000001192092896
$ ros2 param set /patrol publish_hz 10.0
Set parameter successful
$ timeout -s INT 6s ros2 topic hz /turtle1/cmd_vel
average rate: 9.997   window: 49
--- лог patrol:
[INFO] [patrol]: publish_hz 10.0 -> 5.0, timer period 0.200 s
[INFO] [patrol]: publish_hz 5.0 -> 10.0, timer period 0.100 s
```

## 5. Тесты (`tests.txt`)

`python3 -m pytest src/patrol/test -v` на `main`: **32 passed, 1 skipped** (пропущен
copyright, его отключил генератор пакета). `colcon test` для `turtle_bringup` и `patrol`:
`38 tests, 0 errors, 0 failures, 2 skipped`.

- `test_validate_values.py` — чистая функция. Значения по умолчанию и обычное изменение
  10 → 5 Гц принимаются. Для `publish_hz` отклоняются 0, −1, NaN, inf, 0.5 и 30.5,
  границы 1 и 30 допустимы. Для скорости и поворота отклоняются значения вне диапазона,
  NaN и inf, а также не числа.
- `test_parameters.py` — нода `Patrol` без симулятора. Смена 10 → 5 создаёт новый
  таймер с периодом 0,2 с, и у ноды остаётся ровно один таймер. Запросы 0, −1 и NaN
  отклоняются с причиной `publish_hz…`: значение 5.0 и объект таймера прежние
  (`node.timer is old_timer`). Смена скорости таймер не пересоздаёт. Набор
  `linear_speed=0.8, publish_hz=0.0` отклоняется целиком: скорость тоже не меняется.
- `test_choose_command.py` — команда использует переданные `linear_speed` и `turn_rate`.

## 6. Готовый сервис и действие (`services-actions.txt`)

```text
$ ros2 service type /clear
std_srvs/srv/Empty
$ ros2 topic echo /turtle1/pose --once
x: 8.212376594543457  y: 8.022640228271484  theta: 1.4976881742477417
$ ros2 service call /clear std_srvs/srv/Empty '{}'
requester: making request: std_srvs.srv.Empty_Request()
response:
std_srvs.srv.Empty_Response()
$ ros2 topic echo /turtle1/pose --once
x: 8.212376594543457  y: 8.022640228271484  theta: 1.4976881742477417   # поза та же
$ ros2 action list -t
/turtle1/rotate_absolute [turtlesim_msgs/action/RotateAbsolute]
$ ros2 action info /turtle1/rotate_absolute
Action servers: 1
    /turtlesim
$ ros2 action send_goal /turtle1/rotate_absolute turtlesim_msgs/action/RotateAbsolute '{theta: -1.57}' --feedback
Goal accepted with ID: …
Feedback:
    remaining: -3.131688117980957
    …                       # всего 196 feedback, |remaining| уменьшается к 0
    remaining: -0.1236882209777832
Result:
    delta: 3.119999885559082
Goal finished with status: SUCCEEDED
$ ros2 topic echo /turtle1/pose --once --field theta
-1.5583118200302124
```

След стёрт, поза сохранилась. Первая цель `theta: 1.57` (черепаха уже смотрела почти туда)
завершилась за 5 feedback с `SUCCEEDED`.

**Запрос и цель.** Запрос сервиса (`/clear`) — это один вызов: сервер его выполняет и
возвращает один ответ, промежуточного состояния клиент не видит. Цель action
(`rotate_absolute`) живёт дольше запроса: сервер сначала принимает её или отказывает,
затем во время выполнения шлёт feedback, в конце возвращает result со статусом
(`SUCCEEDED`, `CANCELED`, `ABORTED`), и в процессе клиент может запросить отмену.
