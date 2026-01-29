"""
"specializations/oko.py: Хэндлеры для ОКО теста."
Полный FSM: spec → name → position → dept → difficulty → test → results.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from library import (
    TestStates,
    Difficulty,
    CurrentTestState,
    load_questions_for_specialization,
    create_timer,
    get_difficulty_keyboard,
    show_question,
    handle_answer_toggle,
    handle_next_question,
    finish_test,
    get_main_keyboard
)

logger = logging.getLogger(__name__)

# Создаем роутер для специализации OKO
oko_router = Router(name="oko")


@oko_router.callback_query(F.data == "spec_oko")
async def select_oko(callback: CallbackQuery, state: FSMContext):
    """Выбор специализации ОКО → запрос ФИО."""
    await callback.message.edit_text(
        "📡 <b>ОКО</b>\n\nВведите ваше ФИО:"
    )
    await state.set_state(TestStates.waiting_full_name)
    await state.update_data(specialization="oko")
    await callback.answer()


@oko_router.message(StateFilter(TestStates.waiting_full_name))
async def process_name(message: Message, state: FSMContext):
    """ФИО → должность."""
    await state.update_data(full_name=message.text.strip())
    await message.answer("Введите вашу должность:")
    await state.set_state(TestStates.waiting_position)


@oko_router.message(StateFilter(TestStates.waiting_position))
async def process_position(message: Message, state: FSMContext):
    """Должность → отдел."""
    await state.update_data(position=message.text.strip())
    await message.answer("Введите ваше подразделение:")
    await state.set_state(TestStates.waiting_department)


@oko_router.message(StateFilter(TestStates.waiting_department))
async def process_department(message: Message, state: FSMContext):
    """Отдел → выбор сложности."""
    await state.update_data(department=message.text.strip())
    
    await message.answer(
        "Выберите уровень сложности:",
        reply_markup=get_difficulty_keyboard()
    )
    await state.set_state(TestStates.waiting_difficulty)


@oko_router.callback_query(
    F.data.startswith("diff_"),
    StateFilter(TestStates.waiting_difficulty)
)
async def select_difficulty(callback: CallbackQuery, state: FSMContext):
    """Сложность → загрузка вопросов → старт теста."""
    try:
        # Извлекаем уровень сложности
        diff_name = callback.data.split("_", 1)[1]
        difficulty = Difficulty(diff_name)
        
        # Получаем данные пользователя
        user_data = await state.get_data()
        specialization = user_data.get("specialization", "oko")
        
        # Загружаем вопросы
        questions = load_questions_for_specialization(
            specialization,
            difficulty,
            callback.from_user.id
        )
        
        if not questions:
            await callback.message.edit_text(
                "❌ Не удалось загрузить вопросы. Попробуйте позже."
            )
            await state.clear()
            return
        
        # Создаем состояние теста
        test_state = CurrentTestState(
            questions=questions,
            specialization=specialization,
            difficulty=difficulty,
            full_name=user_data.get("full_name", ""),
            position=user_data.get("position", ""),
            department=user_data.get("department", "")
        )
        
        # Создаем и запускаем таймер
        async def on_timeout():
            """Callback при истечении времени."""
            await finish_test(callback, state)
        
        timer = create_timer(difficulty, on_timeout)
        await timer.start()
        test_state.timer_task = timer
        
        # Сохраняем состояние и переходим к тесту
        await state.update_data(test_state=test_state)
        await state.set_state(TestStates.answering_question)
        
        # Показываем первый вопрос
        await show_question(callback, test_state, question_index=0)
        await callback.answer()
        
        logger.info(
            f"▶️ Пользователь {callback.from_user.id} начал тест "
            f"{specialization} ({difficulty.value})"
        )
        
    except ValueError:
        await callback.answer("❌ Неверный уровень сложности")
        logger.error(f"❌ Неверный уровень сложности: {callback.data}")


@oko_router.callback_query(
    F.data.startswith("ans_"),
    StateFilter(TestStates.answering_question)
)
async def answer_toggle(callback: CallbackQuery, state: FSMContext):
    """Toggle выбора ответа во время теста."""
    await handle_answer_toggle(callback, state)


@oko_router.callback_query(
    F.data == "next",
    StateFilter(TestStates.answering_question)
)
async def next_question(callback: CallbackQuery, state: FSMContext):
    """Кнопка 'Далее' → следующий вопрос."""
    await handle_next_question(callback, state)


# === FINISH CALLBACKS ===

@oko_router.callback_query(F.data == "show_answers")
async def show_correct_answers(callback: CallbackQuery, state: FSMContext):
    """Показать правильные ответы (60 секунд)."""
    data = await state.get_data()
    test_state: CurrentTestState = data.get("test_state")
    
    if not test_state:
        await callback.answer("❌ Данные теста не найдены")
        return
    
    # Формируем текст с правильными ответами
    answers_text = "📋 <b>Правильные ответы:</b>\n\n"
    
    for i, question in enumerate(test_state.questions, 1):
        user_answer = test_state.answers_history.get(i - 1, set())
        correct = question.correct_answers
        is_correct = user_answer == correct
        
        emoji = "✅" if is_correct else "❌"
        correct_nums = ", ".join(str(n) for n in sorted(correct))
        
        answers_text += f"{emoji} <b>Вопрос {i}:</b> {correct_nums}\n"
    
    await callback.message.edit_text(answers_text)
    await callback.answer()
    
    # TODO: Автоудаление через 60 секунд


@oko_router.callback_query(F.data == "generate_cert")
async def generate_certificate(callback: CallbackQuery, state: FSMContext):
    """Генерация PDF сертификата."""
    await callback.answer("📄 Генерация сертификата... (в разработке)")
    # TODO: Реализовать генерацию PDF


@oko_router.callback_query(F.data == "repeat_test")
async def repeat_test(callback: CallbackQuery, state: FSMContext):
    """Повторить тест - возврат к выбору сложности."""
    await state.clear()
    await select_oko(callback, state)


@oko_router.callback_query(F.data == "my_stats")
async def show_stats(callback: CallbackQuery):
    """Показать статистику пользователя."""
    await callback.answer("📊 Статистика (в разработке)")
    # TODO: Реализовать статистику


@oko_router.callback_query(F.data == "main_menu")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """Вернуться в главное меню."""
    await state.clear()
    await callback.message.edit_text(
        "🧪 <b>ФССП Тест-бот</b>\n\nВыберите специализацию:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@oko_router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    """Показать помощь."""
    help_text = (
        "❓ <b>Помощь по боту</b>\n\n"
        "1. Выберите специализацию\n"
        "2. Введите свои данные\n"
        "3. Выберите уровень сложности\n"
        "4. Отвечайте на вопросы\n"
        "5. Получите результат и сертификат\n\n"
        "Кнопки с числами 1️⃣2️⃣3️⃣ - выбор вариантов ответа\n"
        "✅ - выбранный вариант\n"
        "➡️ Далее - переход к следующему вопросу"
    )
    await callback.message.edit_text(help_text, reply_markup=get_main_keyboard())
    await callback.answer()
