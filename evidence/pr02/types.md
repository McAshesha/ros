# ПР02. Топики и типы сообщений

Значения получены командами `ros2 topic type` и `ros2 interface show` в ROS 2 Lyrical
(`cmd-once.txt`).

| Топик | Тип | Направление | Назначение |
|---|---|---|---|
| `/turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | издатель (teleop, `ros2 topic pub`) → подписчик `/turtlesim` | команда скорости черепахи |
| `/turtle1/pose` | `turtlesim_msgs/msg/Pose` | издатель `/turtlesim` → подписчики | текущее положение черепахи (~62,5 Гц, см. ПР01) |

В Lyrical тип позы — `turtlesim_msgs/msg/Pose`. В Jazzy было бы `turtlesim/msg/Pose`.

## `geometry_msgs/msg/Twist`

```text
$ ros2 interface show geometry_msgs/msg/Twist
# This expresses velocity in free space broken into its linear and angular parts.
Vector3  linear
	float64 x
	float64 y
	float64 z
Vector3  angular
	float64 x
	float64 y
	float64 z
```

| Поле | Единицы | Смысл для turtlesim |
|---|---|---|
| `linear.x` | м/с | скорость вперёд вдоль направления черепахи (отрицательная — назад) |
| `linear.y` | м/с | боковая скорость; turtlesim тоже её применяет, но teleop её не шлёт |
| `linear.z` | м/с | вверх; на плоскости игнорируется |
| `angular.x`, `angular.y` | рад/с | крен и тангаж; на плоскости игнорируются |
| `angular.z` | рад/с | поворот вокруг вертикали, `> 0` — против часовой стрелки (влево) |

Скорости в Twist заданы в системе координат самого робота. Turtlesim применяет
последнюю команду около 1 с, затем останавливается. Для непрерывного движения команды
нужно слать постоянно (`--rate`).

## `turtlesim_msgs/msg/Pose`

| Поле | Смысл |
|---|---|
| `x`, `y` | положение в мире turtlesim (м), окно ~11 × 11, появление в (5.54, 5.54) |
| `theta` | курс (рад) в диапазоне (−π, π], 0 — вдоль оси x |
| `linear_velocity` | текущая линейная скорость (м/с) |
| `angular_velocity` | текущая угловая скорость (рад/с) |
