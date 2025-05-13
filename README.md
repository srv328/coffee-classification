# Coffee Classification Project

Проект по классификации кофе с использованием машинного обучения и веб-технологий.

## Архитектура проекта

Проект состоит из двух основных частей:
- Backend (Python/Flask)
- Frontend (React)

## Использованные технологии

### Backend
- **Flask 2.0.1** - веб-фреймворк для создания API
- **Flask-CORS 3.0.10** - для обработки CORS-запросов
- **MySQL Connector Python 8.0.26** - для работы с базой данных MySQL
- **Python-dotenv 0.19.0** - для работы с переменными окружения
- **NumPy 1.19.5** - для работы с многомерными массивами и математических вычислений
- **Pandas 1.3.3** - для обработки и анализа данных
- **Scikit-learn 0.24.2** - для машинного обучения
- **TensorFlow 2.6.0** - для создания и использования нейронных сетей
- **Werkzeug 2.0.3** - утилиты для WSGI-приложений
- **Protobuf 3.20.0** - для сериализации данных

### Frontend
- **React 18.2.0** - JavaScript библиотека для создания пользовательских интерфейсов
- **React Router DOM 6.3.0** - для маршрутизации в React-приложении
- **Axios 0.27.2** - для выполнения HTTP-запросов
- **Bootstrap 5.2.0** - для стилизации и создания адаптивного дизайна
- **React Icons 5.5.0** - для использования иконок
- **SweetAlert2 11.19.1** - для создания красивых уведомлений
- **React Scripts 5.0.1** - скрипты и конфигурация для Create React App

### База данных
- **MySQL** - реляционная база данных для хранения информации о кофе и его характеристиках

## Структура проекта

```
coffee-classification/
├── backend/
│   ├── app.py              # Основной файл Flask-приложения
│   ├── ml_model.py         # Модель машинного обучения
│   ├── config.py           # Конфигурация приложения
│   ├── db.py              # Конфигурация базы данных
│   ├── requirements.txt    # Зависимости Python
│   ├── init.sql           # Инициализация базы данных
│   ├── models/            # Модели машинного обучения
│   └── routes/            # Маршруты API
└── frontend/
    ├── public/            # Статические файлы
    ├── src/              # Исходный код React-приложения
    │   ├── components/   # React компоненты
    │   ├── utils/        # Вспомогательные функции
    │   ├── App.js        # Основной компонент приложения
    │   └── index.js      # Точка входа
    ├── package.json      # Зависимости Node.js
    └── .gitignore       # Игнорируемые файлы Git
```

## Требования

- Python 3.9.13
- MySQL Server
- Node.js 14+
- npm 6+

## Установка и запуск

### База данных

1. Установите MySQL Server
2. Создайте базу данных:
```sql
mysql -u root -p
CREATE DATABASE coffee_classification;
exit;
```

3. Импортируйте схему базы данных:
```bash
mysql -u root -p coffee_classification < backend/init.sql
```

### Бэкенд

1. Создайте виртуальное окружение:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Запустите сервер:
```bash
python app.py
```

### Фронтенд

1. Установите зависимости:
```bash
cd frontend
npm install
```

2. Запустите приложение:
```bash
npm start
```

## API Endpoints

### GET /api/coffee-types
Получение списка всех сортов кофе

### GET /api/characteristics
Получение списка всех характеристик

### POST /api/classify
Классификация образца кофе
```json
{
  "method": "statistical|ml",
  "input_data": {
    "acidity": 7.5,
    "body": 6.0,
    "aroma": "Фруктовый",
    "flavor": "Сладкий",
    "aftertaste": "Длительное",
    "roast_level": 5.0
  }
}
```

### POST /api/expert/add-coffee-type
Добавление нового сорта кофе
```json
{
  "name": "Арабика"
}
```

### POST /api/expert/add-numeric-range
Добавление диапазона значений для числовой характеристики
```json
{
  "coffee_type_id": 1,
  "characteristic_id": 1,
  "min_value": 6.0,
  "max_value": 8.0
}
```

### POST /api/expert/add-categorical-value
Добавление значения для категориальной характеристики
```json
{
  "coffee_type_id": 1,
  "characteristic_id": 3,
  "value_id": 1
}
```

## Функциональность

### Эксперт
- Добавление новых сортов кофе
- Управление характеристиками сортов
- Настройка диапазонов значений для числовых характеристик
- Настройка возможных значений для категориальных характеристик

### Специалист
- Ввод характеристик образца кофе
- Выбор метода классификации (статистический анализ или машинное обучение)
- Получение результатов классификации с обоснованием 