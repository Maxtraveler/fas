"""Обработчики модуля кодирования звука"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from handlers.states import SoundCodingStates
from utils.state_manager import update_user_state, get_user_state, is_session_expired
from utils.validators import validate_number, validate_float
from utils.formatters import format_audio_result
from calculators.sound_calculator import calculate_audio_size
from config import ERROR_MESSAGES

router = Router()


@router.callback_query(F.data == "sound_coding")
async def handle_sound_coding(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора раздела 'Кодирование звука'"""
    user_id = callback.from_user.id
    
    if is_session_expired(user_id):
        await callback.answer(ERROR_MESSAGES["timeout"], show_alert=True)
        return
    
    update_user_state(user_id, current_menu="sound_coding", current_method="audio_size")
    await state.set_state(SoundCodingStates.frequency)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    message = """
🔊 **КОДИРОВАНИЕ ЗВУКА**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

**Шаг 1 из 4:** Частота дискретизации

Введите частоту дискретизации в Гц.

💡 **Примеры:**
• `44100` - стандартная частота для аудио
• `22050` - для сжатого аудио
• `48000` - профессиональная частота

Введите значение:
"""
    
    await callback.message.edit_text(
        text=message,
        reply_markup=reply_markup
    )


@router.message(StateFilter(SoundCodingStates.frequency))
async def get_frequency(message: Message, state: FSMContext):
    """Получение частоты дискретизации"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    is_valid, msg = validate_number(message.text, min_val=1)
    if not is_valid:
        error_msg = f"""
❌ **Ошибка ввода: Частота дискретизации**

{msg}

💡 **Пример корректного ввода:**
`44100` или `22050`

Пожалуйста, введите частоту дискретизации в Гц (целое число, не меньше 1):
"""
        await message.answer(error_msg)
        return
    
    frequency = int(message.text)
    await state.update_data(frequency=frequency)
    await state.set_state(SoundCodingStates.depth)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        """**Шаг 2 из 4:** Глубина кодирования

Введите глубину кодирования в битах.

💡 **Примеры:**
• `16` - стандартная глубина (2 байта)
• `8` - низкое качество (1 байт)
• `24` - высокое качество (3 байта)

Введите значение:""",
        reply_markup=reply_markup
    )


@router.message(StateFilter(SoundCodingStates.depth))
async def get_depth(message: Message, state: FSMContext):
    """Получение глубины кодирования"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    is_valid, msg = validate_number(message.text, min_val=1)
    if not is_valid:
        error_msg = f"""
❌ **Ошибка ввода: Глубина кодирования**

{msg}

💡 **Пример корректного ввода:**
`16` или `8`

Пожалуйста, введите глубину кодирования в битах (целое число, не меньше 1):
"""
        await message.answer(error_msg)
        return
    
    depth = int(message.text)
    await state.update_data(depth=depth)
    await state.set_state(SoundCodingStates.duration)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        """**Шаг 3 из 4:** Длительность звука

Введите длительность звука в секундах.

💡 **Примеры:**
• `60` - одна минута
• `180` - три минуты
• `3.5` - три с половиной секунды

Введите значение:""",
        reply_markup=reply_markup
    )


@router.message(StateFilter(SoundCodingStates.duration))
async def get_duration(message: Message, state: FSMContext):
    """Получение длительности"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    is_valid, msg, duration = validate_float(message.text, min_val=0.1)
    if not is_valid:
        error_msg = f"""
❌ **Ошибка ввода: Длительность**

{msg}

💡 **Пример корректного ввода:**
`60` или `3.5`

Пожалуйста, введите длительность в секундах (число, не меньше 0.1):
"""
        await message.answer(error_msg)
        return
    
    await state.update_data(duration=duration)
    await state.set_state(SoundCodingStates.channels)
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        """**Шаг 4 из 4:** Количество каналов

Введите количество каналов.

💡 **Варианты:**
• `1` - моно (один канал)
• `2` - стерео (два канала)

Введите значение:""",
        reply_markup=reply_markup
    )


@router.message(StateFilter(SoundCodingStates.channels))
async def get_channels(message: Message, state: FSMContext):
    """Получение количества каналов и расчет результата"""
    user_id = message.from_user.id
    
    if is_session_expired(user_id):
        await message.answer(ERROR_MESSAGES["timeout"])
        await state.clear()
        return
    
    is_valid, msg = validate_number(message.text, min_val=1, max_val=2)
    if not is_valid:
        error_msg = f"""
❌ **Ошибка ввода: Количество каналов**

{msg}

💡 **Пример корректного ввода:**
`1` - для моно
`2` - для стерео

Пожалуйста, введите количество каналов (1 или 2):
"""
        await message.answer(error_msg)
        return
    
    channels = int(message.text)
    data = await state.get_data()
    
    # Выполнить расчет
    total_bytes, kb, mb = calculate_audio_size(
        data["frequency"],
        data["depth"],
        data["duration"],
        channels
    )
    
    # Форматировать результат
    result = format_audio_result(
        data["frequency"],
        data["depth"],
        data["duration"],
        channels,
        total_bytes,
        kb,
        mb
    )
    
    keyboard = [
        [InlineKeyboardButton(text="🔄 Новый расчет", callback_data="sound_coding")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        text=result,
        reply_markup=reply_markup
    )
    
    await state.clear()
