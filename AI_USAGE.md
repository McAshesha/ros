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

