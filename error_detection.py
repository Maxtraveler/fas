"""Обработчики модуля кодов обнаружения ошибок"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from handlers.states import ErrorDetectionStates
from utils.state_manager import update_user_state, is_session_expired
from utils.validators import validate_binary, validate_number
from utils.formatters import format_parity_result
from calculators.checksum_calculator import parity_check, constant_weight_code, inverse_code, calculate_control_number
from config import ERROR_MESSAGES

router = Router()


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
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    message = """
🛡️ **КОДЫ ОБНАРУЖЕНИЯ ОШИБОК**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

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

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

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

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

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

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

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

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
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

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
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

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
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
