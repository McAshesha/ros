# Декларация использования ИИ

## PR01

- Использован ИИ: да (`ai_used: true` в отчёте этой ПР).
- Модель и версия: Claude Opus 5.5 (Anthropic).
- Среда или интерфейс агента: Claude Code (CLI-агент в терминале macOS), команды ROS
  выполнялись в Docker-контейнере `tiryoh/ros2-desktop-vnc:lyrical-20260906T0836`.
- Затронутые компоненты: `README.md`, `.gitignore`, `.github/workflows/ci.yml`,
  `evidence/pr01/*` (`graph.md`, `environment.json`, `report.json`, сырые логи команд).
- Характер помощи: агент прочитал условие ПР01, скачал и проверил course kit, запустил
  turtlesim и teleop, выполнил CLI-наблюдения графа, замер частоты, опыт с разрывом по
  `ROS_DOMAIN_ID` 16/17 и восстановлением, сохранил реальный вывод команд, составил
  `graph.md`, `environment.json`, отчёт, README и CI workflow.
- Как результат был проверен независимо: все файлы evidence содержат вывод реально
  выполненных команд; `python3 -m json.tool` и `check_practice.py PR01` выполнены локально;
  CI на GitHub повторяет проверку JSON и контракта evidence. Опыт с разрывом домена и
  управление стрелками повторяются вручную в терминалах рабочего стола; причину сбоя
  объясняю сам (см. `evidence/pr01/graph.md`, раздел «Причина»).

## PR02

- Использован ИИ: да (`ai_used: true` в отчёте этой ПР).
- Модель и версия: Claude Opus 5.5 (Anthropic).
- Среда или интерфейс агента: Claude Code (CLI-агент в терминале macOS), команды ROS
  выполнялись в Docker-контейнере `tiryoh/ros2-desktop-vnc:lyrical-20260906T0836`.
- Затронутые компоненты: пакет `src/turtle_bringup` (сгенерирован `ros2 pkg create`,
  изменены метаданные и `data_files` в `setup.py`, добавлен `launch/sim.launch.py` по
  условию), `README.md`, `.gitignore`, `.github/workflows/ci.yml`, `evidence/pr02/*`.
- Характер помощи: агент создал и собрал пакет, установил launch-файл, проверил запуск и
  остановку launch, провёл опыт с публикацией в `/cmd_vel` и исправлением на
  `/turtle1/cmd_vel`, сохранил реальный вывод команд, написал `commands.md`, `types.md`,
  отчёт и шаг CI.
- Как результат был проверен независимо: `colcon build` и `py_compile` выполнены локально,
  установленный `sim.launch.py` проверен через `ros2 pkg prefix`; доставка подтверждена
  изменением `/turtle1/pose` и числом конечных точек в `ros2 topic info --verbose`;
  `check_practice.py PR02` выполнен локально, CI повторяет сборку и проверку контракта.
  Опыт повторяю вручную на рабочем столе и объясняю различие обнаружения и доставки сам
  (`evidence/pr02/commands.md`, раздел «Почему правильного типа недостаточно»).

## PR03

- Использован ИИ: да (`ai_used: true` в отчёте этой ПР).
- Модель и версия: Claude Opus 5.5 (Anthropic).
- Среда или интерфейс агента: Claude Code (CLI-агент в терминале macOS), команды ROS
  выполнялись в Docker-контейнере `tiryoh/ros2-desktop-vnc:lyrical-20260906T0836`.
- Затронутые компоненты: пакет `src/patrol` (сгенерирован `ros2 pkg create`; написаны
  `patrol/patrol.py` и `test/test_choose_command.py`, изменены метаданные, зависимость
  `turtlesim_msgs`, путь проверки в `test/test_mypy.py`), `README.md`,
  `.github/workflows/ci.yml`, `evidence/pr03/*`.
- Характер помощи: агент написал ноду по каркасу лекции 03 (подписка, таймер 0.1 с,
  издатель в относительный `cmd_vel`, чистая функция `choose_command`) и её unit-тесты,
  провёл опыт без remap и с `-r cmd_vel:=/turtle1/cmd_vel`, замер частоту команды и
  остановку, сохранил реальный вывод команд, написал `demo.md`, отчёт и шаг CI.
- Как результат был проверен независимо: `python3 -m pytest src/patrol/test` и
  `colcon test` выполнены локально (вывод в `evidence/pr03/tests.txt`); связь проверена
  через `ros2 node info`, `ros2 topic info --verbose`, изменение позы и `ros2 topic hz`;
  CI повторяет сборку, тесты и `check_practice.py PR03`. Опыт повторён вручную, роли
  `init`/`spin`/callback и причину сбоя объясняю сам (`evidence/pr03/demo.md`).
