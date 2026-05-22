import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import CommandStart

from db import init_db, execute, fetch, fetchrow

# =========================
# BOT
# =========================
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_state = {}


# =========================
# INIT DB TABLES
# =========================
async def init_tables():
    await execute("""
    CREATE TABLE IF NOT EXISTS subjects(
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE
    )
    """)

    await execute("""
    CREATE TABLE IF NOT EXISTS grades(
        id SERIAL PRIMARY KEY,
        subject_id INTEGER,
        grade INTEGER
    )
    """)


# =========================
# SUBJECTS
# =========================
async def add_subject(name):
    await execute(
        "INSERT INTO subjects(name) VALUES($1) ON CONFLICT DO NOTHING",
        name
    )


async def get_subjects():
    rows = await fetch("SELECT name FROM subjects")
    return [r["name"] for r in rows]


async def delete_subject(name):
    row = await fetchrow("SELECT id FROM subjects WHERE name=$1", name)

    if row:
        await execute("DELETE FROM grades WHERE subject_id=$1", row["id"])
        await execute("DELETE FROM subjects WHERE id=$1", row["id"])


async def subject_id(name):
    row = await fetchrow("SELECT id FROM subjects WHERE name=$1", name)
    return row["id"] if row else None


# =========================
# GRADES
# =========================
async def add_grade(subject, grade):
    sid = await subject_id(subject)
    if not sid:
        return

    await execute(
        "INSERT INTO grades(subject_id, grade) VALUES($1,$2)",
        sid, grade
    )


async def get_grades(subject):
    sid = await subject_id(subject)
    if not sid:
        return []

    rows = await fetch(
        "SELECT grade FROM grades WHERE subject_id=$1",
        sid
    )

    return [r["grade"] for r in rows]


async def get_all_subject_grades():
    subjects = await fetch("SELECT id, name FROM subjects")

    result = {}

    for s in subjects:
        rows = await fetch(
            "SELECT grade FROM grades WHERE subject_id=$1",
            s["id"]
        )
        result[s["name"]] = [r["grade"] for r in rows]

    return result


# =========================
# STATS
# =========================
async def subject_avg(subject):
    g = await get_grades(subject)
    return sum(g) / len(g) if g else 0


async def gpa():
    subs = await get_subjects()
    avgs = []

    for s in subs:
        a = await subject_avg(s)
        if a > 0:
            avgs.append(a)

    return sum(avgs) / len(avgs) if avgs else 0


# =========================
# UI
# =========================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Предметы", callback_data="subjects")],
        [InlineKeyboardButton(text="📝 Оценки", callback_data="grades")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="🧮 GPA", callback_data="gpa")]
    ])


# =========================
# START
# =========================
@dp.message(CommandStart())
async def start(m: Message):
    await m.answer("📚 Дневник", reply_markup=main_menu())


# =========================
# SUBJECTS
# =========================
@dp.callback_query(F.data == "subjects")
async def subjects(c: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить", callback_data="add_subject")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data="del_subject")],
        [InlineKeyboardButton(text="📋 Список", callback_data="list_subjects")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])
    await c.message.edit_text("📚 Предметы", reply_markup=kb)


@dp.callback_query(F.data == "list_subjects")
async def list_subjects(c: CallbackQuery):
    subs = await get_subjects()
    await c.message.answer("\n".join(subs) or "пусто")


@dp.callback_query(F.data == "add_subject")
async def add_subject_cb(c: CallbackQuery):
    user_state[c.from_user.id] = "add_subject"
    await c.message.answer("Введите предмет:")


@dp.callback_query(F.data == "del_subject")
async def del_subject_cb(c: CallbackQuery):
    await c.message.answer("Введите название предмета для удаления:")


@dp.message()
async def text(m: Message):
    if user_state.get(m.from_user.id) == "add_subject":
        await add_subject(m.text)
        user_state.pop(m.from_user.id)
        await m.answer("Добавлено")


# =========================
# GRADES
# =========================
@dp.callback_query(F.data == "grades")
async def grades_menu(c: CallbackQuery):
    await c.message.answer("Оценки: используйте команды (упрощённая версия PostgreSQL)")


# =========================
# STATS
# =========================
@dp.callback_query(F.data == "stats")
async def stats(c: CallbackQuery):
    text = "📊 Статистика:\n\n"

    for s in await get_subjects():
        avg = await subject_avg(s)
        if avg > 0:
            text += f"{s}: {avg:.2f}\n"

    await c.message.answer(text or "пусто")


# =========================
# GPA
# =========================
@dp.callback_query(F.data == "gpa")
async def gpa_cb(c: CallbackQuery):
    await c.message.answer(f"🧮 GPA: {await gpa():.2f}")


# =========================
# START BOT
# =========================
async def main():
    await init_db()
    await init_tables()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())