# Расчёт выхода метана по реакции Сабатье

Заявочная система по теме 2 «Синтез метана по реакции Сабатье». Услуги — исходные
вещества для реакции (H₂, CO₂, вода, биогаз, катализатор). Пользователь указывает их
массы в граммах, а система вычисляет массу получаемого метана (CH₄).

Курс «Разработка Интернет Приложений», МГТУ им. Н. Э. Баумана, ИУ5, осень 2026.

## Предметная область

| Сущность | Что это | Таблица |
|---|---|---|
| Материал реакции | Исходное вещество для синтеза (услуга) | `sabatier_materials` |
| Лайк материала | Связь м-м «инженер-технолог ↔ материал» | `material_likes` |
| Инженер-технолог | Пользователь системы, он же модератор | `chemist_users` |
| Заявка на синтез | Расчёт массы метана по количествам материалов (следующие ЛР) | `synthesis_request` |
| Позиция заявки | Связь «заявка ↔ материал» с указанным количеством (следующие ЛР) | `synthesis_request_item` |

Поля предметной области у материала (оба числовые и необязательные): `min_reaction_value` —
минимальная масса вещества в граммах для типовой реакции (получение 1 кг CH₄), фильтруемое поле;
`molar_mass` — молярная масса вещества в г/моль, используется в формуле расчёта. Оба поля
и краткое описание заполняются при публикации, поэтому у черновика они пустые.

## Веб-сервис (ЛР3)

FastAPI, взаимодействие с БД только через ORM SQLAlchemy, файлы в S3-совместимом MinIO.
Шаблонов нет: сервис отдаёт JSON и тестируется в Postman.

Авторизации ещё нет — пользователь-создатель зафиксирован константой и раздаётся
функцией-singleton `get_current_chemist_id()` из `data/sabatier_current_chemist.py`.

### Домен «Материал реакции» — `/api/sabatier_materials`

| Метод | URL | Тело запроса | Ответ |
|---|---|---|---|
| GET | `/api/sabatier_materials?min_reaction_value=N` | — | `200` список опубликованных |
| GET | `/api/sabatier_materials/feed` | — | `200` одна строка — первый материал ленты |
| GET | `/api/sabatier_materials/draft` | — | `200` черновик пользователя, `404` если его нет |
| POST | `/api/sabatier_materials` | `material_name`, `material_image`, `material_video` | `201` созданный черновик, `409` если черновик уже есть |
| PUT | `/api/sabatier_materials/{id}/publish` | `material_description`, `min_reaction_value`, `molar_mass` | `200` опубликованный материал, `404` если это не свой черновик |
| DELETE | `/api/sabatier_materials/{id}` | — | `204`, статус меняется на «удалён» |
| POST | `/api/sabatier_materials/{id}/like` | `liked` 0 или 1 | `200` материал с новыми `liked_count` и `is_liked` |

### Домен «Инженер-технолог» — `/api/chemist_users`

| Метод | URL | Тело запроса | Ответ |
|---|---|---|---|
| POST | `/api/chemist_users/register` | `chemist_login`, `chemist_password`, `full_name` | `201` созданный пользователь, `409` если логин занят |
| POST | `/api/chemist_users/login` | `chemist_login`, `chemist_password` | `204`, заглушка до ЛР4 |
| POST | `/api/chemist_users/logout` | — | `204`, заглушка до ЛР4 |

### Правила веб-сервиса

- Записи в статусе «удалён» наружу не передаются ни одним методом.
- Системные поля (ид, статус, создатель, даты создания и формирования) с клиента
  не принимаются — их выставляет бизнес-логика.
- Статусы меняются только вперёд: `черновик → опубликован` (PUT) и
  `черновик/опубликован → удалён` (DELETE). Вернуть материал в черновик нельзя.
- У одного пользователя не больше одного черновика.
- Набор полей в json материала всегда один и тот же, незаполненные приходят как `null`.
  Статуса в ответе нет — он нужен только в БД.
- Фильтрация выполняется на бэкенде, в SQL-запросе.
- Количество лайков и признак «лайкнул ли текущий пользователь» считает СУБД
  подзапросами в том же `SELECT`, что и сам материал.

Тело материала в ответе: `id`, `material_name`, `material_description`,
`material_image_name`, `material_video_name`, `min_reaction_value`, `molar_mass`,
`liked_count`, `is_mine` (1, если создатель — текущий пользователь),
`is_liked` (1, если текущий пользователь уже поставил лайк).

### Файлы материалов

