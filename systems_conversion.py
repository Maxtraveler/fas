"""Обработчики модуля систем счисления и кодировок"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from handlers.states import SystemsConversionStates, NumberCodingStates, SoundCodingStates, QRStates, BarcodeStates
from utils.state_manager import update_user_state, is_session_expired
from utils.validators import validate_binary, validate_number, validate_float, validate_digits
from utils.formatters import format_number_code_result, format_audio_result, format_qr_numeric_result, format_ean13_result
from calculators.systems_converter import convert_base
from calculators.koi8_encoder import koi8_encode, koi8_decode, block_parity_encode
from calculators.number_converter import reverse_code, additional_code
from calculators.sound_calculator import (
    calculate_audio_size, calculate_frequency, calculate_depth,
    calculate_duration, calculate_channels
)
from calculators.qr_encoder import numeric_qr_encode, numeric_qr_encode_with_mask
from calculators.barcode_calculator import ean13_checksum
from config import ERROR_MESSAGES

router = Router()


@router.callback_query(F.data == "systems_conversion")
async def handle_systems_conversion(callback: CallbackQuery):
    """Обработчик выбора раздела 'Системы счисления'"""
    user_id = callback.from_user.id
    
    if is_session_expired(user_id):
        await callback.answer(ERROR_MESSAGES["timeout"], show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton(text="🔄 Перевод систем счисления", callback_data="base_conversion")],
        [InlineKeyboardButton(text="🔄 Обратный код", callback_data="number_reverse")],
        [InlineKeyboardButton(text="➕ Дополнительный код", callback_data="number_additional")],
        [InlineKeyboardButton(text="🔊 Кодирование звука", callback_data="sound_coding")],
        [InlineKeyboardButton(text="🔲 QR-кодирование", callback_data="qr_coding")],
        [InlineKeyboardButton(text="🔤 Кодировка КОИ-8", callback_data="koi8_coding")],
        [InlineKeyboardButton(text="📊 Штрих-кодирование", callback_data="barcode")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    message = """
🔄 **СИСТЕМЫ СЧИСЛЕНИЯ И КОДИРОВКА**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Выберите операцию:
"""
    
    await callback.message.edit_text(
        text=message,
        reply_markup=reply_markup
    )


@router.callback_query(F.data.in_(["number_reverse", "number_additional"]))
async def handle_integer_code(callback: CallbackQuery, state: FSMContext):
    """Обработчик для обратного и дополнительного кода"""
    user_id = callback.from_user.id
    method_map = {
        "number_reverse": "reverse",
        "number_additional": "additional"
    }
    method = method_map[callback.data]
    update_user_state(user_id, current_method=method)
    await state.update_data(method=method)
    await state.set_state(NumberCodingStates.number)
    
    method_names = {
        "reverse": "Обратный код",
        "additional": "Дополнительный код"
    }
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="systems_conversion"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(
        f"""🔢 **{method_names[method].upper()}**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Введите число для кодирования.

💡 **Примеры:**
• `10` - положительное число
• `-5` - отрицательное число
• `127` - большое число

