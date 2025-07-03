# Форматы игровых паков

## Обзор

Этот документ описывает JSON-форматы для различных типов игр, поддерживаемых системой.

## Формат викторины (Quiz)

### Базовая структура

```json
{
  "name": "Название викторины",
  "description": "Описание викторины",
  "type": "quiz",
  "settings": {
    "time_per_question": 30,
    "show_correct_answer": true,
    "allow_skip": false,
    "points_per_correct": 10,
    "penalty_for_wrong": -2,
    "shuffle_questions": false,
    "shuffle_options": true
  },
  "questions": [
    // Массив вопросов
  ]
}
```

### Типы вопросов

#### 1. Множественный выбор (Multiple Choice)

```json
{
  "id": 1,
  "question": "В каком году была основана Москва?",
  "type": "multiple_choice",
  "options": ["1147", "1156", "1174", "1185"],
  "correct_answer": 0,
  "explanation": "Москва была основана в 1147 году князем Юрием Долгоруким",
  "points": 10,
  "time_limit": 30,
  "image_url": "https://example.com/moscow.jpg"
}
```

#### 2. Текстовый ввод (Text Input)

```json
{
  "id": 2,
  "question": "Кто был первым царем всея Руси?",
  "type": "text_input",
  "correct_answers": ["Иван Грозный", "Иван IV", "Иван Васильевич"],
  "case_sensitive": false,
  "points": 15,
  "time_limit": 45,
  "hint": "Прозвище этого царя связано с его характером"
}
```

#### 3. Правда/Ложь (True/False)

```json
{
  "id": 3,
  "question": "Петр I был первым императором России",
  "type": "true_false",
  "correct_answer": true,
  "explanation": "Петр I принял титул императора в 1721 году",
  "points": 5,
  "time_limit": 20
}
```

#### 4. Числовой ответ (Numeric)

```json
{
  "id": 4,
  "question": "В каком году началась Великая Отечественная война?",
  "type": "numeric",
  "correct_answer": 1941,
  "tolerance": 0,
  "points": 10,
  "time_limit": 25
}
```

### Полный пример викторины

```json
{
  "name": "Викторина по истории России",
  "description": "Вопросы о ключевых событиях российской истории",
  "type": "quiz",
  "author": "Администратор",
  "difficulty": "medium",
  "estimated_time": 15,
  "settings": {
    "time_per_question": 30,
    "show_correct_answer": true,
    "allow_skip": false,
    "points_per_correct": 10,
    "penalty_for_wrong": -2,
    "shuffle_questions": true,
    "shuffle_options": true,
    "show_progress": true,
    "show_timer": true
  },
  "questions": [
    {
      "id": 1,
      "question": "В каком году была основана Москва?",
      "type": "multiple_choice",
      "options": ["1147", "1156", "1174", "1185"],
      "correct_answer": 0,
      "explanation": "Москва была основана в 1147 году князем Юрием Долгоруким",
      "points": 10,
      "time_limit": 30
    },
    {
      "id": 2,
      "question": "Кто написал 'Войну и мир'?",
      "type": "text_input",
      "correct_answers": ["Лев Толстой", "Толстой", "Л.Н. Толстой"],
      "case_sensitive": false,
      "points": 15,
      "time_limit": 25,
      "hint": "Великий русский писатель XIX века"
    },
    {
      "id": 3,
      "question": "Петр I был первым императором России",
      "type": "true_false",
      "correct_answer": true,
      "explanation": "Петр I принял титул императора в 1721 году после победы в Северной войне",
      "points": 8,
      "time_limit": 20
    }
  ]
}
```

## Формат игры "100 к 1" (Hundred to One)

### Базовая структура

```json
{
  "name": "100 к 1: Семейные темы",
  "description": "Популярные ответы на семейные темы",
  "type": "hundred_to_one",
  "settings": {
    "teams_count": 2,
    "rounds_count": 3,
    "final_round": true,
    "simple_game_multiplier": 1,
    "double_game_multiplier": 2,
    "triple_game_multiplier": 3,
    "final_game_multiplier": 5,
    "wrong_answers_limit": 3
  },
  "rounds": [
    // Массив раундов
  ]
}
```

### Структура раунда

```json
{
  "id": 1,
  "question": "Что люди обычно забывают дома?",
  "type": "simple",
  "answers": [
    {"text": "Ключи", "points": 40},
    {"text": "Телефон", "points": 25},
    {"text": "Кошелек", "points": 15},
    {"text": "Документы", "points": 10},
    {"text": "Очки", "points": 6},
    {"text": "Зонт", "points": 4}
  ],
  "alternative_answers": {
    "Ключи": ["ключ", "ключик", "связка ключей"],
    "Телефон": ["мобильный", "смартфон", "сотовый"],
    "Кошелек": ["портмоне", "бумажник", "деньги"]
  }
}
```

### Полный пример игры "100 к 1"

