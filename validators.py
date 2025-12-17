"""Модуль валидации входных данных"""


def validate_binary(binary_string):
    """
    Валидация двоичной последовательности
    
    Args:
        binary_string: Строка с двоичными данными
        
    Returns:
        tuple: (is_valid, message)
    """
    if not binary_string:
        return False, "Пустая последовательность"
    if not all(bit in '01' for bit in binary_string):
        return False, "Содержит недопустимые символы (только 0 и 1)"
    return True, "OK"


def validate_number(value, min_val=None, max_val=None):
    """
    Валидация числового значения
    
    Args:
        value: Значение для проверки
        min_val: Минимальное допустимое значение
        max_val: Максимальное допустимое значение
        
    Returns:
        tuple: (is_valid, message)
    """
    try:
        num = int(value)
        if min_val is not None and num < min_val:
            return False, f"Значение должно быть не меньше {min_val}"
        if max_val is not None and num > max_val:
            return False, f"Значение должно быть не больше {max_val}"
        return True, "OK"
    except ValueError:
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                return False, f"Значение должно быть не меньше {min_val}"
            if max_val is not None and num > max_val:
                return False, f"Значение должно быть не больше {max_val}"
            return True, "OK"
        except ValueError:
            return False, "Некорректное числовое значение"


def validate_float(value, min_val=None, max_val=None):
    """
    Валидация вещественного числа
    
    Args:
        value: Значение для проверки
        min_val: Минимальное допустимое значение
        max_val: Максимальное допустимое значение
        
    Returns:
        tuple: (is_valid, message, float_value)
    """
    try:
        num = float(value)
        if min_val is not None and num < min_val:
            return False, f"Значение должно быть не меньше {min_val}", None
        if max_val is not None and num > max_val:
            return False, f"Значение должно быть не больше {max_val}", None
        return True, "OK", num
    except ValueError:
        return False, "Некорректное числовое значение", None


def validate_digits(digit_string):
    """
    Валидация строки из цифр
    
    Args:
        digit_string: Строка с цифрами
        
    Returns:
        tuple: (is_valid, message)
    """
    if not digit_string:
        return False, "Пустая строка"
    if not all(char.isdigit() for char in digit_string):
        return False, "Строка должна содержать только цифры"
    return True, "OK"

