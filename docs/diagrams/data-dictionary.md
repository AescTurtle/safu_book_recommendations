# Словарь данных

Описание всех таблиц и столбцов системы **«Книги по настроению»**. Соответствует моделям
SQLAlchemy в [models.py](../../models.py). Диаграмма связей — в [erd.md](erd.md).

Обозначения: **PK** — первичный ключ, **FK** — внешний ключ, **U** — уникальное значение,
**NN** — NOT NULL (обязательное).

---

## `users` — пользователи

| Столбец | Тип | NULL | Ключ / ограничение | По умолчанию | Описание |
|---|---|---|---|---|---|
| `id` | INTEGER | нет | PK | автоинкремент | Идентификатор пользователя |
| `username` | VARCHAR(64) | нет | U, NN | — | Логин (уникальный) |
| `password_hash` | VARCHAR(255) | нет | NN | — | Хеш пароля (Werkzeug, `generate_password_hash`) |
| `role` | VARCHAR(16) | нет | NN | `"user"` | Роль: `user` или `admin` |
| `created_at` | DATETIME | нет | NN | `utcnow()` | Дата и время регистрации (UTC) |

Связи: `users 1-* recommendations`, `users 1-* ratings` (каскадное удаление).
Свойство `is_admin` (вычисляемое) — `True`, если `role == "admin"`.

---

## `moods` — настроения

| Столбец | Тип | NULL | Ключ / ограничение | По умолчанию | Описание |
|---|---|---|---|---|---|
| `id` | INTEGER | нет | PK | автоинкремент | Идентификатор настроения |
| `code` | VARCHAR(32) | нет | U, NN | — | Машинный код (`sad`, `happy`, …) |
| `name_ru` | VARCHAR(64) | нет | NN | — | Название на русском |
| `emoji` | VARCHAR(8) | нет | NN | `""` | Эмодзи для отображения |
| `description` | VARCHAR(255) | нет | NN | `""` | Краткое описание настроения |

Связи: `moods *-* books` (через `book_moods`), `moods 1-* recommendations`.

---

## `books` — книги

| Столбец | Тип | NULL | Ключ / ограничение | По умолчанию | Описание |
|---|---|---|---|---|---|
| `id` | INTEGER | нет | PK | автоинкремент | Идентификатор книги |
| `title` | VARCHAR(255) | нет | NN | — | Название |
| `author` | VARCHAR(255) | нет | NN | — | Автор |
| `year` | INTEGER | да | — | — | Год издания (необязательно) |
| `description` | TEXT | нет | NN | `""` | Аннотация |
| `language` | VARCHAR(8) | нет | NN | `"ru"` | Язык книги |
| `cover_url` | VARCHAR(500) | да | — | — | URL обложки (необязательно) |

Связи: `books *-* moods` (через `book_moods`), `books 1-* ratings` (каскадное удаление).

---

## `book_moods` — связь «книга ↔ настроение» (M:N)

| Столбец | Тип | NULL | Ключ / ограничение | По умолчанию | Описание |
|---|---|---|---|---|---|
| `book_id` | INTEGER | нет | PK, FK → `books.id` | — | Книга (`ON DELETE CASCADE`) |
| `mood_id` | INTEGER | нет | PK, FK → `moods.id` | — | Настроение (`ON DELETE CASCADE`) |

Составной первичный ключ `(book_id, mood_id)` — реализует связь «многие-ко-многим».

---

## `recommendations` — история рекомендаций

| Столбец | Тип | NULL | Ключ / ограничение | По умолчанию | Описание |
|---|---|---|---|---|---|
| `id` | INTEGER | нет | PK | автоинкремент | Идентификатор записи |
| `user_id` | INTEGER | нет | FK → `users.id`, NN | — | Кто запросил (`ON DELETE CASCADE`) |
| `mood_id` | INTEGER | нет | FK → `moods.id`, NN | — | Выбранное настроение (`ON DELETE CASCADE`) |
| `created_at` | DATETIME | нет | NN | `utcnow()` | Когда выдана рекомендация (UTC) |

Индекс: `ix_recommendations_user_id` по `user_id`.
Запись создаётся при каждом подборе книг по настроению (`/recommend`).

---

## `ratings` — оценки книг

| Столбец | Тип | NULL | Ключ / ограничение | По умолчанию | Описание |
|---|---|---|---|---|---|
| `id` | INTEGER | нет | PK | автоинкремент | Идентификатор оценки |
| `user_id` | INTEGER | нет | FK → `users.id`, NN | — | Автор оценки (`ON DELETE CASCADE`) |
| `book_id` | INTEGER | нет | FK → `books.id`, NN | — | Оцениваемая книга (`ON DELETE CASCADE`) |
| `rating` | INTEGER | нет | NN | — | Оценка от 1 до 5 (проверяется в приложении) |
| `comment` | TEXT | нет | NN | `""` | Текстовый отзыв (необязательно заполнять) |
| `created_at` | DATETIME | нет | NN | `utcnow()` | Когда поставлена оценка (UTC) |

Ограничения:
- `uq_user_book_rating` — **UNIQUE** `(user_id, book_id)`: один пользователь — одна оценка
  на книгу. Повторная отправка обновляет существующую запись.
- Индекс `ix_ratings_book_id` по `book_id`.
