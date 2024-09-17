from aiogram import types, Router, F
from aiogram.filters import Command
from service import generate_options_keyboard, get_question, new_quiz, get_quiz_index, update_quiz_index, get_user_score, update_score, get_question_by_index, get_total_questions, set_user_score
from aiogram.utils.keyboard import ReplyKeyboardBuilder

router = Router()

@router.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup()

    await update_score(callback.from_user.id, increment=1)
    await callback.message.answer("Верно!")
    current_question_index = await get_quiz_index(callback.from_user.id)
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)

    total_questions = await get_total_questions()
    if current_question_index < total_questions:
        await get_question(callback.message, callback.from_user.id)
    else:
        score = await get_user_score(callback.from_user.id)
        await callback.message.answer(f"Это был последний вопрос. Квиз завершен! Ваш результат: {score} из {total_questions}")
        # Сброс состояния квиза
        await update_quiz_index(callback.from_user.id, 0)
        await set_user_score(callback.from_user.id, 0)

@router.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup()

    current_question_index = await get_quiz_index(callback.from_user.id)
    question_data = await get_question_by_index(current_question_index)
    correct_option = question_data['correct_option_index']
    options = question_data['options']

    await callback.message.answer(f"Неправильно. Правильный ответ: {options[correct_option]}")

    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)

    total_questions = await get_total_questions()
    if current_question_index < total_questions:
        await get_question(callback.message, callback.from_user.id)
    else:
        score = await get_user_score(callback.from_user.id)
        await callback.message.answer(f"Это был последний вопрос. Квиз завершен! Ваш результат: {score} из {total_questions}")
        # Сброс состояния квиза
        await update_quiz_index(callback.from_user.id, 0)
        await set_user_score(callback.from_user.id, 0)

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="Начать игру")
    reply_markup = builder.as_markup(resize_keyboard=True)
    await message.answer("Добро пожаловать в квиз!", reply_markup=reply_markup)

@router.message(F.text == "Начать игру")
@router.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    photo_url = 'https://storage.yandexcloud.net/quiz-photo/QuizPhoto.png'
    await message.answer_photo(photo=photo_url, caption="Давайте начнем квиз!")
    await new_quiz(message)
