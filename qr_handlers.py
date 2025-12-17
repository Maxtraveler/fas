"""Обработчики модуля QR-кодирования"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from handlers.states import QRStates
from utils.state_manager import update_user_state, is_session_expired
from utils.validators import validate_digits, validate_binary
from utils.formatters import format_qr_numeric_result, format_qr_alphanumeric_result
from calculators.qr_encoder import numeric_qr_encode, alphanumeric_qr_encode, numeric_qr_encode_with_mask
from config import ERROR_MESSAGES

router = Router()


@router.callback_query(F.data == "qr_coding")
async def handle_qr_coding(callback: CallbackQuery):
    """Обработчик выбора раздела 'QR-кодирование'"""
    user_id = callback.from_user.id
    
    if is_session_expired(user_id):
        await callback.answer(ERROR_MESSAGES["timeout"], show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton(text="🔢 Цифровое кодирование", callback_data="qr_numeric")],
        [InlineKeyboardButton(text="🔤 Буквенно-цифровое кодирование", callback_data="qr_alphanumeric")],
        [InlineKeyboardButton(text="🎭 Цифровое с маской", callback_data="qr_numeric_mask")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    message = """
🔲 **QR-КОДИРОВАНИЕ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Выберите тип кодирования:
"""
    
    await callback.message.edit_text(
        text=message,
        reply_markup=reply_markup
    )


@router.callback_query(F.data == "qr_numeric")
async def handle_qr_numeric(callback: CallbackQuery, state: FSMContext):
    """Обработчик цифрового QR-кодирования"""
    user_id = callback.from_user.id
    update_user_state(user_id, current_method="qr_numeric")
    await state.update_data(method="qr_numeric")
    await state.set_state(QRStates.input)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="qr_coding"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(
        """🔢 **ЦИФРОВОЕ QR-КОДИРОВАНИЕ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Введите цифры для кодирования.

💡 **Примеры:**
• `123456789` - длинное число
• `42` - короткое число
• `100` - три цифры

Введите значение:""",
        reply_markup=reply_markup
    )


@router.callback_query(F.data == "qr_numeric_mask")
async def handle_qr_numeric_mask(callback: CallbackQuery, state: FSMContext):
    """Обработчик цифрового QR-кодирования с маской"""
    user_id = callback.from_user.id
    update_user_state(user_id, current_method="qr_numeric_mask")
    await state.update_data(method="qr_numeric_mask")
    await state.set_state(QRStates.input)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="qr_coding"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(
        """🎭 **ЦИФРОВОЕ QR-КОДИРОВАНИЕ С МАСКОЙ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

**Шаг 1 из 2:** Введите число для кодирования

💡 **Примеры:**
• `123456789`
• `42`
• `100`

Введите число:""",
        reply_markup=reply_markup
    )


@router.callback_query(F.data == "qr_alphanumeric")
async def handle_qr_alphanumeric(callback: CallbackQuery, state: FSMContext):
    """Обработчик буквенно-цифрового QR-кодирования"""
    user_id = callback.from_user.id
    update_user_state(user_id, current_method="qr_alphanumeric")
    await state.update_data(method="qr_alphanumeric")
    await state.set_state(QRStates.input)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="qr_coding"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(
        """🔤 **БУКВЕННО-ЦИФРОВОЕ QR-КОДИРОВАНИЕ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Введите текст для кодирования.

💡 **Допустимые символы:**
• Латинские буквы: A-Z, a-z
• Цифры: 0-9
• Пробел
• Символы: $%*+-./:

💡 **Примеры:**
• `HELLO WORLD`
• `ABC123`
• `TEST $100`

