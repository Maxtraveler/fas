"""Модуль преобразования чисел в различные коды"""


def direct_code(number, bits=8):
    """
    Прямой код числа
    
    Args:
        number: Число для кодирования
        bits: Количество бит (по умолчанию 8)
        
    Returns:
        str: Двоичное представление в прямом коде
    """
    if number >= 0:
        return f"0{bin(number)[2:].zfill(bits-1)}"
    else:
        return f"1{bin(abs(number))[2:].zfill(bits-1)}"


def reverse_code(number, bits=8):
    """
    Обратный код числа
    
    Args:
        number: Число для кодирования
        bits: Количество бит (по умолчанию 8)
        
    Returns:
        str: Двоичное представление в обратном коде
    """
    if number >= 0:
        return direct_code(number, bits)
    else:
        positive = direct_code(abs(number), bits)
        # Инвертировать все биты кроме знакового
        inverted = ''.join('1' if bit == '0' else '0' for bit in positive[1:])
        return f"1{inverted}"


def additional_code(number, bits=8):
    """
    Дополнительный код числа
    
    Args:
        number: Число для кодирования
        bits: Количество бит (по умолчанию 8)
        
    Returns:
        str: Двоичное представление в дополнительном коде
    """
    if number >= 0:
        return direct_code(number, bits)
    else:
        # Получить обратный код
        reverse = reverse_code(number, bits)
        
        # Добавить 1 к обратному коду
        result = list(reverse)
        carry = 1
        for i in range(len(result) - 1, 0, -1):
            if result[i] == '0' and carry == 1:
                result[i] = '1'
                carry = 0
                break
            elif result[i] == '1' and carry == 1:
                result[i] = '0'
                carry = 1
        
        return ''.join(result)


def float_to_binary(number):
    """
    Преобразование числа с плавающей запятой в двоичный формат
    
    Args:
        number: Вещественное число
        
    Returns:
        tuple: (steps, result) - список шагов и результат
    """
    steps = []
    
    # Разделить на целую и дробную части
    integer_part = int(abs(number))
    fractional_part = abs(number) - integer_part
    
    # Преобразовать целую часть
    integer_binary = bin(integer_part)[2:]
    steps.append(f"Целая часть: {integer_part} → {integer_binary}")
    
    # Преобразовать дробную часть
    fractional_binary = ""
    if fractional_part > 0:
        steps.append(f"Дробная часть: {fractional_part}")
        temp = fractional_part
        for i in range(10):  # Ограничение до 10 знаков после запятой
            temp *= 2
            bit = int(temp)
            fractional_binary += str(bit)
            steps.append(f"  {temp/2:.6f} × 2 = {temp:.6f} (целая {bit})")
            temp -= bit
            if temp == 0:
                break
    
    # Объединить части
    if fractional_binary:
        full_binary = f"{integer_binary}.{fractional_binary}"
    else:
        full_binary = integer_binary
    
    # Нормализация
    if integer_binary:
        # Найти позицию первой единицы
        exp = len(integer_binary) - 1
        mantissa = integer_binary[1:] + fractional_binary
        normalized = f"1.{mantissa} × 2^{exp}"
        steps.append(f"Нормализация: {normalized}")
        result = normalized
    else:
        # Найти первую единицу в дробной части
        first_one_pos = fractional_binary.find('1')
        if first_one_pos != -1:
            exp = -(first_one_pos + 1)
            mantissa = fractional_binary[first_one_pos + 1:]
            normalized = f"1.{mantissa} × 2^{exp}"
            steps.append(f"Нормализация: {normalized}")
            result = normalized
        else:
            result = "0"
    
    return steps, result

