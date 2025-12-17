"""Обработчики модуля кодов и ошибок"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from handlers.states import ErrorDetectionStates, ErrorCorrectionStates, ClassificationStates
from utils.state_manager import update_user_state, is_session_expired
from utils.validators import validate_binary, validate_number, validate_digits
from utils.formatters import format_parity_result, format_hamming_encode_result, format_hamming_decode_result
from calculators.checksum_calculator import parity_check, constant_weight_code, inverse_code, calculate_control_number
from calculators.hamming_code import hamming_encode, hamming_decode
from config import ERROR_MESSAGES

router = Router()


def calculate_redundancy(total_combinations, used_combinations):
    """
    Расчет избыточности
    
    Args:
        total_combinations: Общее количество комбинаций
        used_combinations: Используемое количество комбинаций
        
    Returns:
        tuple: (redundancy, unused) - избыточность в процентах, неиспользуемые комбинации
    """
    unused = total_combinations - used_combinations
    redundancy = (unused / total_combinations) * 100
    return redundancy, unused


@router.callback_query(F.data == "codes_and_errors")
async def handle_codes_and_errors(callback: CallbackQuery):
    """Обработчик выбора раздела 'Коды и ошибки'"""
    user_id = callback.from_user.id
    
    if is_session_expired(user_id):
        await callback.answer(ERROR_MESSAGES["timeout"], show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton(text="🛡️ Коды обнаружения ошибок", callback_data="error_detection")],
        [InlineKeyboardButton(text="🔧 Коды исправления ошибок", callback_data="error_correction")],
        [InlineKeyboardButton(text="📁 Классификация и кодирование", callback_data="classification")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    message = """
🛡️ **КОДЫ И ОШИБКИ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Выберите раздел:
"""
    
    await callback.message.edit_text(
        text=message,
        reply_markup=reply_markup
    )


# ========== КОДЫ ОБНАРУЖЕНИЯ ОШИБОК ==========

@router.callback_query(F.data == "error_detection")
async def handle_error_detection(callback: CallbackQuery):
    """Обработчик выбора раздела 'Коды обнаружения ошибок'"""
    user_id = callback.from_user.id
    
    if is_session_expired(user_id):
        await callback.answer(ERROR_MESSAGES["timeout"], show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton(text="🔍 Проверка на четность", callback_data="parity_check")],
        [InlineKeyboardButton(text="⚖️ Код с постоянным весом", callback_data="constant_weight")],
        [InlineKeyboardButton(text="🔄 Инверсный код", callback_data="inverse_code")],
        [InlineKeyboardButton(text="🎯 Расчет контрольного числа", callback_data="control_number")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="codes_and_errors"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    message = """
🛡️ **КОДЫ ОБНАРУЖЕНИЯ ОШИБОК**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Выберите метод:
"""
    
    await callback.message.edit_text(
        text=message,
        reply_markup=reply_markup
    )


@router.callback_query(F.data.in_(["parity_check", "inverse_code"]))
async def handle_simple_binary(callback: CallbackQuery, state: FSMContext):
    """Обработчик для проверки на четность и инверсного кода"""
    user_id = callback.from_user.id
    method_map = {
        "parity_check": "parity",
        "inverse_code": "inverse"
    }
    method = method_map[callback.data]
    method_names = {
        "parity": "Проверка на четность",
        "inverse": "Инверсный код"
    }
    update_user_state(user_id, current_method=method)
    await state.update_data(method=method)
    await state.set_state(ErrorDetectionStates.binary)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="error_detection"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(
        f"""🛡️ **{method_names[method].upper()}**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Введите двоичную последовательность.

💡 **Примеры:**
• `1010` - простая последовательность
• `11001100` - 8 бит
• `1111` - все единицы

Введите последовательность:""",
        reply_markup=reply_markup
    )


@router.callback_query(F.data == "constant_weight")
async def handle_constant_weight(callback: CallbackQuery, state: FSMContext):
    """Обработчик кода с постоянным весом"""
    user_id = callback.from_user.id
    update_user_state(user_id, current_method="constant_weight")
    await state.update_data(method="constant_weight")
    await state.set_state(ErrorDetectionStates.binary)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="error_detection"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(
        """⚖️ **КОД С ПОСТОЯННЫМ ВЕСОМ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

**Шаг 1 из 2:** Введите двоичную последовательность

💡 **Примеры:**
• `1010` - простая последовательность
• `11001100` - 8 бит
• `1111` - все единицы

Введите последовательность:""",
        reply_markup=reply_markup
    )


@router.callback_query(F.data == "control_number")
async def handle_control_number(callback: CallbackQuery, state: FSMContext):
    """Обработчик расчета контрольного числа"""
    user_id = callback.from_user.id
    update_user_state(user_id, current_method="control_number")
    await state.update_data(method="control_number")
    await state.set_state(ErrorDetectionStates.number)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="error_detection"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(
        """🎯 **РАСЧЕТ КОНТРОЛЬНОГО ЧИСЛА**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Введите число для расчета контрольной цифры.

