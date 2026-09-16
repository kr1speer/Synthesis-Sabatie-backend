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

Поля предметной области у материала (оба числовые): `min_reaction_value` — минимальная
масса вещества в граммах для типовой реакции (получение 1 кг CH₄), фильтруемое поле;
`molar_mass` — молярная масса вещества в г/моль, используется в формуле расчёта.

## База данных (ЛР2)

PostgreSQL 18, работа с БД через ORM SQLAlchemy, модели — `data/sabatier_models.py`,
подключение — `data/sabatier_database.py`. Таблицы создаются SQL-скриптом `sql/01_create_schema.sql`.
Каскадное удаление запрещено: все внешние ключи `ON DELETE RESTRICT`.

| Таблица | Столбцы |
|---|---|
| `chemist_users` | `id` PK, `chemist_login` varchar(64) unique, `full_name` varchar(128), `is_moderator` boolean |
| `sabatier_materials` | `id` PK, `material_name` varchar(128), `reaction_role` varchar(1024), `material_status` varchar(16) (`draft` / `published` / `deleted`), `material_image_url` varchar(512), `material_video_url` varchar(512), `min_reaction_value` integer, `molar_mass` numeric(8,3), `created_at` timestamptz, `creator_chemist_id` FK → `chemist_users`, `formed_at` timestamptz |
| `material_likes` | `id` PK, `chemist_id` FK → `chemist_users`, `material_id` FK → `sabatier_materials`, unique (`chemist_id`, `material_id`) |

У каждого инженера-технолога не более одного черновика — частичный уникальный индекс
`uq_sabatier_materials_one_draft`. SQL-скрипты лежат в `sql/`:

| Файл | Что делает |
|---|---|
| `01_create_schema.sql` | создаёт три таблицы |
| `02_seed_data.sql` | добавляет 10 инженеров-технологов |
| `03_show_order_queries.sql` | запросы в порядке показа ЛР2 |

Материалы и лайки вносятся вручную через Adminer.

Маршруты ЛР2 (авторизации нет, действия выполняются от имени инженера-технолога `id = 1`):

| Метод | URL | Реализация |
|---|---|---|
| GET | `/sabatier_materials/feed/{material_id}` (`?next=true` — следующий) | ORM |
| GET | `/sabatier_materials/draft` | ORM |
| GET | `/sabatier_materials?min_reaction_value=N` | ORM |
| POST | `/sabatier_materials/draft` — кнопка «Далее», создание черновика | ORM |
| POST | `/sabatier_materials/draft/publish` — кнопка «Опубликовать» | ORM |
| POST | `/sabatier_materials/{material_id}/delete` — логическое удаление | SQL `UPDATE` через курсор |

Если ссылки на фото и видео пустые или недоступны, показываются файлы по умолчанию
из `static/img/default_material.png` и `static/img/default_material.mp4`.

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

## Дизайн

Стилистика повторяет визуальную систему промышленного газового концерна **Air Liquide**
(`airliquide.com`, блок «Stories» на главной). Точные цвета из CSS-переменных проекта:

| Роль | Код | Название в CSS |
|---|---|---|
| Синие карточки, текст, рамка кнопок | `#00349B` | `--identity-primary` |
| Фоновый градиент страницы | `#F2F2FD` → `#B8CFF4` | `--background-gradient-light` / `--background-gradient-deep` |
| Рамка тегов | `#B3D5FB` | `--chip-border` |
| Фокус полей ввода | `#3172D9` | `--identity-accent` |

Карточки синие со скруглением 20 px и белым текстом (как карточка «First Half 2026 Results»).
При наведении карточка смещается на 4 px вверх, а тень усиливается. Кнопки полукруглые
и прозрачные с синей рамкой (как «All stories»), при наведении заливаются белым.
