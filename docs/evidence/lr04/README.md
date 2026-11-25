# Evidence — ЛР4 (непрерывная интеграция)

Дата: 26.11.2026. TeamCity Server 2026.2.2 (build 239308) в Docker на TEST
(`192.168.56.11:8111`), агент `test-agent` в контейнере
`jetbrains/teamcity-agent`, Docker 29.10.1.

## Скриншоты

| Файл | Что подтверждает |
|---|---|
| `01-project.png` | Проект StudentLedger, сборки #1 (feature) и #2 (dev) успешны |
| `02-dev-build.png` | Сборка #2 ветки dev: шаги Build image (1м07с) и Push image (41с) |
| `03-agents.png` | Агент `test-agent` подключён к серверу |

## Текстовые подтверждения

| Файл | Что подтверждает |
|---|---|
| `01-teamcity-server.json` | Версия TeamCity Server |
| `02-build2.json` | Сборка #2: `status=SUCCESS`, ветка `dev` |
| `03-build1-log.txt` | Feature-сборка: образ собран, push пропущен с сообщением |
| `04-build2-log.txt` | Dev-сборка: `docker login`, push тегов `2` и `dev`, выход из registry |
| `05-agent.json` | Агент `test-agent` зарегистрирован |
| `06-dockerhub-tags.json` | В Docker Hub есть теги `dev` и `2` (digest, дата) |

## Что проверено

- VCS-корень на публичный GitHub, branch spec `+:refs/heads/*`;
- VCS-триггер на все ветки;
- feature-ветка `feature/lr4-teamcity-ci`: сборка #1 успешна, публикация
  пропущена (ветка не dev/prod);
- ветка `dev`: сборка #2 успешна, образ `ahdyshba/studentledger:2` и
  `:dev` опубликован в Docker Hub;
- параметр `DOCKERHUB_TOKEN` имеет тип password и маскируется в UI/логах.

## Ограничения

- Сборка `prod` не запускалась: ветка `prod` ещё не содержит Dockerfile,
  пока не выполнен выпуск dev → prod. После слияния выпуска нужно запустить
  сборку `prod` и проверить тег `prod` в Docker Hub.
- TeamCity использует внутреннюю HSQLDB (учебный стенд); для production
  нужен PostgreSQL.
- Агент запущен с `--user root` из-за доступа к сокету Docker; это
  ограничение стенда, не production-схема.
- Отчёт ЛР4 ещё не создан.
