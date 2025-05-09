# LesJours - Мастер-классы

Платформа для проведения и записи на мастер-классы.

## Требования

- Python 3.10+
- PostgreSQL
- Virtual environment

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd LesJours
```

2. Создайте и активируйте виртуальное окружение:
```bash
python -m venv .venv
source .venv/bin/activate  # для Linux/Mac
# или
.venv\Scripts\activate  # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл .env в корневой директории:
```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:password@localhost:5432/lesjours
```

5. Примените миграции:
```bash
python manage.py migrate
```

6. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

7. Запустите сервер разработки:
```bash
python manage.py runserver
```

## Структура проекта

- `users/` - Приложение для управления пользователями
- `masterclasses/` - Приложение для мастер-классов
- `orders/` - Приложение для управления заказами
- `certificates/` - Приложение для сертификатов

## Функциональность

- Регистрация и авторизация пользователей
- Просмотр и бронирование мастер-классов
- Управление избранными мастер-классами
- Корзина и оформление заказов
- Система сертификатов
- API для интеграции 