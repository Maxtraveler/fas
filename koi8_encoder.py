"""Модуль работы с кодировкой КОИ-8"""

# Таблица КОИ-8 для русских букв
KOI8_TABLE = {
    # Строчные буквы (192-223)
    'ю': ('192', '11000000'), 'а': ('193', '11000001'),
    'б': ('194', '11000010'), 'ц': ('195', '11000011'),
    'д': ('196', '11000100'), 'е': ('197', '11000101'),
    'ф': ('198', '11000110'), 'г': ('199', '11000111'),
    'х': ('200', '11001000'), 'и': ('201', '11001001'),
    'й': ('202', '11001010'), 'к': ('203', '11001011'),
    'л': ('204', '11001100'), 'м': ('205', '11001101'),
    'н': ('206', '11001110'), 'о': ('207', '11001111'),
    'п': ('208', '11010000'), 'я': ('209', '11010001'),
    'р': ('210', '11010010'), 'с': ('211', '11010011'),
    'т': ('212', '11010100'), 'у': ('213', '11010101'),
    'ж': ('214', '11010110'), 'в': ('215', '11010111'),
    'ь': ('216', '11011000'), 'ы': ('217', '11011001'),
    'з': ('218', '11011010'), 'ш': ('219', '11011011'),
    'э': ('220', '11011100'), 'щ': ('221', '11011101'),
    'ч': ('222', '11011110'), 'ё': ('223', '11011111'),
    
    # Прописные буквы (224-255)
    'Ю': ('224', '11100000'), 'А': ('225', '11100001'),
    'Б': ('226', '11100010'), 'Ц': ('227', '11100011'),
    'Д': ('228', '11100100'), 'Е': ('229', '11100101'),
    'Ф': ('230', '11100110'), 'Г': ('231', '11100111'),
    'Х': ('232', '11101000'), 'И': ('233', '11101001'),
    'Й': ('234', '11101010'), 'К': ('235', '11101011'),
    'Л': ('236', '11101100'), 'М': ('237', '11101101'),
    'Н': ('238', '11101110'), 'О': ('239', '11101111'),
    'П': ('240', '11110000'), 'Я': ('241', '11110001'),
    'Р': ('242', '11110010'), 'С': ('243', '11110011'),
    'Т': ('244', '11110100'), 'У': ('245', '11110101'),
    'Ж': ('246', '11110110'), 'В': ('247', '11110111'),
    'Ь': ('248', '11111000'), 'Ы': ('249', '11111001'),
    'З': ('250', '11111010'), 'Ш': ('251', '11111011'),
    'Э': ('252', '11111100'), 'Щ': ('253', '11111101'),
    'Ч': ('254', '11111110'), 'Ъ': ('255', '11111111')
}

# Обратная таблица для декодирования
KOI8_REVERSE = {v[1]: k for k, v in KOI8_TABLE.items()}


def koi8_encode(text):
    """
    Кодирование текста в КОИ-8
    
    Args:
        text: Текст для кодирования
        
    Returns:
        tuple: (encoded_binary, steps) - закодированный двоичный код и список шагов
    """
    encoded_binary = ""
    steps = []
    
    for char in text:
        if char in KOI8_TABLE:
            decimal, binary = KOI8_TABLE[char]
            encoded_binary += binary
            steps.append(f"'{char}' → {decimal} (десятичное) → {binary} (двоичное)")
        elif char.isascii():
            # ASCII символы остаются как есть
            ascii_code = ord(char)
            binary = format(ascii_code, '08b')
            encoded_binary += binary
            steps.append(f"'{char}' → {ascii_code} (ASCII) → {binary} (двоичное)")
        else:
            # Неизвестный символ
            steps.append(f"'{char}' → символ не найден в таблице КОИ-8")
    
    return encoded_binary, steps


def koi8_decode(binary_string):
    """
    Декодирование двоичного кода из КОИ-8
    
    Args:
        binary_string: Двоичная строка (длина должна быть кратна 8)
        
    Returns:
        tuple: (decoded_text, steps) - декодированный текст и список шагов
    """
    decoded_text = ""
    steps = []
    
    # Разбить на байты (по 8 бит)
    for i in range(0, len(binary_string), 8):
        byte = binary_string[i:i+8]
        if len(byte) == 8:
            if byte in KOI8_REVERSE:
                char = KOI8_REVERSE[byte]
                decimal = KOI8_TABLE[char][0]
                decoded_text += char
                steps.append(f"{byte} → {decimal} (десятичное) → '{char}'")
            else:
                # Попробовать как ASCII
                try:
                    decimal = int(byte, 2)
                    if 32 <= decimal <= 126:  # Печатные ASCII символы
                        char = chr(decimal)
                        decoded_text += char
                        steps.append(f"{byte} → {decimal} (ASCII) → '{char}'")
                    else:
                        decoded_text += '?'
                        steps.append(f"{byte} → неизвестный символ")
                except:
                    decoded_text += '?'
                    steps.append(f"{byte} → ошибка декодирования")
    
    return decoded_text, steps


def block_parity_encode(binary_sequence, block_size=8):
    """
    Блочное кодирование с контролем четности
    
    Args:
        binary_sequence: Двоичная последовательность
        block_size: Размер блока (по умолчанию 8)
        
    Returns:
        list: Список кортежей (block, ones_count, parity_bit, encoded_block)
    """
    results = []
    
    # Разбить на блоки
    for i in range(0, len(binary_sequence), block_size):
        block = binary_sequence[i:i+block_size]
        
        # Добавить бит четности
        ones_count = block.count('1')
        parity_bit = '0' if ones_count % 2 == 0 else '1'
        encoded_block = block + parity_bit
        
        results.append((block, ones_count, parity_bit, encoded_block))
    
    return results

