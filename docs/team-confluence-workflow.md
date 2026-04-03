# Работа с Confluence через GigaCode

Это основная инструкция для команды.

Задачи, которые поддерживаются:

- проверить одну или несколько существующих страниц
- изменить одну или несколько существующих страниц
- создать одну или несколько новых страниц
- одновременно изменить существующие страницы и создать новые

## Установка

Сделай это на рабочей машине после `git pull`.

### 1. Перейди в репозиторий

```bash
cd /path/to/confluence-section-mcp
```

### 2. Запусти настройку

```bash
bash tools/setup_other_machine_after_pull.sh
```

### 3. Открой конфиг Confluence

Файл:

- `~/.gigacode/confluence-orchestrator/confluence-rest.config.json`

### 4. Заполни конфиг

Для рабочей машины команды используй рабочий URL Confluence и рабочий токен.

Минимально нужно заполнить:

```json
{
  "mode": "rest",
  "rest": {
    "base_url": "https://YOUR-CONFLUENCE",
    "api_flavor": "server",
    "body_format": "storage",
    "bearer_token": "PASTE_YOUR_TOKEN_HERE",
    "ssl_verify": false,
    "default_space_id": ""
  }
}
```

Что куда вставлять:

- в `base_url` вставь адрес своего Confluence
- в `bearer_token` вставь рабочий токен

### 5. Проверь, что всё готово

```bash
python3 -m unittest discover -s tests -v
```

## Использование

Ниже основной рабочий порядок. Делай именно так.

### 1. Создай job

```bash
cd /path/to/confluence-section-mcp
bash tools/cjob.sh
```

Скрипт сам спросит:

- `Job id`
- `Mode`
- текст задачи
- ссылки или id страниц
- родительскую страницу для новых страниц

### 2. Что вводить в поля

`Mode`:

- для обычной рабочей задачи ставь `mixed`
- для чистой проверки без правок ставь `analyze`

В поле задачи пиши прямо, что надо сделать.

Пример:

```text
Проверь страницы FE и BE на консистентность требований. Исправь найденные расхождения. Создай отдельную страницу с checklist для rollout. Ничего не публикуй автоматически.
```

В поля страниц вставляй:

- либо `pageId`
- либо полную ссылку на страницу Confluence

### 3. Открой готовый prompt

После `cjob.sh` будет создан файл:

- `work/review-jobs/<job-id>/gigacode-prompt.md`

Открой его:

```bash
cat work/review-jobs/<job-id>/gigacode-prompt.md
```

### 4. Вставь этот prompt в GigaCode

Ничего руками не дописывай.

Нужно взять весь текст файла `gigacode-prompt.md` целиком и вставить его в GigaCode.

### 5. Дождись завершения GigaCode

GigaCode сам:

- прочитает job
- откроет нужные chunks
- внесёт правки
- создаст новые страницы, если это нужно
- запишет controller report

### 6. Заверши job

После завершения GigaCode выполни:

```bash
cd /path/to/confluence-section-mcp
bash tools/cfinish.sh --job-id <job-id>
```

## Что делает `finish`

Команда `cfinish.sh` сама:

- проверяет статус job
- проверяет, есть ли реальные изменения
- собирает merged outputs
- публикует изменения только когда это действительно нужно
- не публикует ничего, если job вернулся как `review-only`

Оператору не нужно вручную решать, публиковать или нет.

## Как понимать результат

### `review-only`

Это нормальный результат.

Это значит:

- модель проверила задачу
- правки не потребовались
- публикация не выполняется

### `approved`

Это значит:

- есть реальные изменения
- `finish` публикует их

### `needs-edits`

Это значит:

- нужен ещё один проход
- нужно посмотреть отчёт и снова запустить работу по этому job

## Где смотреть результат

Рабочая папка job:

- `work/review-jobs/<job-id>/`

Главные файлы:

- `work/review-jobs/<job-id>/gigacode-prompt.md`
- `work/review-jobs/<job-id>/job.json`
- `work/review-jobs/<job-id>/loop-status.json`
- `work/review-jobs/<job-id>/reports/iteration-001/controller-report.md`

Пакет с обновлёнными существующими страницами:

- `work/review-jobs/<job-id>/artifacts/updated-pages`

Пакет с новыми страницами:

- `work/review-jobs/<job-id>/artifacts/new-pages`

## Что делать при ошибке

Собери диагностику:

```bash
cd /path/to/confluence-section-mcp
bash tools/collect_review_job_debug.sh <job-id>
```

## Короткая памятка

1. `git pull`
2. `bash tools/setup_other_machine_after_pull.sh`
3. заполни `~/.gigacode/confluence-orchestrator/confluence-rest.config.json`
4. `bash tools/cjob.sh`
5. открой `work/review-jobs/<job-id>/gigacode-prompt.md`
6. вставь этот prompt в GigaCode
7. после завершения GigaCode запусти `bash tools/cfinish.sh --job-id <job-id>`
