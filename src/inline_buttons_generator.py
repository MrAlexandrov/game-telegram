from admin_constants import *
from admin_settings import *
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from logger import get_logger

logger = get_logger(__name__)

async def generate_inline_buttons_by_state(state: str, game_id: str | None = None, question_id: str | None = None, variant_id: str | None = None):
    logger.debug("called")
    if state not in ADMIN_STATES:
        logger.error(f"state '{state}' does not exists")
        return None
    if FORWARD_STATES not in ADMIN_STATES[state] or ADMIN_STATES[state][FORWARD_STATES] is None:
        logger.error(f"inline buttons are not expected in state '{state}'")
        return None
    keyboard = []
    for button in ADMIN_STATES[state][FORWARD_STATES]:
        callback_data = f"{ADMIN}:{button}"
        if ADMIN_STATES[button][DEPENDENCIES] == GAME_ID:
            if game_id is None:
                logger.error("game_id expected")
                return None
            callback_data += f":{game_id}"
        if ADMIN_STATES[button][DEPENDENCIES] == QUESTION_ID:
            if question_id is None:
                logger.error("quesiton_id expected")
                return None
            callback_data += f":{question_id}"
        if ADMIN_STATES[button][DEPENDENCIES] == VARIANT_ID:
            if variant_id is None:
                logger.error("variant_id expected")
                return None
            callback_data += f":{variant_id}"
        if len(callback_data.split(":")) > 4:
            logger.error("generated callback is too long")
            return None
        keyboard.append([InlineKeyboardButton(ADMIN_STATES[button][LABEL], callback_data=callback_data)])
    if ADMIN_STATES[state][BACKWARD_STATES] != None:
        for button in ADMIN_STATES[state][BACKWARD_STATES]:
            callback_data = f"{ADMIN}:{button}"
            if ADMIN_STATES[button][DEPENDENCIES] == GAME_ID:
                if game_id is None:
                    logger.error("game_id expected")
                    return None
                callback_data += f":{game_id}"
            if ADMIN_STATES[button][DEPENDENCIES] == QUESTION_ID:
                if question_id is None:
                    logger.error("quesiton_id expected")
                    return None
                callback_data += f":{question_id}"
            if ADMIN_STATES[button][DEPENDENCIES] == VARIANT_ID:
                if variant_id is None:
                    logger.error("variant_id expected")
                    return None
                callback_data += f":{variant_id}"
            if len(callback_data.split(":")) > 4:
                logger.error("generated callback is too long")
                return None
            keyboard.append([InlineKeyboardButton(ADMIN_STATES[button][LABEL], callback_data=callback_data)])
    print(f"keyboard = {keyboard}")
    return InlineKeyboardMarkup(keyboard)
