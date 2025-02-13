# gamer_settings.py
from gamer_constants import *
from constants import *

GAMER_STATES = {
    # CODE_TO_GAME: {
    #     LABEL:              "Ожидание ввода кода",
    #     DEPENDENCIES:       None,
    #     BEGIN_MESSAGE:      "Введи код игры \"LEXA\"",
    #     ACTION:             TEXT,
    #     FORWARD_STATES:     [GAMER_NICKNAME],
    #     BACKWARD_STATES:    None,
    #     END_MESSAGE:        None,
    # },
    GAMER_NICKNAME: {
        LABEL:              "Ввод никнейма",
        DEPENDENCIES:       None,
        BEGIN_MESSAGE:      "Введи никнейм",
        ACTION:             TEXT,
        FORWARD_STATES:     [WAITING_START],
        BACKWARD_STATES:    None,
        END_MESSAGE:        None,
    },
    WAITING_START: {
        LABEL:              "Ожидание начала игры",
        DEPENDENCIES:       None, 
        BEGIN_MESSAGE:      "Теперь всех ждём 😐",
        ACTION:             None,
        FORWARD_STATES:     [GAME_WORKFLOW],
        BACKWARD_STATES:    None,
        END_MESSAGE:        None,
    },
    GAME_WORKFLOW: {
        LABEL:              "Тут игра должна идти",
        DEPENDENCIES:       None,
        BEGIN_MESSAGE:      None,
        ACTION:             None,
        FORWARD_STATES:     None,
        BACKWARD_STATES:    None,
        END_MESSAGE:        None,
    },
}
