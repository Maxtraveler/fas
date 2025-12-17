"""FSM состояния для бота"""

from aiogram.fsm.state import State, StatesGroup


class SoundCodingStates(StatesGroup):
    target_param = State()  # Выбор параметра для вычисления
    input_volume = State()  # Ввод объёма
    input_frequency = State()  # Ввод частоты
    input_depth = State()  # Ввод глубины
    input_duration = State()  # Ввод длительности
    input_channels = State()  # Ввод каналов


class NumberCodingStates(StatesGroup):
    number = State()
    bits = State()


class ErrorDetectionStates(StatesGroup):
    binary = State()
    weight = State()
    number = State()


class ErrorCorrectionStates(StatesGroup):
    data = State()


class BarcodeStates(StatesGroup):
    digits = State()


class QRStates(StatesGroup):
    input = State()
    mask = State()


class ClassificationStates(StatesGroup):
    total = State()
    used = State()


class SystemsConversionStates(StatesGroup):
    number = State()
    from_base = State()
    to_base = State()
    text = State()
    binary = State()
    block_size = State()