Файлы в POST необязательные. Если их не прислали, у черновика остаются медиа
по умолчанию `default_material.png` и `default_material.mp4`
(константы `DEFAULT_MATERIAL_IMAGE_NAME` и `DEFAULT_MATERIAL_VIDEO_NAME`) — их отдаёт
SSR-сервер из `static/img`, в MinIO они не лежат. Заменить медиа у своего материала
можно методами `PUT /{id}/image` и `PUT /{id}/video`: новый файл уходит в бакет,
прежний объект из бакета удаляется, а в БД обновляется имя. Файл по умолчанию
при замене не удаляется — он принадлежит SSR-серверу.

Бакет создаётся при старте сервиса (`ensure_material_bucket()` в `main.py`), и там же
на **каждом** запуске выставляется его политика: читать объекты может кто угодно,
а писать и удалять — только сервис по своим ключам. Политика переустанавливается
каждый раз потому, что бакет, открытый руками через консоль MinIO, остаётся доступным
на запись анонимно. Код — `data/sabatier_minio.py`.

## База данных

PostgreSQL 18, модели — `data/sabatier_models.py`, подключение — `data/sabatier_database.py`.
Таблицы создаются SQL-скриптом `sql/01_create_schema.sql`.
Каскадное удаление запрещено: все внешние ключи `ON DELETE RESTRICT`.

| Таблица | Столбцы |
|---|---|
| `chemist_users` | `id` PK, `chemist_login` varchar(64) unique, `chemist_password` varchar(128), `full_name` varchar(128), `is_moderator` boolean |
| `sabatier_materials` | `id` PK, `material_name` varchar(128), `material_description` varchar(1024) NULL, `material_status` varchar(16) (`draft` / `published` / `deleted`), `material_image_name` varchar(128) NOT NULL, `material_video_name` varchar(128) NOT NULL, `min_reaction_value` integer NULL, `molar_mass` numeric(8,3) NULL, `created_at` timestamptz, `creator_chemist_id` FK → `chemist_users`, `formed_at` timestamptz NULL |
| `material_likes` | `id` PK, `chemist_id` FK → `chemist_users`, `material_id` FK → `sabatier_materials`, unique (`chemist_id`, `material_id`) |

У каждого инженера-технолога не более одного черновика — частичный уникальный индекс
`uq_sabatier_materials_one_draft`. Количество лайков считает СУБД скалярным подзапросом
(`liked_count`, `column_property`), строки таблицы лайков в приложение не вычитываются.


## Запуск

```bash
docker compose up -d                  # MinIO :9000, Postgres :5434, Adminer :8082
source synthesis-sabatie/bin/activate
pip install -r requirements.txt
python main.py                        # http://127.0.0.1:8000
```

Adminer — http://localhost:8082: движок **PostgreSQL**, сервер `postgres`, пользователь `postgres`,
пароль `labs`, база данных `sabatier`. Таблицы создаются в Adminer: вкладка «SQL-запрос» →
выполнить `sql/01_create_schema.sql`, затем `sql/02_seed_data.sql`.

Консоль MinIO — http://localhost:9001, пользователь `root`, пароль `rootpassword`,
публичный бакет `sabatie-assets`.

## Формула

Выход массы метана рассчитывается по законам химической стехиометрии реакции гидрирования
диоксида углерода (реакция Сабатье):

$$\text{CO}_2 + 4\text{H}_2 \xrightarrow{\text{Катализатор, } \Delta T} \text{CH}_4 + 2\text{H}_2\text{O}$$

1. Расчёт количества моль исходных реагентов:

$$n(\text{H}_2) = \frac{m(\text{H}_2)}{M(\text{H}_2)}, \quad n(\text{CO}_2) = \frac{m(\text{CO}_2)}{M(\text{CO}_2)}$$

2. Определение лимитирующего реагента и теоретического количества моль метана:

$$n_{\text{max}}(\text{CH}_4) = \min\left(\frac{n(\text{H}_2)}{4}, n(\text{CO}_2)\right)$$

3. Итоговый расчёт массы метана с учётом КПД установки ($\eta$):

$$m(\text{CH}_4) = n_{\text{max}}(\text{CH}_4) \times M(\text{CH}_4) \times \eta$$

В основу расчёта положены законы стехиометрии химических реакций и закон сохранения массы. Константы молярных масс: $M(\text{H}_2) = 2.016 \text{ г/моль}$, $M(\text{CO}_2) = 44.01 \text{ г/моль}$, $M(\text{CH}_4) = 16.04 \text{ г/моль}$. Параметр $\eta$
(технологический КПД реактора) определяется типом катализатора и температурным режимом установки.
