"""Модуль работы с кодом Хэмминга"""


def is_power_of_two(n):
    """Проверка, является ли число степенью двойки"""
    return n > 0 and (n & (n - 1)) == 0


def hamming_encode(data_bits):
    """
    Кодирование данных кодом Хэмминга
    
    Args:
        data_bits: Строка с битами данных
        
    Returns:
        tuple: (encoded_code, r, n) - закодированный код, количество контрольных битов, общая длина
    """
    m = len(data_bits)
    
    # Определить количество контрольных битов
    r = 1
    while 2**r < m + r + 1:
        r += 1
    
    # Создать заготовку с контрольными битами
    n = m + r
    code = ['0'] * n
    
    # Заполнить информационные биты (позиции, не являющиеся степенями двойки)
    data_index = 0
    for i in range(1, n + 1):
        if not is_power_of_two(i):
            if data_index < m:
                code[i-1] = data_bits[data_index]
                data_index += 1
    
    # Вычислить контрольные биты
    for i in range(r):
        pos = 2**i
        parity = 0
        for j in range(1, n + 1):
            if j & pos:  # Проверяем, установлен ли i-й бит в позиции j
                parity ^= int(code[j-1])
        code[pos-1] = str(parity)
    
    return ''.join(code), r, n


def hamming_decode(received_code):
    """
    Декодирование кода Хэмминга с обнаружением и исправлением ошибок
    
    Args:
        received_code: Принятая последовательность битов
        
    Returns:
        tuple: (data_bits, error_pos, corrected_code) - извлеченные данные, позиция ошибки, исправленный код
    """
    n = len(received_code)
    
    # Определить количество контрольных битов
    r = 0
    while 2**r < n:
        r += 1
    
    # Проверить контрольные биты
    error_pos = 0
    for i in range(r):
        pos = 2**i
        parity = 0
        for j in range(1, n + 1):
            if j & pos:
                parity ^= int(received_code[j-1])
        if parity != 0:
            error_pos += pos
    
    # Исправить ошибку
    corrected = list(received_code)
    if error_pos > 0 and error_pos <= n:
        corrected[error_pos-1] = '1' if corrected[error_pos-1] == '0' else '0'
        corrected_code = ''.join(corrected)
    else:
        corrected_code = received_code
    
    # Извлечь информационные биты
    data_bits = []
    for i in range(1, n + 1):
        if not is_power_of_two(i):
            data_bits.append(corrected_code[i-1])
    
    return ''.join(data_bits), error_pos, corrected_code

