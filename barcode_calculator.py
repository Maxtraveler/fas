"""Модуль расчета контрольной цифры для EAN-13"""


def ean13_checksum(first_12_digits):
    """
    Расчет контрольной цифры для EAN-13
    
    Args:
        first_12_digits: Первые 12 цифр штрих-кода (строка)
        
    Returns:
        tuple: (checksum, even_sum, odd_sum, total) - контрольная цифра, сумма четных, сумма нечетных, общая сумма
    """
    if len(first_12_digits) != 12:
        raise ValueError("Должно быть ровно 12 цифр")
    
    # Четные позиции (2, 4, 6, 8, 10, 12) - индексы 1, 3, 5, 7, 9, 11
    even_sum = sum(int(first_12_digits[i]) for i in range(1, 12, 2))
    
    # Нечетные позиции (1, 3, 5, 7, 9, 11) - индексы 0, 2, 4, 6, 8, 10
    odd_sum = sum(int(first_12_digits[i]) for i in range(0, 12, 2))
    
    total = odd_sum + even_sum * 3
    checksum = (10 - (total % 10)) % 10
    
    return checksum, even_sum, odd_sum, total

