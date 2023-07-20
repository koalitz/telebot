import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup


# Классы состояний для регистрации и отмены регистрации
class RegisterState(StatesGroup):
    RegisterEvent = State()
    RegisterEmail = State()
    RegisterFirstName = State()
    RegisterLastName = State()


class UnregisterState(StatesGroup):
    UnregisterEvent = State()
    UnregisterEmail = State()


POSTGRES_DSN = "postgresql://postgres:zeynia1234@localhost/koalitz"

bot = Bot(token="6168649405:AAHZcjXu7LtX6elM5_QtgWRTkg6u4KNyl2E")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Функция для получения списка мероприятий из базы данных
async def get_events():
    conn = await asyncpg.connect(POSTGRES_DSN)
    events = await conn.fetch("SELECT * FROM events")
    await conn.close()
    return events


# Функция для регистрации пользователя на мероприятие
async def register_user(event_id, email, first_name, last_name):
    conn = await asyncpg.connect(POSTGRES_DSN)
    await conn.execute("INSERT INTO registrations (event_id, email, first_name, last_name) VALUES ($1, $2, $3, $4)",
                       event_id, email, first_name, last_name)
    await conn.close()


# Функция для отмены регистрации пользователя на мероприятие
async def unregister_user(event_id, email):
    conn = await asyncpg.connect(POSTGRES_DSN)
    await conn.execute("DELETE FROM registrations WHERE event_id = $1 AND email = $2", event_id, email)
    await conn.close()


@dp.message_handler(commands=['start'])
async def start(message: types.Message, state: FSMContext):
    events = await get_events()
    events_list = "\n".join([f"{event['id']}. {event['name']}" for event in events])
    await message.answer(f"Добро пожаловать! Выберите мероприятие:\n\n{events_list}")


@dp.message_handler(regexp=r"^\d+.\s")
async def register(message: types.Message, state: FSMContext):
    event_id = int(message.text.split(".")[0])
    await state.update_data(event_id=event_id)
    await message.answer("Введите ваш email:")
    await RegisterState.RegisterEmail.set()


@dp.message_handler(state=RegisterState.RegisterEmail)
async def process_register_email(message: types.Message, state: FSMContext):
    email = message.text
    await state.update_data(email=email)
    await message.answer("Введите ваше имя:")
    await RegisterState.RegisterFirstName.set()


@dp.message_handler(state=RegisterState.RegisterFirstName)
async def process_register_firstname(message: types.Message, state: FSMContext):
    first_name = message.text
    await state.update_data(first_name=first_name)
    await message.answer("Введите вашу фамилию:")
    await RegisterState.RegisterLastName.set()


@dp.message_handler(state=RegisterState.RegisterLastName)
async def process_register_lastname(message: types.Message, state: FSMContext):
    last_name = message.text
    data = await state.get_data()
    event_id = data['event_id']
    email = data['email']
    first_name = data['first_name']
    await register_user(event_id, email, first_name, last_name)
    await message.answer("Регистрация успешно завершена!")
    await state.finish()


@dp.message_handler(commands=['unregister'])
async def unregister(message: types.Message, state: FSMContext):
    events = await get_events()
    events_list = "\n".join([f"{event['id']}. {event['name']}" for event in events])
    await message.answer(f"Выберите мероприятие для отмены регистрации:\n\n{events_list}")
    await UnregisterState.UnregisterEvent.set()


@dp.message_handler(state=UnregisterState.UnregisterEvent)
async def process_unregister_event(message: types.Message, state: FSMContext):
    event_id = int(message.text.split(".")[0])
    await state.update_data(event_id=event_id)
    await message.answer("Введите ваш email:")
    await UnregisterState.UnregisterEmail.set()


@dp.message_handler(state=UnregisterState.UnregisterEmail)
async def process_unregister_email(message: types.Message, state: FSMContext):
    event_id = (await state.get_data())['event_id']
    email = message.text
    await unregister_user(event_id, email)
    await message.answer("Регистрация успешно отменена!")
    await state.finish()


if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)