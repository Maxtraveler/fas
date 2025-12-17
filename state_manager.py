"""Модуль управления состоянием пользователя"""

import time
from config import SESSION_TIMEOUT

# Хранение состояний пользователей в памяти
user_states = {}


def get_user_state(user_id):
    """
    Получить состояние пользователя
    
    Args:
        user_id: ID пользователя
        
    Returns:
        dict: Состояние пользователя
    """
    if user_id not in user_states:
        user_states[user_id] = {
            "current_menu": "main_menu",
            "current_method": None,
            "input_data": {},
            "last_activity": time.time(),
            "conversation_step": 0
        }
    return user_states[user_id]


def update_user_state(user_id, **kwargs):
    """
    Обновить состояние пользователя
    
    Args:
        user_id: ID пользователя
        **kwargs: Поля для обновления
    """
    state = get_user_state(user_id)
    state.update(kwargs)
    state["last_activity"] = time.time()


def clear_user_state(user_id):
    """
    Очистить состояние пользователя
    
    Args:
        user_id: ID пользователя
    """
    if user_id in user_states:
        del user_states[user_id]


def is_session_expired(user_id):
    """
    Проверить, истекла ли сессия пользователя
    
    Args:
        user_id: ID пользователя
        
    Returns:
        bool: True если сессия истекла
    """
    if user_id not in user_states:
        return False
    
    state = user_states[user_id]
    elapsed = time.time() - state["last_activity"]
    return elapsed > SESSION_TIMEOUT


def reset_user_state(user_id):
    """
    Сбросить состояние пользователя к начальному
    
    Args:
        user_id: ID пользователя
    """
    user_states[user_id] = {
        "current_menu": "main_menu",
        "current_method": None,
        "input_data": {},
        "last_activity": time.time(),
        "conversation_step": 0
    }

