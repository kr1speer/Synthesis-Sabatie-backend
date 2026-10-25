# Synthesis-Sabatie-backend

Общий контекст курса: @~/.claude/sabatier-course.md

Это бэкенд-репозиторий. Фронтенд живёт в отдельном репозитории,
но методички и документация курса лежат здесь, в `methods/`.

## Структура

- `main.py` — приложение FastAPI, описание Swagger, подключение роутеров
- `api/` — `chemist_user_handlers.py`, `sabatier_material_handlers.py`,
  `chemist_user_auth.py` (сессии), `sabatier_schemas.py` (Pydantic)
- `data/` — `sabatier_models.py` (SQLAlchemy), `sabatier_database.py`,
  `sabatier_redis.py` (сессии), `sabatier_minio.py` (изображения и видео)
- `sql/` — схема и наполнение
- `methods/` — методички, ГОСТ, образец РПЗ, диаграммы, скрипты сборки документации
- `sabatier_api.postman_collection.json` — коллекция Postman

## Документация и диаграммы

- `methods/edit.drawio` — страница 1 диаграмма классов, страница 2 диаграмма последовательности
- `methods/build_docs.py` — сборка РПЗ в .docx
- `methods/build_sequence.py` — генерация диаграммы последовательности

Экспорт диаграмм в PNG и вставка в РПЗ — шириной 17 см, по центру, «в тексте».
Вертикальные диаграммы ограничены высотой 23 см.
