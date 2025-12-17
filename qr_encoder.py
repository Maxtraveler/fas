"""Модуль QR-кодирования"""

from calculators.koi8_encoder import koi8_encode


def numeric_qr_encode(digits):
    """
    Цифровое QR-кодирование
    
    Args:
        digits: Строка с цифрами
        
    Returns:
        tuple: (encoded_bits, steps) - закодированные биты и список шагов
    """
    result_bits = ""
    steps = []
    
    # Обработать группы по 3 цифры
    i = 0
    while i < len(digits):
        group = digits[i:i+3]
        
        if len(group) == 3:
            # 3 цифры → 10 бит
            value = int(group)
            bits = format(value, '010b')
            result_bits += bits
            steps.append(f"Группа '{group}' → {value} → {bits} (10 бит)")
            i += 3
        elif len(group) == 2:
            # 2 цифры → 7 бит
            value = int(group)
            bits = format(value, '07b')
            result_bits += bits
            steps.append(f"Группа '{group}' → {value} → {bits} (7 бит)")
            i += 2
        else:
            # 1 цифра → 4 бита
            value = int(group)
            bits = format(value, '04b')
            result_bits += bits
            steps.append(f"Группа '{group}' → {value} → {bits} (4 бита)")
            i += 1
    
    return result_bits, steps


def alphanumeric_qr_encode(text):
    """
    Буквенно-цифровое QR-кодирование с использованием КОИ-8
    
    Args:
        text: Текст для кодирования
        
    Returns:
        tuple: (encoded_bits, steps) - закодированные биты и список шагов
    """
    # Используем КОИ-8 кодирование
    encoded_bits, koi8_steps = koi8_encode(text)
    
    # Форматируем шаги для QR-кодирования
    steps = []
    steps.append("**Использована кодировка КОИ-8:**")
    steps.extend([f"  {step}" for step in koi8_steps])
    steps.append(f"\n**Результат:** `{encoded_bits}`")
    
    return encoded_bits, steps


def numeric_qr_encode_with_mask(digits, mask):
    """
    Цифровое QR-кодирование с наложением маски
    
    Args:
        digits: Строка с цифрами
        mask: Двоичная маска для наложения
        
    Returns:
        tuple: (encoded_bits, masked_bits, steps) - закодированные биты, результат с маской, список шагов
    """
    # Сначала закодировать число
    encoded_bits, encode_steps = numeric_qr_encode(digits)
    
    steps = []
    steps.append("**Шаг 1: Кодирование числа**")
    steps.extend([f"  {step}" for step in encode_steps])
    steps.append(f"  **Результат:** `{encoded_bits}`")
    
    # Наложить маску (XOR)
    steps.append(f"\n**Шаг 2: Наложение маски**")
    steps.append(f"  **Маска:** `{mask}`")
    
    # Выровнять длину маски под длину закодированных битов
    if len(mask) < len(encoded_bits):
        # Повторить маску
        mask_extended = (mask * ((len(encoded_bits) // len(mask)) + 1))[:len(encoded_bits)]
    elif len(mask) > len(encoded_bits):
        # Обрезать маску
        mask_extended = mask[:len(encoded_bits)]
    else:
        mask_extended = mask
    
    steps.append(f"  **Выровненная маска:** `{mask_extended}`")
    
    # Применить XOR
    masked_bits = ""
    xor_steps = []
    for i in range(len(encoded_bits)):
        bit1 = int(encoded_bits[i])
        bit2 = int(mask_extended[i])
        result_bit = bit1 ^ bit2
        masked_bits += str(result_bit)
        if i < 8:  # Показать первые 8 бит для примера
            xor_steps.append(f"  Бит {i+1}: {bit1} XOR {bit2} = {result_bit}")
    
    if len(encoded_bits) > 8:
        xor_steps.append(f"  ... (аналогично для остальных {len(encoded_bits) - 8} бит)")
    
    steps.extend(xor_steps)
    steps.append(f"  **Результат с маской:** `{masked_bits}`")
    
    # Преобразовать в десятичное
    decimal_result = int(masked_bits, 2)
    steps.append(f"\n**Шаг 3: Преобразование в десятичное**")
    steps.append(f"  `{masked_bits}` (двоичное) = `{decimal_result}` (десятичное)")
    
    return encoded_bits, masked_bits, steps