Введите число:""",
        reply_markup=reply_markup
    )


@router.message(StateFilter(NumberCodingStates.number))
async def get_number_for_coding(message: Message, state: FSMContext):
    """Получение числа и выполнение кодирования"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    data = await state.get_data()
    method = data.get("method")
    
    # Проверяем, что это кодирование чисел, а не другие операции
    if method not in ["reverse", "additional"]:
        return
    
    is_valid, msg = validate_number(message.text)
    if not is_valid:
        error_msg = f"""
❌ **Ошибка ввода: Целое число**

{msg}

💡 **Пример корректного ввода:**
`10` или `-5`

Пожалуйста, введите целое число:
"""
        await message.answer(error_msg)
        return
    
    number = int(message.text)
    bits = 8  # По умолчанию 8 бит
    
    if method == "reverse":
        code = reverse_code(number, bits)
        code_type = "reverse"
    elif method == "additional":
        code = additional_code(number, bits)
        code_type = "additional"
    else:
        await message.answer(ERROR_MESSAGES["invalid_choice"])
        await state.clear()
        return
    
    formatted = format_number_code_result(number, code, code_type)
    
    keyboard = [
        [InlineKeyboardButton(text="🔄 Новый расчет", callback_data="systems_conversion")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        text=formatted,
        reply_markup=reply_markup
    )
    
    await state.clear()


@router.callback_query(F.data == "base_conversion")
async def handle_base_conversion(callback: CallbackQuery, state: FSMContext):
    """Обработчик перевода систем счисления"""
    user_id = callback.from_user.id
    update_user_state(user_id, current_method="base_conversion")
    await state.set_state(SystemsConversionStates.number)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="systems_conversion"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(
        """🔄 **ПЕРЕВОД СИСТЕМ СЧИСЛЕНИЯ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

**Шаг 1 из 3:** Введите число

Введите число в исходной системе счисления.

💡 **Примеры:**
• `1010` - двоичное число
• `FF` - шестнадцатеричное
• `123` - десятичное

Введите число:""",
        reply_markup=reply_markup
    )


@router.callback_query(F.data == "koi8_coding")
async def handle_koi8_coding(callback: CallbackQuery):
    """Обработчик выбора раздела 'Кодировка КОИ-8'"""
    user_id = callback.from_user.id
    
    if is_session_expired(user_id):
        await callback.answer(ERROR_MESSAGES["timeout"], show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton(text="🔤 Кодировка КОИ-8 (текст → двоичный)", callback_data="koi8_encode")],
        [InlineKeyboardButton(text="📝 Декодировка КОИ-8 (двоичный → текст)", callback_data="koi8_decode")],
        [InlineKeyboardButton(text="📦 Блочное кодирование с контролем четности", callback_data="block_parity")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="systems_conversion"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    message = """
🔤 **КОДИРОВКА КОИ-8**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Выберите операцию:
"""
    
    await callback.message.edit_text(
        text=message,
        reply_markup=reply_markup
    )


@router.callback_query(F.data == "koi8_encode")
async def handle_koi8_encode(callback: CallbackQuery, state: FSMContext):
    """Обработчик кодирования КОИ-8"""
    user_id = callback.from_user.id
    update_user_state(user_id, current_method="koi8_encode")
    await state.set_state(SystemsConversionStates.text)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="koi8_coding"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(
        """🔤 **КОДИРОВАНИЕ КОИ-8**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Введите текст для кодирования в КОИ-8.

💡 **Примеры:**
• `Привет` - русский текст
• `АБВ` - русские буквы
• `Hello` - латинский текст (также поддерживается)

Введите текст:""",
        reply_markup=reply_markup
    )


@router.callback_query(F.data == "koi8_decode")
async def handle_koi8_decode(callback: CallbackQuery, state: FSMContext):
    """Обработчик декодирования КОИ-8"""
    user_id = callback.from_user.id
    update_user_state(user_id, current_method="koi8_decode")
    await state.set_state(SystemsConversionStates.binary)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="koi8_coding"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(
        """📝 **ДЕКОДИРОВАНИЕ КОИ-8**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Введите двоичную последовательность для декодирования.

💡 **Важно:** Длина должна быть кратна 8 (каждый символ = 8 бит)

💡 **Примеры:**
• `1100000111000010` - 16 бит (2 символа)
• `11000001` - 8 бит (1 символ)
• `110000011100001011000011` - 24 бита (3 символа)

Введите последовательность:""",
        reply_markup=reply_markup
    )


@router.callback_query(F.data == "block_parity")
async def handle_block_parity(callback: CallbackQuery, state: FSMContext):
    """Обработчик блочного кодирования"""
    user_id = callback.from_user.id
    update_user_state(user_id, current_method="block_parity")
    await state.set_state(SystemsConversionStates.binary)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="koi8_coding"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(
        """📦 **БЛОЧНОЕ КОДИРОВАНИЕ С КОНТРОЛЕМ ЧЕТНОСТИ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

**Шаг 1 из 2:** Введите двоичную последовательность

Введите двоичную последовательность для разбиения на блоки.

💡 **Примеры:**
• `10101100` - 8 бит
• `110011001100` - 12 бит
• `1010` - 4 бита

Введите последовательность:""",
        reply_markup=reply_markup
    )


@router.message(StateFilter(SystemsConversionStates.number))
async def get_number_for_conversion(message: Message, state: FSMContext):
    """Получение числа для преобразования"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    number = message.text.strip()
    await state.update_data(number=number)
    await state.set_state(SystemsConversionStates.from_base)
    
    await message.answer(
        "Введите исходную систему счисления (2-36):"
    )


@router.message(StateFilter(SystemsConversionStates.from_base))
async def get_from_base(message: Message, state: FSMContext):
    """Получение исходной системы счисления"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    is_valid, msg = validate_number(message.text, min_val=2, max_val=36)
    if not is_valid:
        error_msg = f"""
❌ **Ошибка ввода: Исходная система счисления**

{msg}

💡 **Допустимый диапазон:** 2-36

💡 **Примеры:**
• `2` - двоичная
• `8` - восьмеричная
• `16` - шестнадцатеричная
• `10` - десятичная

Пожалуйста, введите систему счисления (2-36):
"""
        await message.answer(error_msg)
        return
    
    from_base = int(message.text)
    await state.update_data(from_base=from_base)
    await state.set_state(SystemsConversionStates.to_base)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="systems_conversion"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        f"""**Шаг 2 из 3:** Целевая система счисления

Введите целевую систему счисления (куда преобразовать).

💡 **Допустимый диапазон:** 2-36

💡 **Примеры:**
• `2` - в двоичную
• `8` - в восьмеричную
• `16` - в шестнадцатеричную
• `10` - в десятичную

Введите систему счисления:""",
        reply_markup=reply_markup
    )


@router.message(StateFilter(SystemsConversionStates.to_base))
async def get_to_base(message: Message, state: FSMContext):
    """Получение целевой системы счисления и выполнение преобразования"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    is_valid, msg = validate_number(message.text, min_val=2, max_val=36)
    if not is_valid:
        error_msg = f"""
❌ **Ошибка ввода: Целевая система счисления**

{msg}

💡 **Допустимый диапазон:** 2-36

💡 **Примеры:**
• `2` - двоичная
• `8` - восьмеричная
• `16` - шестнадцатеричная
• `10` - десятичная

Пожалуйста, введите систему счисления (2-36):
"""
        await message.answer(error_msg)
        return
    
    to_base = int(message.text)
    data = await state.get_data()
    number = data.get("number")
    from_base = data.get("from_base")
    
    try:
        result, steps = convert_base(number, from_base, to_base)
        steps_text = "\n".join(steps)
        
        formatted_result = f"""
🔄 **ПЕРЕВОД СИСТЕМ СЧИСЛЕНИЯ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
**Исходное число:** {number} ({from_base}-я система)

{steps_text}

**Результат:** `{result}` ({to_base}-я система)
"""
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при преобразовании: {str(e)}")
        await state.clear()
        return
    
    keyboard = [
        [InlineKeyboardButton(text="🔄 Новый расчет", callback_data="base_conversion")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        text=formatted_result,
        reply_markup=reply_markup
    )
    
    await state.clear()


@router.message(StateFilter(SystemsConversionStates.text))
async def get_text_for_koi8(message: Message, state: FSMContext):
    """Получение текста для кодирования КОИ-8"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    text = message.text
    encoded_binary, steps = koi8_encode(text)
    
    steps_text = "\n".join([f"• {step}" for step in steps])
    
    result = f"""
🔤 **КОДИРОВАНИЕ КОИ-8**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
**Исходный текст:** {text}

**Шаги кодирования:**
{steps_text}

**Результат:** `{encoded_binary}`
"""
    
    keyboard = [
        [InlineKeyboardButton(text="🔄 Новый расчет", callback_data="koi8_coding")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        text=result,
        reply_markup=reply_markup
    )
    
    await state.clear()


@router.message(StateFilter(SystemsConversionStates.binary))
async def get_binary_for_operations(message: Message, state: FSMContext):
    """Получение двоичной последовательности для различных операций"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    # Определить метод из состояния пользователя
    from utils.state_manager import get_user_state
    user_state = get_user_state(user_id)
    method = user_state.get("current_method")
    
    is_valid, msg = validate_binary(message.text)
    if not is_valid:
        await message.answer(f"❌ {msg}\n\nВведите двоичную последовательность:")
        return
    
    binary_string = message.text
    
    if method == "koi8_decode":
        if len(binary_string) % 8 != 0:
            await message.answer(
                "❌ Длина двоичной последовательности должна быть кратна 8.\n"
                "Введите двоичную последовательность:"
            )
            return
        
        decoded_text, steps = koi8_decode(binary_string)
        
        steps_text = "\n".join([f"• {step}" for step in steps])
        
        result = f"""
📝 **ДЕКОДИРОВАНИЕ КОИ-8**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
**Исходная последовательность:** `{binary_string}`

**Шаги декодирования:**
{steps_text}

**Результат:** {decoded_text}
"""
        
        keyboard = [
            [InlineKeyboardButton(text="🔄 Новый расчет", callback_data="koi8_decode")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        await message.answer(
            text=result,
            reply_markup=reply_markup
        )
        
        await state.clear()
        
    elif method == "block_parity":
        await state.update_data(binary=binary_string)
        await state.set_state(SystemsConversionStates.block_size)
        keyboard = [
            [InlineKeyboardButton(text="🔙 Назад", callback_data="systems_conversion"),
             InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        await message.answer(
            """**Шаг 2 из 2:** Размер блока

Введите размер блока для разбиения последовательности.

💡 **Примеры:**
• `8` - стандартный размер (1 байт)
• `4` - для 4-битных блоков
• `16` - для 16-битных блоков

💡 **По умолчанию:** 8 (можно оставить пустым)

Введите размер блока:""",
            reply_markup=reply_markup
        )


@router.message(StateFilter(SystemsConversionStates.block_size))
async def get_block_size(message: Message, state: FSMContext):
    """Получение размера блока и выполнение блочного кодирования"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    if message.text.strip() == "":
        block_size = 8
    else:
        is_valid, msg = validate_number(message.text, min_val=1)
        if not is_valid:
            error_msg = f"""
❌ **Ошибка ввода: Размер блока**

{msg}

💡 **Пример корректного ввода:**
`8` или `4`

Пожалуйста, введите размер блока (целое число, не меньше 1):
"""
            await message.answer(error_msg)
            return
        block_size = int(message.text)
    
    data = await state.get_data()
    binary_string = data.get("binary")
    
    results = block_parity_encode(binary_string, block_size)
    
    blocks_text = []
    for i, (block, ones_count, parity_bit, encoded_block) in enumerate(results, 1):
        blocks_text.append(
            f"**Блок {i}:**\n"
            f"  Исходный: `{block}`\n"
            f"  Количество единиц: {ones_count}\n"
            f"  Бит четности: `{parity_bit}`\n"
            f"  Результат: `{encoded_block}`"
        )
    
    result = f"""
📦 **БЛОЧНОЕ КОДИРОВАНИЕ С КОНТРОЛЕМ ЧЕТНОСТИ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
**Исходная последовательность:** `{binary_string}`
**Размер блока:** {block_size}

{chr(10).join(blocks_text)}
"""
    
    keyboard = [
        [InlineKeyboardButton(text="🔄 Новый расчет", callback_data="block_parity")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        text=result,
        reply_markup=reply_markup
    )
    
    await state.clear()


# ========== КОДИРОВАНИЕ ЗВУКА ==========

@router.callback_query(F.data == "sound_coding")
async def handle_sound_coding(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора раздела 'Кодирование звука'"""
    user_id = callback.from_user.id
    
    if is_session_expired(user_id):
        await callback.answer(ERROR_MESSAGES["timeout"], show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton(text="[V] 📁 Объём файла", callback_data="calc_volume")],
        [InlineKeyboardButton(text="[F] 🔊 Частота дискретизации", callback_data="calc_frequency")],
        [InlineKeyboardButton(text="[B] 💾 Глубина кодирования", callback_data="calc_depth")],
        [InlineKeyboardButton(text="[T] ⏱️ Длительность", callback_data="calc_duration")],
        [InlineKeyboardButton(text="[C] 🎧 Каналы", callback_data="calc_channels")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="systems_conversion"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    message = """
🔊 **КОДИРОВАНИЕ ЗВУКА**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

**📐 ОСНОВНАЯ ФОРМУЛА:**

`V = F * (B/8) * T * C`

Где:
• V - объём (байты)
• F - частота дискретизации (Гц)
• B - глубина кодирования (биты)
• T - время (секунды)
• C - количество каналов (1-моно, 2-стерео)

**🔊 ЧТО ВЫЧИСЛЯЕМ?**

Выберите параметр для вычисления:
"""
    
    await callback.message.edit_text(
        text=message,
        reply_markup=reply_markup
    )


# Обработчики выбора параметра для вычисления
@router.callback_query(F.data.startswith("calc_"))
async def handle_calc_param(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора параметра для вычисления"""
    user_id = callback.from_user.id
    
    if is_session_expired(user_id):
        await callback.answer(ERROR_MESSAGES["timeout"], show_alert=True)
        return
    
    param_map = {
        "calc_volume": ("volume", "📁 Объём файла (V)", "V = F * (B/8) * T * C"),
        "calc_frequency": ("frequency", "🔊 Частота дискретизации (F)", "F = V / [(B/8) * T * C]"),
        "calc_depth": ("depth", "💾 Глубина кодирования (B)", "B = (V * 8) / (F * T * C)"),
        "calc_duration": ("duration", "⏱️ Длительность (T)", "T = V / [F * (B/8) * C]"),
        "calc_channels": ("channels", "🎧 Каналы (C)", "C = V / [F * (B/8) * T]")
    }
    
    param_key, param_name, formula = param_map[callback.data]
    update_user_state(user_id, current_method=param_key)
    
    # Инициализация параметров
    await state.update_data(
        target_param=param_key,
        formula=formula,
        volume=None,
        frequency=None,
        depth=None,
        duration=None,
        channels=None
    )
    
    # Определить порядок ввода параметров
    param_order = []
    if param_key != "volume":
        param_order.append(("volume", "📁 Объём (V)", "байты", SoundCodingStates.input_volume))
    if param_key != "frequency":
        param_order.append(("frequency", "🔊 Частота (F)", "Гц", SoundCodingStates.input_frequency))
    if param_key != "depth":
        param_order.append(("depth", "💾 Глубина (B)", "биты", SoundCodingStates.input_depth))
    if param_key != "duration":
        param_order.append(("duration", "⏱️ Длительность (T)", "секунды", SoundCodingStates.input_duration))
    if param_key != "channels":
        param_order.append(("channels", "🎧 Каналы (C)", "1 или 2", SoundCodingStates.input_channels))
    
    await state.update_data(param_order=param_order, current_param_idx=0)
    
    # Начать ввод первого параметра
    if param_order:
        first_param = param_order[0]
        await state.set_state(first_param[3])
        
        keyboard = [
            [InlineKeyboardButton(text="🔙 Назад", callback_data="sound_coding"),
             InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        message = f"""
🔊 **ВЫЧИСЛЯЕМ: {param_name.upper()}**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

**Формула:** `{formula}`

**Шаг 1 из {len(param_order)}:** {first_param[1]}

Введите значение {first_param[1]} ({first_param[2]}).

💡 Введите положительное число (не 0)

Введите значение:
"""
        
        await callback.message.edit_text(
            text=message,
            reply_markup=reply_markup
        )


# Универсальный обработчик для ввода параметров звука
async def handle_audio_param_input(message: Message, state: FSMContext, param_key: str, param_name: str, param_unit: str):
    """Универсальный обработчик ввода параметра звука"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    # Валидация ввода
    try:
        value = float(message.text.strip())
        if value < 0:
            await message.answer(f"❌ Ошибка: значение не может быть отрицательным. Введите положительное число:")
            return
        if value == 0:
            await message.answer(f"❌ Ошибка: значение не может быть равно 0. Пожалуйста, введите положительное число:")
            return
    except ValueError:
        await message.answer(f"❌ Ошибка: введите число:")
        return
    
    # Сохранить значение параметра (включая 0)
    data = await state.get_data()
    await state.update_data(**{param_key: value})
    
    # Получить порядок параметров
    param_order = data.get("param_order", [])
    current_idx = data.get("current_param_idx", 0)
    
    # Перейти к следующему параметру
    current_idx += 1
    
    if current_idx < len(param_order):
        # Есть еще параметры для ввода
        next_param = param_order[current_idx]
        await state.update_data(current_param_idx=current_idx)
        await state.set_state(next_param[3])
        
        keyboard = [
            [InlineKeyboardButton(text="🔙 Назад", callback_data="sound_coding"),
             InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        await message.answer(
            f"✅ {param_name}: {value}\n\n"
            f"**Шаг {current_idx + 1} из {len(param_order)}:** {next_param[1]}\n\n"
            f"Введите значение {next_param[1]} ({next_param[2]}).\n\n"
            f"💡 Введите положительное число (не 0)",
            reply_markup=reply_markup
        )
    else:
        # Все параметры введены, выполнить расчет
        await message.answer(f"✅ {param_name}: {value}\n\nВыполняю расчет...")
        await calculate_audio_result(message, state)


@router.message(StateFilter(SoundCodingStates.input_volume))
async def get_input_volume(message: Message, state: FSMContext):
    """Ввод объёма"""
    await handle_audio_param_input(message, state, "volume", "📁 Объём (V)", "байты")


@router.message(StateFilter(SoundCodingStates.input_frequency))
async def get_input_frequency(message: Message, state: FSMContext):
    """Ввод частоты"""
    await handle_audio_param_input(message, state, "frequency", "🔊 Частота (F)", "Гц")


@router.message(StateFilter(SoundCodingStates.input_depth))
async def get_input_depth(message: Message, state: FSMContext):
    """Ввод глубины"""
    await handle_audio_param_input(message, state, "depth", "💾 Глубина (B)", "биты")


@router.message(StateFilter(SoundCodingStates.input_duration))
async def get_input_duration(message: Message, state: FSMContext):
    """Ввод длительности"""
    await handle_audio_param_input(message, state, "duration", "⏱️ Длительность (T)", "секунды")


@router.message(StateFilter(SoundCodingStates.input_channels))
async def get_input_channels(message: Message, state: FSMContext):
    """Ввод каналов"""
    await handle_audio_param_input(message, state, "channels", "🎧 Каналы (C)", "1 или 2")


async def calculate_audio_result(message: Message, state: FSMContext):
    """Выполнение расчета после ввода всех параметров"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    data = await state.get_data()
    target_param = data.get("target_param")
    
    # Получить все параметры
    params = {
        'volume': data.get('volume'),
        'frequency': data.get('frequency'),
        'depth': data.get('depth'),
        'duration': data.get('duration'),
        'channels': data.get('channels')
    }
    
    # Проверить, что все необходимые параметры введены
    required = {'volume', 'frequency', 'depth', 'duration', 'channels'} - {target_param}
    missing = [k for k in required if params[k] is None]
    
    if missing:
        missing_names = {
            'volume': 'V (объём)',
            'frequency': 'F (частота)',
            'depth': 'B (глубина)',
            'duration': 'T (длительность)',
            'channels': 'C (каналы)'
        }
        missing_list = ', '.join([missing_names[m] for m in missing])
        await message.answer(
            f"❌ **Не хватает параметров:** {missing_list}\n\n"
            f"Пожалуйста, введите все необходимые параметры."
        )
        return
    
    # Выполнение расчета
    try:
        if target_param == "volume":
            result_value = calculate_audio_size(
                params['frequency'], params['depth'],
                params['duration'], params['channels']
            )
            total_bytes, kb, mb = result_value
            result_text = f"""
📁 **РАСЧЕТ ОБЪЁМА ФАЙЛА**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
**Входные данные:**
• Частота: {params['frequency']} Гц
• Глубина: {params['depth']} бит
• Длительность: {params['duration']} сек
• Каналы: {params['channels']} ({'стерео' if params['channels'] == 2 else 'моно'})

**Расчет:**
V = {params['frequency']} * ({params['depth']}/8) * {params['duration']} * {params['channels']}
V = {params['frequency']} * {params['depth']/8} * {params['duration']} * {params['channels']}
V = {total_bytes} байт

**Результат:**
• {total_bytes} байт
• {kb:.2f} КБ
• {mb:.2f} МБ
"""
        elif target_param == "frequency":
            result_value = calculate_frequency(
                params['volume'], params['depth'],
                params['duration'], params['channels']
            )
            result_text = f"""
🔊 **РАСЧЕТ ЧАСТОТЫ ДИСКРЕТИЗАЦИИ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
**Входные данные:**
• Объём: {params['volume']} байт
• Глубина: {params['depth']} бит
• Длительность: {params['duration']} сек
• Каналы: {params['channels']} ({'стерео' if params['channels'] == 2 else 'моно'})

**Расчет:**
F = {params['volume']} / [({params['depth']}/8) * {params['duration']} * {params['channels']}]
F = {params['volume']} / [{params['depth']/8} * {params['duration']} * {params['channels']}]
F = {result_value:.2f} Гц

**Результат:** {result_value:.2f} Гц
"""
        elif target_param == "depth":
            result_value = calculate_depth(
                params['volume'], params['frequency'],
                params['duration'], params['channels']
            )
            result_text = f"""
💾 **РАСЧЕТ ГЛУБИНЫ КОДИРОВАНИЯ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
**Входные данные:**
• Объём: {params['volume']} байт
• Частота: {params['frequency']} Гц
• Длительность: {params['duration']} сек
• Каналы: {params['channels']} ({'стерео' if params['channels'] == 2 else 'моно'})

**Расчет:**
B = ({params['volume']} * 8) / ({params['frequency']} * {params['duration']} * {params['channels']})
B = {params['volume']*8} / ({params['frequency']} * {params['duration']} * {params['channels']})
B = {result_value:.2f} бит

**Результат:** {result_value:.2f} бит
"""
        elif target_param == "duration":
            result_value = calculate_duration(
                params['volume'], params['frequency'],
                params['depth'], params['channels']
            )
            result_text = f"""
⏱️ **РАСЧЕТ ДЛИТЕЛЬНОСТИ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
**Входные данные:**
• Объём: {params['volume']} байт
• Частота: {params['frequency']} Гц
• Глубина: {params['depth']} бит
• Каналы: {params['channels']} ({'стерео' if params['channels'] == 2 else 'моно'})

**Расчет:**
T = {params['volume']} / [{params['frequency']} * ({params['depth']}/8) * {params['channels']}]
T = {params['volume']} / [{params['frequency']} * {params['depth']/8} * {params['channels']}]
T = {result_value:.2f} сек

**Результат:** {result_value:.2f} сек ({result_value/60:.2f} мин)
"""
        elif target_param == "channels":
            result_value = calculate_channels(
                params['volume'], params['frequency'],
                params['depth'], params['duration']
            )
            result_text = f"""
🎧 **РАСЧЕТ КОЛИЧЕСТВА КАНАЛОВ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
**Входные данные:**
• Объём: {params['volume']} байт
• Частота: {params['frequency']} Гц
• Глубина: {params['depth']} бит
• Длительность: {params['duration']} сек

**Расчет:**
C = {params['volume']} / [{params['frequency']} * ({params['depth']}/8) * {params['duration']}]
C = {params['volume']} / [{params['frequency']} * {params['depth']/8} * {params['duration']}]
C = {result_value:.2f}

**Результат:** {result_value:.2f} ({'стерео' if abs(result_value - 2) < 0.1 else 'моно' if abs(result_value - 1) < 0.1 else 'нестандартное значение'})
"""
        else:
            await message.answer(ERROR_MESSAGES["invalid_choice"])
            await state.clear()
            return
        
        keyboard = [
            [InlineKeyboardButton(text="🔄 Новый расчет", callback_data="sound_coding")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        await message.answer(
            text=result_text,
            reply_markup=reply_markup
        )
        
        await state.clear()
        
    except ZeroDivisionError:
        await message.answer("❌ Ошибка: деление на ноль. Проверьте введенные значения.")
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Ошибка при расчете: {str(e)}")
        await state.clear()


# ========== QR-КОДИРОВАНИЕ ==========

@router.callback_query(F.data == "qr_coding")
async def handle_qr_coding(callback: CallbackQuery):
    """Обработчик выбора раздела 'QR-кодирование'"""
    user_id = callback.from_user.id
    
    if is_session_expired(user_id):
        await callback.answer(ERROR_MESSAGES["timeout"], show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton(text="🔢 Цифровое кодирование", callback_data="qr_numeric")],
        [InlineKeyboardButton(text="🎭 Цифровое с маской", callback_data="qr_numeric_mask")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="systems_conversion"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    message = """
🔲 **QR-КОДИРОВАНИЕ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

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

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

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

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

**Шаг 1 из 2:** Введите число для кодирования

💡 **Примеры:**
• `123456789`
• `42`
• `100`

Введите число:""",
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
        
    else:
        await message.answer(ERROR_MESSAGES["invalid_choice"])
        await state.clear()
        return
    
    keyboard = [
        [InlineKeyboardButton(text="🔄 Новый расчет", callback_data="systems_conversion")],
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

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
**Исходные данные:**
• Число: {digits}
• Маска: `{mask}`

{steps_text}

**Итоговый результат:**
• Двоичный: `{masked_bits}`
• Десятичный: `{int(masked_bits, 2)}`
"""
    
    keyboard = [
        [InlineKeyboardButton(text="🔄 Новый расчет", callback_data="systems_conversion")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        text=result,
        reply_markup=reply_markup
    )
    
    await state.clear()


# ========== ШТРИХ-КОДИРОВАНИЕ ==========

@router.callback_query(F.data == "barcode")
async def handle_barcode(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора раздела 'Штрих-кодирование'"""
    user_id = callback.from_user.id
    
    if is_session_expired(user_id):
        await callback.answer(ERROR_MESSAGES["timeout"], show_alert=True)
        return
    
    update_user_state(user_id, current_method="ean13")
    await state.set_state(BarcodeStates.digits)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="systems_conversion"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    message = """
📊 **ШТРИХ-КОДИРОВАНИЕ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Введите первые 12 цифр для расчета EAN-13 (например, 460123456789):
"""
    
    await callback.message.edit_text(
        text=message,
        reply_markup=reply_markup
    )


@router.message(StateFilter(BarcodeStates.digits))
async def get_ean13_digits(message: Message, state: FSMContext):
    """Получение цифр и расчет EAN-13"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    is_valid, msg = validate_digits(message.text)
    if not is_valid:
        error_msg = f"""
❌ **Ошибка ввода: Цифры**

{msg}

💡 **Пример корректного ввода:**
`460123456789` (ровно 12 цифр)

Пожалуйста, введите 12 цифр:
"""
        await message.answer(error_msg)
        return
    
    if len(message.text) != 12:
        error_msg = f"""
❌ **Ошибка ввода: Длина**

Введено {len(message.text)} цифр, требуется ровно 12.

💡 **Пример корректного ввода:**
`460123456789` (ровно 12 цифр)

Пожалуйста, введите ровно 12 цифр:
"""
        await message.answer(error_msg)
        return
    
    first_12 = message.text
    
    try:
        checksum, even_sum, odd_sum, total = ean13_checksum(first_12)
        full_code = first_12 + str(checksum)
        
        result = format_ean13_result(first_12, even_sum, odd_sum, total, checksum, full_code)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при расчете: {str(e)}")
        return
    
    keyboard = [
        [InlineKeyboardButton(text="🔄 Новый расчет", callback_data="barcode")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        text=result,
        reply_markup=reply_markup
    )
    
    await state.clear()