💡 **Примеры:**
• `12345` - пятизначное число
• `987` - трехзначное число
• `123456789` - длинное число

Введите число:""",
        reply_markup=reply_markup
    )


@router.message(StateFilter(ErrorDetectionStates.binary))
async def get_binary(message: Message, state: FSMContext):
    """Получение двоичной последовательности и выполнение расчета"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    is_valid, msg = validate_binary(message.text)
    if not is_valid:
        error_msg = f"""
❌ **Ошибка ввода: Двоичная последовательность**

{msg}

💡 **Пример корректного ввода:**
`1010` или `11001100`

Пожалуйста, введите двоичную последовательность (только символы 0 и 1):
"""
        await message.answer(error_msg)
        return
    
    data = await state.get_data()
    method = data.get("method")
    data_bits = message.text
    
    if method == "parity":
        encoded, ones_count, parity_bit = parity_check(data_bits)
        result = format_parity_result(data_bits, ones_count, parity_bit, encoded)
        
    elif method == "inverse":
        encoded, ones_count, check_bits = inverse_code(data_bits)
        result = f"""
🔄 **ИНВЕРСНЫЙ КОД**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
**Исходные данные:** `{data_bits}`

**Количество единиц:** {ones_count}
**Четность:** {'четное' if ones_count % 2 == 0 else 'нечетное'}
**Проверочные биты:** `{check_bits}`

**Результат:** `{encoded}`
"""
    elif method == "constant_weight":
        # Сохранить данные и запросить вес
        await state.update_data(data_bits=data_bits)
        await state.set_state(ErrorDetectionStates.weight)
        
        keyboard = [
            [InlineKeyboardButton(text="🔙 Назад", callback_data="error_detection"),
             InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        await message.answer(
            """**Шаг 2 из 2:** Требуемый вес

Введите требуемый вес (количество единиц в результате).

💡 **Примеры:**
• `4` - для 4 единиц
• `5` - для 5 единиц
• `0` - для нулевого веса

Введите вес:""",
            reply_markup=reply_markup
        )
        return
    else:
        await message.answer(ERROR_MESSAGES["invalid_choice"])
        await state.clear()
        return
    
    keyboard = [
        [InlineKeyboardButton(text="🔄 Новый расчет", callback_data="error_detection")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        text=result,
        reply_markup=reply_markup
    )
    
    await state.clear()


@router.message(StateFilter(ErrorDetectionStates.weight))
async def get_weight(message: Message, state: FSMContext):
    """Получение требуемого веса для кода с постоянным весом"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    is_valid, msg = validate_number(message.text, min_val=0)
    if not is_valid:
        error_msg = f"""
❌ **Ошибка ввода: Вес**

{msg}

💡 **Пример корректного ввода:**
`4` или `5`

Пожалуйста, введите требуемый вес (целое число, не меньше 0):
"""
        await message.answer(error_msg)
        return
    
    weight = int(message.text)
    data = await state.get_data()
    data_bits = data.get("data_bits")
    
    encoded, current_weight, check_bits = constant_weight_code(data_bits, weight)
    
    result = f"""
⚖️ **КОД С ПОСТОЯННЫМ ВЕСОМ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
**Исходные данные:** `{data_bits}`

**Текущий вес:** {current_weight}
**Требуемый вес:** {weight}
**Проверочные биты:** `{check_bits}`

**Результат:** `{encoded}`
"""
    
    keyboard = [
        [InlineKeyboardButton(text="🔄 Новый расчет", callback_data="error_detection")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        text=result,
        reply_markup=reply_markup
    )
    
    await state.clear()


@router.message(StateFilter(ErrorDetectionStates.number))
async def get_number_for_control(message: Message, state: FSMContext):
    """Получение числа для расчета контрольного числа"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    is_valid, msg = validate_number(message.text)
    if not is_valid:
        error_msg = f"""
❌ **Ошибка ввода: Число**

{msg}

💡 **Пример корректного ввода:**
`12345` или `987`

Пожалуйста, введите число:
"""
        await message.answer(error_msg)
        return
    
    number = int(message.text)
    control_digit, weighted_sum, weights = calculate_control_number(number)
    
    result = f"""
🎯 **РАСЧЕТ КОНТРОЛЬНОГО ЧИСЛА**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
**Исходное число:** {number}

**Веса позиций:** {weights}
**Взвешенная сумма:** {weighted_sum}
**Контрольная цифра:** {control_digit}

**Результат:** {number}{control_digit}
"""
    
    keyboard = [
        [InlineKeyboardButton(text="🔄 Новый расчет", callback_data="error_detection")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        text=result,
        reply_markup=reply_markup
    )
    
    await state.clear()


# ========== КОДЫ ИСПРАВЛЕНИЯ ОШИБОК ==========

@router.callback_query(F.data == "error_correction")
async def handle_error_correction(callback: CallbackQuery):
    """Обработчик выбора раздела 'Коды исправления ошибок'"""
    user_id = callback.from_user.id
    
    if is_session_expired(user_id):
        await callback.answer(ERROR_MESSAGES["timeout"], show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton(text="🔧 Код Хэмминга (кодирование)", callback_data="hamming_encode")],
        [InlineKeyboardButton(text="🔍 Код Хэмминга (декодирование)", callback_data="hamming_decode")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="codes_and_errors"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    message = """
🔧 **КОДЫ ИСПРАВЛЕНИЯ ОШИБОК**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Выберите операцию:
"""
    
    await callback.message.edit_text(
        text=message,
        reply_markup=reply_markup
    )


@router.callback_query(F.data == "hamming_encode")
async def handle_hamming_encode(callback: CallbackQuery, state: FSMContext):
    """Обработчик кодирования Хэмминга"""
    user_id = callback.from_user.id
    update_user_state(user_id, current_method="hamming_encode")
    await state.update_data(method="hamming_encode")
    await state.set_state(ErrorCorrectionStates.data)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="error_correction"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(
        """🔧 **КОДИРОВАНИЕ ХЭММИНГА**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Введите двоичную последовательность для кодирования.

💡 **Примеры:**
• `1010` - 4 бита данных
• `1100` - 4 бита данных
• `1111` - 4 бита данных

Введите последовательность:""",
        reply_markup=reply_markup
    )


@router.callback_query(F.data == "hamming_decode")
async def handle_hamming_decode(callback: CallbackQuery, state: FSMContext):
    """Обработчик декодирования Хэмминга"""
    user_id = callback.from_user.id
    update_user_state(user_id, current_method="hamming_decode")
    await state.update_data(method="hamming_decode")
    await state.set_state(ErrorCorrectionStates.data)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="error_correction"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(
        """🔍 **ДЕКОДИРОВАНИЕ ХЭММИНГА**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Введите закодированную последовательность для декодирования.

💡 **Примеры:**
• `10101010` - 8 бит (4 данных + 4 контрольных)
• `11001100` - 8 бит
• `11111111` - 8 бит

Введите последовательность:""",
        reply_markup=reply_markup
    )


@router.message(StateFilter(ErrorCorrectionStates.data))
async def get_hamming_data(message: Message, state: FSMContext):
    """Получение данных и выполнение операции Хэмминга"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    is_valid, msg = validate_binary(message.text)
    if not is_valid:
        error_msg = f"""
❌ **Ошибка ввода: Двоичная последовательность**

{msg}

💡 **Пример корректного ввода:**
`1010` или `11001100`

Пожалуйста, введите двоичную последовательность (только 0 и 1):
"""
        await message.answer(error_msg)
        return
    
    data = await state.get_data()
    method = data.get("method")
    input_data = message.text
    
    if method == "hamming_encode":
        encoded, r, n = hamming_encode(input_data)
        result = format_hamming_encode_result(input_data, encoded, r, n)
        
    elif method == "hamming_decode":
        data_bits, error_pos, corrected = hamming_decode(input_data)
        result = format_hamming_decode_result(input_data, data_bits, error_pos, corrected)
        
    else:
        await message.answer(ERROR_MESSAGES["invalid_choice"])
        await state.clear()
        return
    
    keyboard = [
        [InlineKeyboardButton(text="🔄 Новый расчет", callback_data="error_correction")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        text=result,
        reply_markup=reply_markup
    )
    
    await state.clear()


# ========== КЛАССИФИКАЦИЯ И КОДИРОВАНИЕ ==========

@router.callback_query(F.data == "classification")
async def handle_classification(callback: CallbackQuery):
    """Обработчик выбора раздела 'Классификация и кодирование'"""
    user_id = callback.from_user.id
    
    if is_session_expired(user_id):
        await callback.answer(ERROR_MESSAGES["timeout"], show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton(text="📊 Расчет избыточности", callback_data="redundancy")],
        [InlineKeyboardButton(text="📚 Методы классификации", callback_data="classification_methods")],
        [InlineKeyboardButton(text="🔢 Методы кодирования", callback_data="coding_methods")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="codes_and_errors"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    message = """
📁 **КЛАССИФИКАЦИЯ И КОДИРОВАНИЕ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Выберите раздел:
"""
    
    await callback.message.edit_text(
        text=message,
        reply_markup=reply_markup
    )


@router.callback_query(F.data == "redundancy")
async def handle_redundancy(callback: CallbackQuery, state: FSMContext):
    """Обработчик расчета избыточности"""
    user_id = callback.from_user.id
    update_user_state(user_id, current_method="redundancy")
    await state.set_state(ClassificationStates.total)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="classification"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(
        """📊 **РАСЧЕТ ИЗБЫТОЧНОСТИ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

**Шаг 1 из 2:** Общее количество комбинаций

Введите общее количество возможных комбинаций.

💡 **Примеры:**
• `256` - для 8-битного кода
• `1024` - для 10-битного кода
• `100` - произвольное значение

Введите значение:""",
        reply_markup=reply_markup
    )


@router.callback_query(F.data == "classification_methods")
async def handle_classification_methods(callback: CallbackQuery):
    """Обработчик информации о методах классификации"""
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="classification")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    message = """
📚 **МЕТОДЫ КЛАССИФИКАЦИИ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

**1. Иерархический метод:**
   • Древовидная структура классификации
   • Каждый объект принадлежит только одному классу
   • Классы образуют иерархию (родитель-потомок)
   • Пример: Животные → Млекопитающие → Собаки

**2. Фасетный метод:**
   • Независимые признаки (фасеты)
   • Объект может иметь несколько значений по каждому признаку
   • Гибкая система классификации
   • Пример: Цвет (красный, синий) + Размер (малый, большой)
"""
    
    await callback.message.edit_text(
        text=message,
        reply_markup=reply_markup
    )


@router.callback_query(F.data == "coding_methods")
async def handle_coding_methods(callback: CallbackQuery):
    """Обработчик информации о методах кодирования"""
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="classification")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    message = """
🔢 **МЕТОДЫ КОДИРОВАНИЯ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

**1. Порядковый метод:**
   • Последовательная нумерация объектов
   • Простой и универсальный
   • Пример: 1, 2, 3, 4, 5...

**2. Серийно-порядковый метод:**
   • Выделение серий для групп объектов
   • Внутри серии - порядковая нумерация
   • Пример: 10-19 (серия 1), 20-29 (серия 2)

**3. Последовательный метод:**
   • Кодирование иерархии уровней
   • Каждый уровень добавляет разряд кода
   • Пример: 1 → 11 → 111 (уровни иерархии)

**4. Параллельный метод:**
   • Независимые фасеты кодируются отдельно
   • Комбинация кодов фасетов дает полный код
   • Пример: Цвет (1-9) + Размер (1-9) = 19
"""
    
    await callback.message.edit_text(
        text=message,
        reply_markup=reply_markup
    )


@router.message(StateFilter(ClassificationStates.total))
async def get_total_combinations(message: Message, state: FSMContext):
    """Получение общего количества комбинаций"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    is_valid, msg = validate_number(message.text, min_val=1)
    if not is_valid:
        error_msg = f"""
❌ **Ошибка ввода: Общее количество комбинаций**

{msg}

💡 **Пример корректного ввода:**
`256` или `1024`

Пожалуйста, введите общее количество комбинаций (целое число, не меньше 1):
"""
        await message.answer(error_msg)
        return
    
    total = int(message.text)
    await state.update_data(total=total)
    await state.set_state(ClassificationStates.used)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="classification"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        f"""**Шаг 2 из 2:** Используемые комбинации

Введите количество используемых комбинаций.

💡 **Важно:** Должно быть не больше {total} (общее количество)

💡 **Примеры:**
• `100` - если используется 100 из {total}
• `50` - если используется 50 из {total}
• `1` - минимум

Введите значение:""",
        reply_markup=reply_markup
    )


@router.message(StateFilter(ClassificationStates.used))
async def get_used_combinations(message: Message, state: FSMContext):
    """Получение количества используемых комбинаций и расчет"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    data = await state.get_data()
    total = data.get("total")
    
    is_valid, msg = validate_number(message.text, min_val=1, max_val=total)
    if not is_valid:
        error_msg = f"""
❌ **Ошибка ввода: Используемые комбинации**

{msg}

💡 **Ограничения:**
• Минимум: 1
• Максимум: {total} (общее количество комбинаций)

💡 **Пример корректного ввода:**
`100` или `50`

Пожалуйста, введите количество используемых комбинаций:
"""
        await message.answer(error_msg)
        return
    
    used = int(message.text)
    redundancy, unused = calculate_redundancy(total, used)
    
    result = f"""
📊 **РАСЧЕТ ИЗБЫТОЧНОСТИ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
**Общее количество комбинаций:** {total}
**Используемых комбинаций:** {used}
**Неиспользуемых комбинаций:** {unused}

**Избыточность:** {redundancy:.2f}%
"""
    
    keyboard = [
        [InlineKeyboardButton(text="🔄 Новый расчет", callback_data="redundancy")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        text=result,
        reply_markup=reply_markup
    )
    
    await state.clear()

