"""Обработчики модуля кодов исправления ошибок"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from handlers.states import ErrorCorrectionStates
from utils.state_manager import update_user_state, is_session_expired
from utils.validators import validate_binary
from utils.formatters import format_hamming_encode_result, format_hamming_decode_result
from calculators.hamming_code import hamming_encode, hamming_decode
from config import ERROR_MESSAGES

router = Router()


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
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    message = """
🔧 **КОДЫ ИСПРАВЛЕНИЯ ОШИБОК**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

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

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

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

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

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
