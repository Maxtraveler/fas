"""Модуль преобразования систем счисления"""


def convert_base(number, from_base, to_base):
    """
    Перевод числа из одной системы счисления в другую
    
    Args:
        number: Число для преобразования (строка)
        from_base: Исходная система счисления (2-36)
        to_base: Целевая система счисления (2-36)
        
    Returns:
        tuple: (result, steps) - результат и список шагов
    """
    steps = []
    
    # Преобразовать в десятичную систему
    if from_base != 10:
        decimal_value = 0
        steps.append(f"Преобразование из {from_base}-й системы в 10-ю:")
        for i, digit in enumerate(reversed(str(number))):
            digit_value = int(digit, from_base)
            power = from_base ** i
            decimal_value += digit_value * power
            steps.append(f"  {digit} × {from_base}^{i} = {digit_value} × {power} = {digit_value * power}")
        steps.append(f"  Итого: {decimal_value}")
    else:
        decimal_value = int(number)
        steps.append(f"Исходное число в 10-й системе: {decimal_value}")
    
    # Преобразовать из десятичной в целевую систему
    if to_base == 10:
        return str(decimal_value), steps
    
    steps.append(f"\nПреобразование из 10-й системы в {to_base}-ю:")
    result = ""
    n = decimal_value
    
    if n == 0:
        return "0", steps
    
    step_num = 0
    while n > 0:
        remainder = n % to_base
        if remainder < 10:
            digit = str(remainder)
        else:
            digit = chr(55 + remainder)  # A-Z для 10-35
        result = digit + result
        steps.append(f"  {n} ÷ {to_base} = {n // to_base} (остаток {remainder} → '{digit}')")
        n //= to_base
        step_num += 1
    
    steps.append(f"  Результат: {result}")
    return result, steps

