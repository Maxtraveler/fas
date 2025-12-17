"""Обработчики главного меню и навигации"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

from utils.state_manager import reset_user_state, is_session_expired
from config import ERROR_MESSAGES

router = Router()

# Создаем постоянную клавиатуру с кнопкой "Меню"
def get_main_keyboard():
    """Возвращает постоянную клавиатуру с кнопкой Меню"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🏠 Меню")]],
        resize_keyboard=True,
        persistent=True
    )
    return keyboard


@router.message(F.text == "🏠 Меню")
async def handle_menu_button(message: Message, state=None):
    """Обработчик кнопки Меню (имеет приоритет, работает даже в FSM)"""
    user_id = message.from_user.id
    reset_user_state(user_id)
    if state:
        await state.clear()  # Очищаем состояние FSM если есть
    await show_main_menu(message)


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    reset_user_state(user_id)
    
    await show_main_menu(message)
    # Отправляем постоянную клавиатуру только при первом запуске
    reply_markup = get_main_keyboard()
    await message.answer(
        text="Используйте кнопку '🏠 Меню' для возврата в главное меню в любое время.",
        reply_markup=reply_markup
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Обработчик команды /menu"""
    await show_main_menu(message)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = """
📖 **СПРАВКА**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Этот бот помогает применять различные методы кодирования информации.

**Доступные команды:**
/start - Начать работу с ботом
/menu - Показать главное меню
/help - Показать эту справку
/cancel - Отменить текущую операцию

**Доступные разделы:**
• Системы счисления и кодировка - перевод систем, кодирование чисел, звука, QR, КОИ-8
• Коды и ошибки - обнаружение и исправление ошибок, штрих-коды, классификация

Используйте кнопки меню для навигации.
"""
    
    await message.answer(text=help_text)


async def show_main_menu(message_or_callback):
    """Отображение главного меню"""
    keyboard = [
        [InlineKeyboardButton(text="🔄 Системы счисления и кодировка", callback_data="systems_conversion")],
        [InlineKeyboardButton(text="🛡️ Коды и ошибки", callback_data="codes_and_errors")]
    ]
    
    inline_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    reply_markup = get_main_keyboard()  # Постоянная клавиатура с кнопкой Меню
    
    menu_text = """
🏠 **ГЛАВНОЕ МЕНЮ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

🔄 Системы счисления и кодировка
🛡️ Коды и ошибки

Выберите раздел:
"""
    
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.edit_text(
            text=menu_text,
            reply_markup=inline_markup
        )
    else:
        await message_or_callback.answer(
            text=menu_text,
            reply_markup=inline_markup
        )


@router.callback_query(F.data == "back")
async def handle_back(callback: CallbackQuery):
    """Обработчик кнопки 'Назад'"""
    await show_main_menu(callback)


@router.callback_query(F.data == "main_menu")
async def handle_main_menu(callback: CallbackQuery):
    """Обработчик возврата в главное меню"""
    user_id = callback.from_user.id
    
    if is_session_expired(user_id):
        await callback.answer(ERROR_MESSAGES["timeout"], show_alert=True)
        return
    
    await show_main_menu(callback)
