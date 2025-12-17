"""Модуль расчета контрольных сумм и кодов обнаружения ошибок"""


def parity_check(data_bits):
    """
    Проверка на четность
    
    Args:
        data_bits: Строка с битами данных
        
    Returns:
        tuple: (encoded, ones_count, parity_bit) - закодированная последовательность, количество единиц, бит четности
    """
    ones_count = data_bits.count('1')
    parity_bit = '0' if ones_count % 2 == 0 else '1'
    encoded = data_bits + parity_bit
    return encoded, ones_count, parity_bit


def constant_weight_code(data_bits, weight):
    """
    Код с постоянным весом
    
    Args:
        data_bits: Строка с битами данных
        weight: Требуемый вес (количество единиц)
        
    Returns:
        tuple: (encoded, current_weight, check_bits) - закодированная последовательность, текущий вес, проверочные биты
    """
    current_weight = data_bits.count('1')
    needed_ones = weight - current_weight
    
    if needed_ones < 0:
        # Нужно уменьшить количество единиц
        check_bits = '0' * abs(needed_ones)
    elif needed_ones > 0:
        # Нужно увеличить количество единиц
        check_bits = '1' * needed_ones
    else:
        check_bits = '0'
    
    encoded = data_bits + check_bits
    return encoded, current_weight, check_bits


def inverse_code(data_bits):
    """
    Инверсный код
    
    Args:
        data_bits: Строка с битами данных
        
    Returns:
        tuple: (encoded, ones_count, check_bits) - закодированная последовательность, количество единиц, проверочные биты
    """
    ones_count = data_bits.count('1')
    
    if ones_count % 2 == 0:
        check_bits = data_bits
    else:
        # Инвертировать все биты
        check_bits = ''.join('1' if bit == '0' else '0' for bit in data_bits)
    
    encoded = data_bits + check_bits
    return encoded, ones_count, check_bits


def calculate_control_number(number, weights=None, modulus=9):
    """
    Расчет контрольного числа
    
    Args:
        number: Число для расчета
        weights: Веса для позиций (по умолчанию 1, 2, 3, ...)
        modulus: Модуль для расчета (по умолчанию 9)
        
    Returns:
        tuple: (control_digit, weighted_sum, weights) - контрольная цифра, взвешенная сумма, использованные веса
    """
    number_str = str(number)
    
    if weights is None:
        weights = list(range(1, len(number_str) + 1))
    else:
        # Дополнить веса до нужной длины
        while len(weights) < len(number_str):
            weights.append(1)
        weights = weights[:len(number_str)]
    
    digits = [int(d) for d in number_str]
    weighted_sum = sum(digit * weight for digit, weight in zip(digits, weights))
    control_digit = weighted_sum % modulus
    
    return control_digit, weighted_sum, weights

