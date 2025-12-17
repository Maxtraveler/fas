"""Обработчики модуля классификации и кодирования"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from handlers.states import ClassificationStates
from utils.state_manager import update_user_state, is_session_expired
from utils.validators import validate_number
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
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    message = """
📁 **КЛАССИФИКАЦИЯ И КОДИРОВАНИЕ**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

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

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

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

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

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

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

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

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
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
