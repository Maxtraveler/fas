"""Модуль расчета параметров звукового файла"""


def calculate_audio_size(frequency, depth, duration, channels):
    """
    Расчет объема звукового файла
    
    Формула: V = F × (B/8) × T × C
    
    Args:
        frequency: Частота дискретизации (Гц)
        depth: Глубина кодирования (бит)
        duration: Длительность звука (секунды)
        channels: Количество каналов (1-моно, 2-стерео)
        
    Returns:
        tuple: (total_bytes, kb, mb)
    """
    bytes_per_sample = depth / 8
    total_bytes = frequency * bytes_per_sample * duration * channels
    kb = total_bytes / 1024
    mb = kb / 1024
    return int(total_bytes), kb, mb


def calculate_frequency(volume, depth, duration, channels):
    """
    Расчет частоты дискретизации
    
    Формула: F = V / [(B/8) × T × C]
    
    Args:
        volume: Объем файла (байты)
        depth: Глубина кодирования (бит)
        duration: Длительность звука (секунды)
        channels: Количество каналов (1-моно, 2-стерео)
        
    Returns:
        float: Частота дискретизации (Гц)
    """
    bytes_per_sample = depth / 8
    frequency = volume / (bytes_per_sample * duration * channels)
    return frequency


def calculate_depth(volume, frequency, duration, channels):
    """
    Расчет глубины кодирования
    
    Формула: B = (V × 8) / (F × T × C)
    
    Args:
        volume: Объем файла (байты)
        frequency: Частота дискретизации (Гц)
        duration: Длительность звука (секунды)
        channels: Количество каналов (1-моно, 2-стерео)
        
    Returns:
        float: Глубина кодирования (бит)
    """
    depth = (volume * 8) / (frequency * duration * channels)
    return depth


def calculate_duration(volume, frequency, depth, channels):
    """
    Расчет длительности звука
    
    Формула: T = V / [F × (B/8) × C]
    
    Args:
        volume: Объем файла (байты)
        frequency: Частота дискретизации (Гц)
        depth: Глубина кодирования (бит)
        channels: Количество каналов (1-моно, 2-стерео)
        
    Returns:
        float: Длительность звука (секунды)
    """
    bytes_per_sample = depth / 8
    duration = volume / (frequency * bytes_per_sample * channels)
    return duration


def calculate_channels(volume, frequency, depth, duration):
    """
    Расчет количества каналов
    
    Формула: C = V / [F × (B/8) × T]
    
    Args:
        volume: Объем файла (байты)
        frequency: Частота дискретизации (Гц)
        depth: Глубина кодирования (бит)
        duration: Длительность звука (секунды)
        
    Returns:
        float: Количество каналов
    """
    bytes_per_sample = depth / 8
    channels = volume / (frequency * bytes_per_sample * duration)
    return channels

