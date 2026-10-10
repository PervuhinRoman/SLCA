# Проверка веток — 2026-10-10

- Исходный origin/master: 816ac3eca4fcf73d2de12a65b907916a97fcaeee.
- git ls-remote до изменений: только master; GitHub PR list: пусто.
- dev и prod созданы на этом SHA, push обеих веток успешен, upstream настроен.
- docs/lr1-branch-workflow создана от dev; изменения только документационные.
- GitHub GET repository: permissions.admin=true, default_branch=master.
- PATCH default branch и PUT protections dev/prod: HTTP 403,
  Resource not accessible by personal access token. Настройки не изменены.
- CI отсутствует по уточнению пользователя. Нет успешного CI/deploy,
  никакой вымышленный status check не создавался.
- Коммит de7be1a (docs: align LR1 branch strategy with lab workflow) создан
  в docs/lr1-branch-workflow; push успешен, upstream настроен.
- gh pr create с base=dev и head=docs/lr1-branch-workflow отклонён:
  GraphQL: Resource not accessible by personal access token (createPullRequest).
  PR не создан, review и CI-статусы PR отсутствуют.
- Ручное создание PR: https://github.com/PervuhinRoman/SLCA/compare/dev...docs/lr1-branch-workflow?expand=1
- APP-01–03 не выполняются. Приложение остаётся прототипом /health.

## Повторная попытка после обновления прав токена

- По указанию пользователя повторён gh pr create: успешно создан PR #1.
- URL: https://github.com/PervuhinRoman/SLCA/pull/1
- Проверено через gh pr view: OPEN, base=dev, head=docs/lr1-branch-workflow,
  head SHA de7be1a500b8fe767c120e50391ae38015bd280d, statusCheckRollup=[],
  reviewDecision пуст. Слияние не выполнялось.
- Настройки default branch/защит повторно не изменялись.


## Защита после разрешения Administration: write — 2026-10-10

Повторные PATCH default branch и PUT protection завершились успешно.
Независимые GET подтвердили default_branch=dev, для dev/prod:
required_pull_request_reviews.required_approving_review_count=0,
dismiss_stale_reviews=true, require_last_push_approval=false,
require_code_owner_reviews=false, required_status_checks=null,
enforce_admins.enabled=true, required_conversation_resolution.enabled=true,
allow_force_pushes.enabled=false, allow_deletions.enabled=false,
required_linear_history.enabled=false, lock_branch.enabled=false.
Для master: lock_branch.enabled=true, enforce_admins.enabled=true,
allow_force_pushes.enabled=false, allow_deletions.enabled=false.

PR #1 уже MERGED: mergedBy=PervuhinRoman, mergedAt=2026-10-10T13:18:23Z,
mergeCommit=21ca865a1649b8d0b335dd9209cc25585ba2958b. Reviews=[], checks=[].
Агент merge не выполнял. Remote dev на 21ca865, prod/master на 816ac3e.
Ветки dev/prod/master имеют protected=true; временная docs-ветка — false.
Проверка фактического отклонения push/merge не выполнялась; API подтверждает
конфигурацию, не результат отрицательного теста. Скриншоты не создавались.
