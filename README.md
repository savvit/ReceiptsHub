# Розгортання проекту
## Для розгортання проекту спочатку клонуйте репозиторій за допомогою Git:

- git clone https://github.com/savvit/ReceiptsHub.git

## Далі у кореневій директорії проекту (на одному рівні з файлом docker-compose.yml) створіть файл .env і додайте в нього наступні змінні:

`SECRET_KEY=<your_secret_key>`

`ALGORITHM=HS256`

`ACCESS_TOKEN_EXPIRE_MINUTES=<your_expiry_time>`

`POSTGRES_DB=db`

`POSTGRES_DB_NAME=db`

`POSTGRES_PORT=<your_db_port>`

`POSTGRES_USER=<your_db_user>`

`POSTGRES_PASSWORD=<your_db_password>`

Замість значень <your_secret_key>, <your_expiry_time>, <your_db_port>, <your_db_user>, та <your_db_password> вкажіть відповідні параметри для вашого проекту.

Для коректного запуску проекту на вашому сервері має бути встановлений Python 3.13 та Docker, а також активний Docker Daemon.
Після налаштування .env файлу, в кореневій директорії проекту виконайте команду для побудови та запуску контейнерів:

`docker-compose up --build`

Ця команда завантажить необхідні залежності, побудує Docker образи та запустить проект.
Перевірити працездатність API можна за посиланням http://0.0.0.0:8001/docs або використовуючи Postman.


# API для обробки чеків та аутентифікації

Це документація для FastAPI сервісу, що надає ендпоінти для реєстрації користувачів, їхньої аутентифікації, а також для роботи з чеками, включаючи створення, перегляд та генерацію чека у текстовому форматі.

## 1. Реєстрація користувача (POST /auth/register)

### Опис:
Цей ендпоінт дозволяє зареєструвати нового користувача в системі. Під час реєстрації перевіряється, чи існує вже користувач з таким ім'ям. Якщо ні — створюється новий запис у базі даних.

### Параметри запиту:
  - `full_name` (рядок): Повне ім'я користувача.
  - `username` (рядок): Логін користувача.
  - `password` (рядок): Пароль користувача.
### Приклад тіла запиту:
`{
  "full_name": "Vitalii Savchuk",
  "username": "vitaliisavchuk",
  "password": "Mypass1"
}`
### Відповідь:
- Після успішної реєстрації система повертає дані нового користувача, включаючи його ім'я та логін.
### Приклад відповіді:
`
{
  "full_name": "Vitalii Savchuk",
  "username": "vitaliisavchuk"
}
`
---

## 2. Вхід користувача (POST /auth/login)

### Опис:
Цей ендпоінт дозволяє користувачеві увійти в систему, використовуючи логін та пароль. Після успішної аутентифікації генерується токен доступу, який необхідний для роботи з іншими ендпоінтами.

### Параметри запиту:
  - `username` (рядок): Логін користувача.
  - `password` (рядок): Пароль користувача.
### Приклад тіла запиту:
`{
  "username": "vitaliisavchuk",
  "password": "Mypass1"
}`
### Відповідь:
- Після успішної аутентифікації система повертає токен доступу:
  - `access_token` (рядок): Токен для аутентифікації у майбутніх запитах.
  - `token_type` (рядок): Тип токена, зазвичай "bearer".
### Приклад відповіді:
`
{
  "access_token": "тут буде токен",
  "token_type": "bearer"
}
`
---

## 3. Створення чека (POST /checks/create)

### Опис:
Цей ендпоінт дозволяє створити новий чек, асоціюючи його з поточним користувачем. Під час створення чека враховуються деталі продуктів, а також тип і сума оплати.

### Приклад тіла запиту:
`{
  "products": [
    {
      "name": "Хліб",
      "price": 20,
      "quantity": 1
    }
  ],
  "payment": {
    "type": "cash",
    "amount": 50
  }
}`
### Відповідь:
- Інформація про створений чек, включаючи ID, суму, залишок, деталі оплати та список придбаних продуктів.
### Приклад відповіді:
`
{
  "id": 44,
  "user_id": 8,
  "created_at": "2024-11-22T01:46:42.159356",
  "total": 20,
  "payment": {
    "type": "cash",
    "amount": "50"
  },
  "rest": "30",
  "products": [
    {
      "name": "Хліб",
      "price": "20.0",
      "quantity": 1,
      "total": 20
    }
  ]
}
`
---

## 4. Перегляд списку чеків (GET /checks/list)

### Опис:
Цей ендпоінт дозволяє отримати список чеків поточного користувача з можливістю фільтрації за різними параметрами.

### Параметри запиту:
- **created_from (date)**: Дата початку фільтрації. Повертаються записи, де дата створення чека більша або рівна цій даті. Передається у форматі 2024-11-22.
- **created_to (date)**: Дата кінця фільтрації. Повертаються записи, де дата створення чека менша або рівна цій даті. Передається у форматі 2025-10-06.
- **min_total (int)**: Мінімальна сума чека для фільтрації. Повертаються записи, де загальна сума чека більше або рівне цій сумі.
- **max_total (int)**: Максимальна сума чека для фільтрації. Повертаються записи, де загальна сума чека менша або рівна цій сумі.
- **payment_type (str)**: Тип оплати для фільтрації. Може бути значенням 'cash' або 'card'.
- **skip (int)**: Кількість записів, які потрібно пропустити. За замовчуванням 0. Використовується для пагінації.
- **per_page (int)**: Максимальна кількість записів, що повинні бути повернуті. За замовчуванням 10. Використовується для пагінації.

### Приклад відповіді:
`
{
  "id": 49,
  "user_id": 8,
  "created_at": "2024-11-22",
  "total": 20,
  "payment": {
    "type": "cash",
    "amount": "100"
  },
  "rest": "80",
  "products": [
    {
      "name": "Хліб",
      "price": "20.0",
      "quantity": 1,
      "total": 20
    }
  ]
}
`
---

## 5. Перегляд чека за ID (GET /checks/{check_id})

### Опис:
Цей ендпоінт дозволяє отримати детальну інформацію про конкретний чек за його ID, включаючи продукти, суму, оплату та час створення.

### Параметри запиту:
- **check_id (int)**: ID чека, який необхідно отримати.

### Відповідь:
- Детальна інформація про чек, включаючи список продуктів, оплату та час створення.
### Приклад відповіді:
`
{
  "id": 49,
  "user_id": 8,
  "created_at": "2024-11-22",
  "total": 20,
  "payment": {
    "type": "cash",
    "amount": "100.0"
  },
  "rest": "80.0",
  "products": [
    {
      "name": "Хліб",
      "price": "20.0",
      "quantity": 1,
      "total": 20
    }
  ],
  "receipt_url": "http://localhost:8000/checks/49/text"
}
`
---

## 6. Генерація текстового чека (GET /checks/{check_id}/text)

### Опис:
Цей ендпоінт генерує текстову версію чека для зручного виведення або друку.

### Параметри запиту:
- **line_width (int)**: Загальна довжина рядка чека. По замовчуванню 40 символів.

### Відповідь:
- Текстова версія чека, яка містить всі необхідні деталі, відформатовані для виведення.

---
### Аутентифікація:
Для доступу до більшості ендпоінтів користувач має бути автентифікованим. Токен доступу видається після успішного входу користувача та зберігається в cookie.

---