"""
Клавиатуры: главное меню, уровни сложности, тест с ЧИСЛОВЫМИ кнопками 1️⃣2️⃣3️⃣4️⃣5️⃣, результаты.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .enum import Difficulty


# Маппинг цифр на эмодзи
NUMBER_EMOJI = {
    1: "1️⃣",
    2: "2️⃣",
    3: "3️⃣",
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣"
}


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню: 11 специализаций inline кнопками."""
    builder = InlineKeyboardBuilder()
    
    # 11 специализаций
    specs = [
        ("🚨 ООУПДС", "spec_oupds"),
        ("📊 Исполнители", "spec_ispolniteli"),
        ("🧑‍🧑‍🧒 Алименты", "spec_aliment"),
        ("🎯 Дознание", "spec_doznanie"),
        ("⏳ Розыск", "spec_rozyisk"),
        ("📈 Профподготовка", "spec_prof"),
        ("📡 ОКО", "spec_oko"),
        ("💻 Информатизация", "spec_informatika"),
        ("👥 Кадры", "spec_kadry"),
        ("🔒 Безопасность", "spec_bezopasnost"),
        ("💼 Управление", "spec_upravlenie"),
    ]
    
    for text, callback in specs:
        builder.button(text=text, callback_data=callback)
    
    builder.button(text="❓ Помощь", callback_data="help")
    builder.adjust(2)  # 2 колонки
    
    return builder.as_markup()


def get_difficulty_keyboard() -> InlineKeyboardMarkup:
    """Выбор уровня сложности."""
    builder = InlineKeyboardBuilder()
    
    difficulties = [
        ("🥉 Резерв (20 вопросов, 35 мин)", "diff_резерв"),
        ("🥈 Базовый (30 вопросов, 25 мин)", "diff_базовый"),
        ("🥇 Стандартный (40 вопросов, 20 мин)", "diff_стандартный"),
        ("💎 Продвинутый (50 вопросов, 20 мин)", "diff_продвинутый"),
    ]
    
    for text, callback in difficulties:
        builder.button(text=text, callback_data=callback)
    
    builder.adjust(1)  # 1 колонка
    return builder.as_markup()


def get_test_keyboard(options: list[str], selected: set[int] | None = None) -> InlineKeyboardMarkup:
    """
    Клавиатура теста с ЧИСЛОВЫМИ ЭМОДЗИ 1️⃣2️⃣3️⃣4️⃣5️⃣.
    
    Args:
        options: Список вариантов ответа
        selected: Множество выбранных номеров (1-based)
    
    Returns:
        InlineKeyboardMarkup с числовыми кнопками
    """
    builder = InlineKeyboardBuilder()
    selected = selected or set()
    
    for i, opt_text in enumerate(options, start=1):
        # Числовой эмодзи
        number_emoji = NUMBER_EMOJI.get(i, str(i))
        
        # Галочка если выбрано
        check = "✅ " if i in selected else ""
        
        # Сокращенный текст ответа (первые 30 символов)
        short_text = opt_text[:30] + "..." if len(opt_text) > 30 else opt_text
        
        button_text = f"{check}{number_emoji} {short_text}"
        
        builder.button(
            text=button_text,
            callback_data=f"ans_{i}"
        )
    
    # Кнопка "Далее"
    builder.button(text="➡️ Далее", callback_data="next")
    
    # Компоновка: 2 колонки для ответов, кнопка "Далее" на всю ширину
    builder.adjust(2, *([2] * (len(options) // 2)), 1)
    
    return builder.as_markup()


def get_finish_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после завершения теста."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📋 Показать правильные ответы", callback_data="show_answers")
    builder.button(text="🏆 Сертификат PDF", callback_data="generate_cert")
    builder.button(text="🔄 Повторить тест", callback_data="repeat_test")
    builder.button(text="📊 Моя статистика", callback_data="my_stats")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    
    builder.adjust(1)  # 1 колонка
    return builder.as_markup()