```json
{
  "name": "100 к 1: Повседневная жизнь",
  "description": "Вопросы о повседневных ситуациях",
  "type": "hundred_to_one",
  "author": "Администратор",
  "difficulty": "easy",
  "estimated_time": 25,
  "settings": {
    "teams_count": 2,
    "rounds_count": 4,
    "final_round": true,
    "simple_game_multiplier": 1,
    "double_game_multiplier": 2,
    "triple_game_multiplier": 3,
    "final_game_multiplier": 5,
    "wrong_answers_limit": 3,
    "time_per_answer": 30,
    "show_remaining_answers": false
  },
  "rounds": [
    {
      "id": 1,
      "question": "Что люди обычно забывают дома?",
      "type": "simple",
      "answers": [
        {"text": "Ключи", "points": 40},
        {"text": "Телефон", "points": 25},
        {"text": "Кошелек", "points": 15},
        {"text": "Документы", "points": 10},
        {"text": "Очки", "points": 6},
        {"text": "Зонт", "points": 4}
      ],
      "alternative_answers": {
        "Ключи": ["ключ", "ключик", "связка ключей"],
        "Телефон": ["мобильный", "смартфон", "сотовый", "мобила"],
        "Кошелек": ["портмоне", "бумажник", "деньги", "кошель"]
      }
    },
    {
      "id": 2,
      "question": "Что покупают в первую очередь при переезде в новую квартиру?",
      "type": "double",
      "answers": [
        {"text": "Мебель", "points": 35},
        {"text": "Холодильник", "points": 28},
        {"text": "Кровать", "points": 18},
        {"text": "Плита", "points": 12},
        {"text": "Стиральная машина", "points": 4},
        {"text": "Телевизор", "points": 3}
      ]
    },
    {
      "id": 3,
      "question": "Что делают люди в выходные дни?",
      "type": "triple",
      "answers": [
        {"text": "Отдыхают", "points": 45},
        {"text": "Убираются", "points": 22},
        {"text": "Готовят", "points": 15},
        {"text": "Гуляют", "points": 10},
        {"text": "Смотрят телевизор", "points": 5},
        {"text": "Спят", "points": 3}
      ]
    },
    {
      "id": 4,
      "question": "Назовите профессию, где нужна хорошая память",
      "type": "final",
      "answers": [
        {"text": "Учитель", "points": 30},
        {"text": "Врач", "points": 25},
        {"text": "Актер", "points": 20},
        {"text": "Переводчик", "points": 15},
        {"text": "Юрист", "points": 10}
      ]
    }
  ]
}
```

## Расширенные форматы

### Викторина с медиа-контентом

```json
{
  "name": "Музыкальная викторина",
  "type": "quiz",
  "settings": {
    "time_per_question": 45,
    "show_correct_answer": true,
    "points_per_correct": 15
  },
  "questions": [
    {
      "id": 1,
      "question": "Кто исполняет эту песню?",
      "type": "multiple_choice",
      "audio_url": "https://example.com/song.mp3",
      "options": ["Группа А", "Группа Б", "Группа В", "Группа Г"],
      "correct_answer": 1,
      "points": 15
    },
    {
      "id": 2,
      "question": "Что изображено на картине?",
      "type": "text_input",
      "image_url": "https://example.com/painting.jpg",
      "correct_answers": ["Мона Лиза", "Джоконда"],
      "points": 20
    }
  ]
}
```

### Командная викторина

```json
{
  "name": "Командная викторина",
  "type": "quiz",
  "settings": {
    "team_mode": true,
    "max_team_size": 4,
    "time_per_question": 60,
    "allow_team_discussion": true,
    "points_per_correct": 20
  },
  "questions": [
    {
      "id": 1,
      "question": "Сложный вопрос для команды",
      "type": "text_input",
      "difficulty": "hard",
      "correct_answers": ["правильный ответ"],
      "points": 30,
      "time_limit": 120
    }
  ]
}
```

## Валидация форматов

### Обязательные поля для всех игр

- `name` (string): Название игры
- `type` (string): Тип игры ("quiz", "hundred_to_one", etc.)
- `description` (string): Описание игры

### Обязательные поля для викторины

- `questions` (array): Массив вопросов
- Каждый вопрос должен содержать:
  - `id` (number): Уникальный идентификатор
  - `question` (string): Текст вопроса
  - `type` (string): Тип вопроса
  - `points` (number): Количество очков

### Обязательные поля для "100 к 1"

- `rounds` (array): Массив раундов
- Каждый раунд должен содержать:
  - `id` (number): Уникальный идентификатор
  - `question` (string): Вопрос раунда
  - `answers` (array): Массив ответов с очками

## Примеры использования

### Создание простой викторины

1. Создайте JSON-файл с вопросами
2. Загрузите через админ-панель
3. Создайте сессию на основе пака
4. Запустите игру

### Создание игры "100 к 1"

1. Подготовьте вопросы с популярными ответами
2. Укажите очки для каждого ответа
3. Добавьте альтернативные варианты ответов
4. Настройте параметры игры (количество команд, раундов)

Эти форматы обеспечивают гибкость и расширяемость системы для различных типов игр.