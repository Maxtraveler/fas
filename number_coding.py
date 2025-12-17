"""Обработчики модуля кодирования чисел"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from handlers.states import NumberCodingStates
from utils.state_manager import update_user_state, is_session_expired
from config import ERROR_MESSAGES

router = Router()


@router.callback_query(F.data == "number_coding")
async def handle_number_coding(callback: CallbackQuery):
    """Обработчик выбора раздела 'Кодирование чисел'"""
    user_id = callback.from_user.id
    
    if is_session_expired(user_id):
        await callback.answer(ERROR_MESSAGES["timeout"], show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton(text="🔄 Обратный код", callback_data="number_reverse")],
        [InlineKeyboardButton(text="➕ Дополнительный код", callback_data="number_additional")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    message = """
🔢 **КОДИРОВАНИЕ ЧИСЕЛ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Выберите метод кодирования:
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
        [InlineKeyboardButton(text="🔙 Назад", callback_data="number_coding"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(
        f"""🔢 **{method_names[method].upper()}**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Введите число для кодирования.

💡 **Примеры:**
• `10` - положительное число
• `-5` - отрицательное число
• `127` - большое число

Введите число:""",
        reply_markup=reply_markup
    )


