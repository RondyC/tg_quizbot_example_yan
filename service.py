import json
from database import pool, execute_update_query, execute_select_query
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram import types

def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()
    for option in answer_options:
        callback_data = "right_answer" if option == right_answer else "wrong_answer"
        builder.button(text=option, callback_data=callback_data)
    builder.adjust(1)
    return builder.as_markup()

async def get_question_by_index(index):
    query = """
    DECLARE $index AS Uint64;

    SELECT
        question_id,
        question_text,
        options,
        correct_option_index
    FROM `quiz_questions`
    WHERE question_id == $index;
    """
    results = execute_select_query(pool, query, index=index)
    if len(results) == 0:
        return None

    question_data = results[0]
    question_data['options'] = json.loads(question_data['options'])
    return question_data

async def get_total_questions():
    query = """
    SELECT COUNT(*) AS total
    FROM `quiz_questions`;
    """
    results = execute_select_query(pool, query)
    return results[0]['total']

async def get_question(message, user_id):
    current_question_index = await get_quiz_index(user_id)
    question_data = await get_question_by_index(current_question_index)
    if not question_data:
        await message.answer("Вопрос не найден.")
        return

    correct_index = question_data['correct_option_index']
    opts = question_data['options']
    kb = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(f"{question_data['question_text']}", reply_markup=kb)

async def new_quiz(message):
    user_id = message.from_user.id
    current_question_index = 0
    await update_quiz_index(user_id, current_question_index)
    await set_user_score(user_id, 0)
    await get_question(message, user_id)

async def get_quiz_index(user_id):
    get_user_index = """
    DECLARE $user_id AS Uint64;

    SELECT question_index
    FROM `quiz_state`
    WHERE user_id == $user_id;
    """
    results = execute_select_query(pool, get_user_index, user_id=user_id)

    if len(results) == 0 or results[0]["question_index"] is None:
        return 0
    return results[0]["question_index"]

async def update_quiz_index(user_id, question_index):
    set_quiz_state = """
    DECLARE $user_id AS Uint64;
    DECLARE $question_index AS Uint64;

    UPSERT INTO `quiz_state` (`user_id`, `question_index`)
    VALUES ($user_id, $question_index);
    """

    execute_update_query(
        pool,
        set_quiz_state,
        user_id=user_id,
        question_index=question_index,
    )

async def get_user_score(user_id):
    get_user_score_query = """
    DECLARE $user_id AS Uint64;

    SELECT score
    FROM `quiz_state`
    WHERE user_id == $user_id;
    """
    results = execute_select_query(pool, get_user_score_query, user_id=user_id)
    if len(results) == 0 or results[0]["score"] is None:
        return 0
    return results[0]["score"]

async def set_user_score(user_id, score):
    set_score_query = """
    DECLARE $user_id AS Uint64;
    DECLARE $score AS Uint64;

    UPSERT INTO `quiz_state` (`user_id`, `score`)
    VALUES ($user_id, $score);
    """
    execute_update_query(
        pool,
        set_score_query,
        user_id=user_id,
        score=score,
    )

async def update_score(user_id, increment=0):
    current_score = await get_user_score(user_id)
    new_score = current_score + increment
    await set_user_score(user_id, new_score)