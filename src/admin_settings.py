# admin_settings.py
from admin_constants import *
from constants import *


GAME_ID             = "game_id"
QUESTION_ID         = "question_id"
VARIANT_ID          = "variant_id"
INTERNAL_USER_ID    = "internal_user_id"

NEXT_QUESTION       = "Следующий вопрос ➡️"

GAME_WORKFLOW = "game_workflow"

ADMIN_STATES = {
    ADMIN_OPTIONS: {
        LABEL:              "Опции администратора",
        DEPENDENCIES:       None,
        BEGIN_MESSAGE:      "Здравствуйте, администратор!\nВыберите действие",
        ACTION:             CALLBACK,
        FORWARD_STATES:     [CREATE_GAME, GAME_TO_EDIT, GAME_TO_DELETE, GAME_TO_START],
        BACKWARD_STATES:    None,
        END_MESSAGE:        None,
    },
    # create_game(title: str from entered text, created_by: str = None from previous state)
    CREATE_GAME: {
        LABEL:              "Создать игру",
        DEPENDENCIES:       None,
        BEGIN_MESSAGE:      "Введите название игры",
        ACTION:             TEXT,
        FORWARD_STATES:     GAME_OPTIONS,
        BACKWARD_STATES:    None, # TODO: add functionality to add GAME_OPTIONS here
        END_MESSAGE:        "Игра создана",
    },
    GAME_TO_EDIT: {
        LABEL:              "Редактировать игру",
        DEPENDENCIES:       None,
        BEGIN_MESSAGE:      "Выберите игру, которую хотите редактировать",
        ACTION:             LIST,
        FORWARD_STATES:     GAME_OPTIONS,
        BACKWARD_STATES:    ADMIN_OPTIONS,
        END_MESSAGE:        "Игра отредактирована",
    },
    GAME_TO_DELETE: {
        LABEL:              "Удалить игру",
        DEPENDENCIES:       None,
        BEGIN_MESSAGE:      "Выберите игру для удаления",
        ACTION:             LIST,
        FORWARD_STATES:     ADMIN_OPTIONS,
        BACKWARD_STATES:    ADMIN_OPTIONS,
        END_MESSAGE:        "Игра удалена",
    },
    DELETE_GAME: {
        LABEL:              "Удаление игры",
        DEPENDENCIES:       GAME_ID,
        BEGIN_MESSAGE:      None,
        ACTION:             CALLBACK,
        FORWARD_STATES:     [ADMIN_OPTIONS],
        BACKWARD_STATES:    ADMIN_OPTIONS,
        END_MESSAGE:        "Игра удалена",
    },
    GAME_OPTIONS: {
        LABEL:              "Редактирование игры",
        DEPENDENCIES:       GAME_ID,
        BEGIN_MESSAGE:      "Что вы хотите сделать с игрой?",
        ACTION:             CALLBACK,
        FORWARD_STATES:     [ADD_QUESTION, QUESTION_TO_EDIT, QUESTION_TO_DELETE],
        BACKWARD_STATES:    ADMIN_OPTIONS,
        END_MESSAGE:        "Хорошо",
    },
    # create_question(game_id: str from previous state, question_text: str from added text)
    ADD_QUESTION: {
        LABEL:              "Добавить вопрос",
        DEPENDENCIES:       GAME_ID,
        BEGIN_MESSAGE:      "Введите текст вопроса",
        ACTION:             TEXT,
        FORWARD_STATES:     QUESTION_OPTIONS,
        BACKWARD_STATES:    None, # TODO: add functionality to add QUESTION_OPTIONS here
        END_MESSAGE:        "Вопрос добавлен, теперь нужно добавить варианты ответов",
    },
    QUESTION_TO_EDIT: {
        LABEL:              "Выбрать вопрос для редактирования",
        DEPENDENCIES:       GAME_ID,
        BEGIN_MESSAGE:      "Выберите вопрос для редактирования",
        ACTION:             LIST,
        FORWARD_STATES:     QUESTION_OPTIONS,
        BACKWARD_STATES:    GAME_OPTIONS,
        END_MESSAGE:        "Вопрос отредактирован",
    },
    QUESTION_TO_DELETE: {
        LABEL:              "Выбрать вопрос для удаления",
        DEPENDENCIES:       GAME_ID,
        BEGIN_MESSAGE:      "Выберите вопрос для удаления",
        ACTION:             LIST,
        FORWARD_STATES:     GAME_OPTIONS,
        BACKWARD_STATES:    GAME_OPTIONS,
        END_MESSAGE:        "Вопрос удален",
    },
    DELETE_QUESTION: {
        LABEL:              "Удаление вопроса",
        DEPENDENCIES:       QUESTION_ID,
        BEGIN_MESSAGE:      None,
        ACTION:             CALLBACK,
        FORWARD_STATES:     GAME_OPTIONS,
        BACKWARD_STATES:    GAME_OPTIONS,
        END_MESSAGE:        "Вопрос удалён",
    },
    QUESTION_OPTIONS: {
        LABEL:              "Редактировать вопрос",
        DEPENDENCIES:       QUESTION_ID,
        BEGIN_MESSAGE:      "Что вы хотите сделать с вопросом?",
        ACTION:             CALLBACK,
        FORWARD_STATES:     [EDIT_QUESTION_TEXT, VARIANT_OPTIONS, UPDATE_IMAGE, CHANGE_CORRECTNESS, ],
        BACKWARD_STATES:    GAME_OPTIONS,
        END_MESSAGE:        "Хорошо",
    },
    # update_question_text(question_id: str from previous state, new_text: str from entered text)
    EDIT_QUESTION_TEXT: {
        LABEL:              "Редактировать текст вопроса",
        DEPENDENCIES:       QUESTION_ID,
        BEGIN_MESSAGE:      "Введите новый текст вопроса",
        ACTION:             TEXT,
        FORWARD_STATES:     QUESTION_OPTIONS,
        BACKWARD_STATES:    None, # TODO: add functionality to add QUESTION_OPTIONS here
        END_MESSAGE:        "Текст вопроса обновлён",
    },
    VARIANT_OPTIONS: {
        LABEL:              "Редактировть вариант",
        DEPENDENCIES:       QUESTION_ID,
        BEGIN_MESSAGE:      "Выберите, что хотите сделать с вариантами ответов",
        ACTION:             CALLBACK,
        FORWARD_STATES:     [ADD_VARIANT, VARIANT_TO_EDIT, VARIANT_TO_DELETE],
        BACKWARD_STATES:    QUESTION_OPTIONS,
        END_MESSAGE:        "Хорошо",
    },
    UPDATE_IMAGE: {
        LABEL:              "Изменить картинку",
        DEPENDENCIES:       QUESTION_ID,
        BEGIN_MESSAGE:      "Отправьте изображение для вопроса",
        ACTION:             IMAGE,
        FORWARD_STATES:     [QUESTION_OPTIONS],
        BACKWARD_STATES:    None, # TODO: add functionality to add QUESTION_OPTIONS here
        END_MESSAGE:        "Изображение обновлено",
    },
    CHANGE_CORRECTNESS: {
        LABEL:              "Изменить правильные ответы",
        DEPENDENCIES:       QUESTION_ID,
        BEGIN_MESSAGE:      "Выберите правильные варианты ответов",
        ACTION:             CALLBACK, # may be mulit linline via having done button
        FORWARD_STATES:     [QUESTION_OPTIONS],
        BACKWARD_STATES:    QUESTION_OPTIONS,
        END_MESSAGE:        "Правильные ответы обновлены",
    },
    # create_variant(question_id: str from previous state, answer_text: str from entered text)
    ADD_VARIANT: {
        LABEL:              "Добавить вариант",
        DEPENDENCIES:       QUESTION_ID,
        BEGIN_MESSAGE:      "Введите текст для нового варианта",
        ACTION:             TEXT,
        FORWARD_STATES:     VARIANT_OPTIONS,
        BACKWARD_STATES:    None, # TODO: add functionality to write VARIANG_OPTIONS here
        END_MESSAGE:        "Новый вариант добавлен",
    },
    VARIANT_TO_EDIT: {
        LABEL:              "Выбрать вариант для редактирования",
        DEPENDENCIES:       QUESTION_ID,
        BEGIN_MESSAGE:      "Выберите вариант, который хотите редактировать",
        ACTION:             LIST,
        FORWARD_STATES:     EDIT_VARIANT_TEXT,
        BACKWARD_STATES:    VARIANT_OPTIONS,
        END_MESSAGE:        None,
    },
    VARIANT_TO_DELETE: {
        LABEL:              "Выбрать вариант для удаления",
        DEPENDENCIES:       QUESTION_ID,
        BEGIN_MESSAGE:      "Выберите вариант, который хотите удалить",
        ACTION:             LIST,
        FORWARD_STATES:     VARIANT_OPTIONS,
        BACKWARD_STATES:    VARIANT_OPTIONS,
        END_MESSAGE:        "Вариант удалён",
    },
    DELETE_VARIANT: {
        LABEL:              "Удаление варианта",
        DEPENDENCIES:       VARIANT_ID,
        BEGIN_MESSAGE:      None,
        ACTION:             CALLBACK,
        FORWARD_STATES:     VARIANT_OPTIONS,
        BACKWARD_STATES:    None,
        END_MESSAGE:        "Вариант удалён",
    },
    # update_variant_text(variant_id: str from previous state, new_text: str from entered text)
    EDIT_VARIANT_TEXT: {
        LABEL:              "Изменить текст варианта",
        DEPENDENCIES:       VARIANT_ID,
        BEGIN_MESSAGE:      "Введите новый текст варианта",
        ACTION:             TEXT,
        FORWARD_STATES:     VARIANT_OPTIONS,
        BACKWARD_STATES:    None, # TODO: add functionality to write VARIANT_OPTIONS here
        END_MESSAGE:        "Вариант изменён",
    },
    GAME_TO_START: {
        LABEL:              "Начать игру",
        DEPENDENCIES:       INTERNAL_USER_ID,
        BEGIN_MESSAGE:      "Выберите игру, которую хотите запустить",
        ACTION:             LIST,
        FORWARD_STATES:     WAITING_START,
        BACKWARD_STATES:    ADMIN_OPTIONS,
        END_MESSAGE:        None,
    },
    WAITING_START: {
        LABEL:              "Ожидание начала",
        DEPENDENCIES:       GAME_ID,
        BEGIN_MESSAGE:      "Ожидание всех игроков",
        ACTION:             CALLBACK,
        FORWARD_STATES:     [GAME_WORKFLOW],
        BACKWARD_STATES:    ADMIN_OPTIONS,
        END_MESSAGE:        None,
    },
    GAME_WORKFLOW: {
        LABEL:              "Поехали",
        DEPENDENCIES:       GAME_ID,
        BEGIN_MESSAGE:      "Можешь переключать вопросы",
        ACTION:             CALLBACK,
        FORWARD_STATES:     [NEXT_QUESTION],
        BACKWARD_STATES:    None,
        END_MESSAGE:        None,
    },
}
