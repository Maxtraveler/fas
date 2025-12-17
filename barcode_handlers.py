"""Обработчики модуля штрих-кодирования"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from handlers.states import BarcodeStates
from utils.state_manager import update_user_state, is_session_expired
from utils.validators import validate_digits
from utils.formatters import format_ean13_result
from calculators.barcode_calculator import ean13_checksum
from config import ERROR_MESSAGES

router = Router()


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
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    message = """
📊 **ШТРИХ-КОДИРОВАНИЕ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

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