Введите текст:""",
        reply_markup=reply_markup
    )


@router.message(StateFilter(QRStates.input))
async def get_qr_input(message: Message, state: FSMContext):
    """Получение входных данных и выполнение QR-кодирования"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    data = await state.get_data()
    method = data.get("method")
    input_text = message.text
    
    if method == "qr_numeric":
        is_valid, msg = validate_digits(input_text)
        if not is_valid:
            error_msg = f"""
❌ **Ошибка ввода: Цифры**

{msg}

💡 **Пример корректного ввода:**
`123456789` или `42`

Пожалуйста, введите только цифры:
"""
            await message.answer(error_msg)
            return
        
        encoded_bits, steps = numeric_qr_encode(input_text)
        result = format_qr_numeric_result(input_text, encoded_bits, steps)
        
    elif method == "qr_numeric_mask":
        is_valid, msg = validate_digits(input_text)
        if not is_valid:
            error_msg = f"""
❌ **Ошибка ввода: Число**

{msg}

💡 **Пример корректного ввода:**
`123456789` или `42`

Пожалуйста, введите число:
"""
            await message.answer(error_msg)
            return
        
        # Сохранить число и запросить маску
        await state.update_data(digits=input_text)
        await state.set_state(QRStates.mask)
        
        keyboard = [
            [InlineKeyboardButton(text="🔙 Назад", callback_data="qr_coding"),
             InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        await message.answer(
            """**Шаг 2 из 2:** Введите маску

Введите двоичную последовательность (маску) для наложения.

💡 **Примеры:**
• `1010` - простая маска
• `11110000` - маска из 8 бит
• `1` - единичная маска

Введите маску:""",
            reply_markup=reply_markup
        )
        return
        
    elif method == "qr_alphanumeric":
        # Проверка на допустимые символы
        allowed_chars = set('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:')
        if not all(c.upper() in allowed_chars for c in input_text):
            error_msg = """
❌ **Ошибка ввода: Текст для QR-кода**

Текст содержит недопустимые символы.

💡 **Допустимые символы:**
• Латинские буквы: A-Z, a-z
• Цифры: 0-9
• Пробел
• Символы: $%*+-./:

💡 **Пример корректного ввода:**
`HELLO WORLD` или `ABC123`

Пожалуйста, попробуйте снова:
"""
            await message.answer(error_msg)
            return
        
        encoded_bits, steps = alphanumeric_qr_encode(input_text)
        result = format_qr_alphanumeric_result(input_text, encoded_bits, steps)
        
    else:
        await message.answer(ERROR_MESSAGES["invalid_choice"])
        await state.clear()
        return
    
    keyboard = [
        [InlineKeyboardButton(text="🔄 Новый расчет", callback_data="qr_coding")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        text=result,
        reply_markup=reply_markup
    )
    
    await state.clear()


@router.message(StateFilter(QRStates.mask))
async def get_qr_mask(message: Message, state: FSMContext):
    """Получение маски и выполнение QR-кодирования с маской"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    is_valid, msg = validate_binary(message.text)
    if not is_valid:
        error_msg = f"""
❌ **Ошибка ввода: Маска**

{msg}

💡 **Пример корректного ввода:**
`1010` или `11110000`

Пожалуйста, введите двоичную последовательность (только 0 и 1):
"""
        await message.answer(error_msg)
        return
    
    mask = message.text
    data = await state.get_data()
    digits = data.get("digits")
    
    # Выполнить кодирование с маской
    encoded_bits, masked_bits, steps = numeric_qr_encode_with_mask(digits, mask)
    
    steps_text = "\n".join(steps)
    
    result = f"""
🎭 **ЦИФРОВОЕ QR-КОДИРОВАНИЕ С МАСКОЙ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
**Исходные данные:**
• Число: {digits}
• Маска: `{mask}`

{steps_text}

**Итоговый результат:**
• Двоичный: `{masked_bits}`
• Десятичный: `{int(masked_bits, 2)}`
"""
    
    keyboard = [
        [InlineKeyboardButton(text="🔄 Новый расчет", callback_data="qr_numeric_mask")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        text=result,
        reply_markup=reply_markup
    )
    
    await state.clear()
