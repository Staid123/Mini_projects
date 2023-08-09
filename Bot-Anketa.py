from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, StateFilter, Text
from aiogram.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, PhotoSize
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.fsm.storage.redis import RedisStorage, Redis


BOT_TOKEN = '6206897348:AAENqclh-o1SObNCLJV69uJCTL5VUVOgj22'

# Инициализируем Redis
redis: Redis = Redis(host='localhost')

# Инициализируем хранилище (создаем экземпляр класса MemoryStorage)
storage: RedisStorage = RedisStorage(redis=redis)

# Создаем объекты бота и диспетчера
bot: Bot = Bot(BOT_TOKEN)
dp: Dispatcher = Dispatcher(storage=storage)

# Создаем базу данных пользователей 
user_dict: dict[int, dict[str, str | int | bool]] = dict()

# Создаем класс, наследуемый от StatesGroup, для группы состояний нашей FSM
class FSMFillForm(StatesGroup):
    # Создаем экземпляры класса State, последовательно
    # перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодейтсвия с пользователем
    fill_name = State()        # Состояние ожидания ввода имени
    fill_age = State()         # Состояние ожидания ввода возраста
    fill_gender = State()      # Состояние ожидания выбора пола
    upload_photo = State()     # Состояние ожидания загрузки фото
    fill_education = State()   # Состояние ожидания выбора образования
    fill_wish_news = State()   # Состояние ожидания выбора получать ли новости
    fill_town = State()
    fill_country = State()
    fill_language = State()


# Этот хэндлер будет срабатывать на команду /start вне состояний
# и предлагать перейти к заполнению анкеты, отправив команду /fillform
@dp.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    await message.answer(text='Этот бот демонстрирует работу FSM\n\n'
                              'Чтобы перейти к заполнению анкеты - '
                              'отправьте команду /fillform')
    

# Этот хэндлер будет срабатывать на команду "/cancel" в любых состояниях,
# кроме состояния по умолчанию, и отключать машину состояний
@dp.message(Command(commands='cancel'), ~StateFilter(default_state))
async def process_cancel_command_state(message: Message, state: FSMContext):
    await message.answer(text='Вы вышли из машины состояний\n\n'
                              'Чтобы снова перейти к заполнению анкеты - '
                              'отправьте команду /fillform')
    # Сбрасываем состояние
    await state.clear()


# Этот хэндлер будет срабатывать на команду "/cancel" в состоянии
# по умолчанию и сообщать, что эта команда доступна в машине состояний
@dp.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message):
    await message.answer(text='Отменять нечего. Вы вне машины состояний\n\n'
                              'Чтобы перейти к заполнению анкеты - '
                              'отправьте команду /fillform')
    

# Этот хэндлер будет срабатывать на команду /fillform
# и переводить бота в состояние ожидания ввода имени
@dp.message(Command(commands='fillform'), StateFilter(default_state))
async def process_filform_command(message: Message, state: FSMContext):
    await message.answer(text='Пожалуйста, введите ваше имя')
    # Устанавливаем состояние ожидания ввода имени
    await state.set_state(FSMFillForm.fill_name)


# Этот хэндлер будет срабатывать, если введено корректное имя
# и переводить в состояние ожидания ввода возраста
@dp.message(StateFilter(FSMFillForm.fill_name), F.text.isalpha())
async def process_name_sent(message: Message, state: FSMContext):
    # Cохраняем введенное имя в хранилище по ключу "name"
    await state.update_data(name=message.text)
    await message.answer(text='Спасибо!\n\nА теперь введите ваш возраст')
    # Устанавливаем состояние ожидания ввода возраста
    await state.set_state(FSMFillForm.fill_age)


# Этот хэндлер будет срабатывать, если во время ввода имени
# будет введено что-то некорректное
@dp.message(StateFilter(FSMFillForm.fill_name))
async def warning_not_name(message: Message):
    await message.answer(text='То, что вы отправили не похоже на имя\n\n'
                              'Пожалуйста, введите ваше имя\n\n'
                              'Если вы хотите прервать заполнение анкеты - '
                              'отправьте команду /cancel')


# Этот хэндлер будет срабатывать, если введен корректный возраст
# и переводить в состояние выбора пола
@dp.message(StateFilter(FSMFillForm.fill_age), 
            lambda x: x.text.isdigit() and 4 <= int(x.text) <= 120)
async def process_age_sent(message: Message, state: FSMContext):
    # Cохраняем возраст в хранилище по ключу "age"
    await state.update_data(age=message.text)
    # Создаем объекты инлайн-кнопок
    male_button = InlineKeyboardButton(text='Мужской', 
                                       callback_data='male')
    female_button = InlineKeyboardButton(text='Женский',
                                         callback_data='female')
    undefined_button = InlineKeyboardButton(text='Не определился',
                                            callback_data='undefined_gender')
    # Добавляем кнопки в клавиатуру (две в одном ряду и одну в другом)
    keyboard: list[list[InlineKeyboardButton]] = [[male_button, female_button],
                                                  [undefined_button]]
    # Создаем объект инлайн-клавиатуры
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    # Отправляем пользователю сообщение с клавиатурой
    await message.answer(text='Спасибо!\n\nУкажите ваш пол',
                         reply_markup=markup)
    # Устанавливаем состояние ожидания выбора пола
    await state.set_state(FSMFillForm.fill_gender)
    

# Этот хэндлер будет срабатывать на нажатие кнопки при
# выборе пола и переводить в состояние отправки фото
@dp.callback_query(StateFilter(FSMFillForm.fill_gender), Text(text=['male', 'female', 'undefined_gender']))
async def process_gender_press(callback: CallbackQuery, state: FSMContext):
    # Cохраняем пол (callback.data нажатой кнопки) в хранилище,
    # по ключу "gender"
    await state.update_data(gender=callback.data)
    # Удаляем сообщение с кнопками, потому что следующий этап - загрузка фото
    # чтобы у пользователя не было желания тыкать кнопки
    await callback.message.delete()
    await callback.message.answer(text='Спасибо! А теперь загрузите, '
                                       'пожалуйста, ваше фото')
    # Устанавливаем состояние ожидания загрузки фото
    await state.set_state(FSMFillForm.upload_photo)


# Этот хэндлер будет срабатывать, если во время выбора пола
# будет введено/отправлено что-то некорректное
@dp.message(StateFilter(FSMFillForm.fill_gender))
async def warning_not_gender(message: Message):
    await message.answer(text='Пожалуйста, пользуйтесь кнопками '
                              'при выборе пола\n\nЕсли вы хотите прервать '
                              'заполнение анкеты - отправьте команду /cancel')


# Этот хэндлер будет срабатывать, если отправлено фото
# и переводить в состояние выбора образования
@dp.message(StateFilter(FSMFillForm.upload_photo), 
            F.photo[-1].as_('largest_photo'))
async def process_photo_sent(message: Message, 
                             state: FSMContext, 
                             largest_photo: PhotoSize):
    # Cохраняем данные фото (file_unique_id и file_id) в хранилище
    # по ключам "photo_unique_id" и "photo_id"
    await state.update_data(photo_unique_id=largest_photo.file_unique_id,
                            photo_id=largest_photo.file_id)
    # Создаем объекты инлайн-кнопок
    secondary_button: InlineKeyboardButton = InlineKeyboardButton(text='Среднее',
                                                                  callback_data='secondary')
    higher_button: InlineKeyboardButton = InlineKeyboardButton(text='Высшее',
                                                               callback_data='higher')
    no_edu_button: InlineKeyboardButton = InlineKeyboardButton(text='Нету',
                                                               callback_data='no_edu')
    # Добавляем кнопки в клавиатуру (две в одном ряду и одну в другом)
    keyboard: list[list[InlineKeyboardMarkup]] = [[secondary_button, higher_button],
                                                  [no_edu_button]]
    # Создаем объект инлайн-клавиатуры
    markup: InlineKeyboardMarkup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    # Отправляем пользователю сообщение с клавиатурой
    await message.answer(text='Спасибо!\n\nУкажите ваше образование',
                         reply_markup=markup)
    # Устанавливаем состояние ожидания выбора образования
    await state.set_state(FSMFillForm.fill_education)


# Этот хэндлер будет срабатывать, если во время отправки фото
# будет введено/отправлено что-то некорректное
@dp.message(StateFilter(FSMFillForm.upload_photo))
async def warning_not_photo(message: Message):
    await message.answer(text='Пожалуйста, на этом шаге отправьте '
                              'ваше фото\n\nЕсли вы хотите прервать '
                              'заполнение анкеты - отправьте команду /cancel')


# Этот хэндлер будет срабатывать, если выбрано образование
# и переводить в состояние согласия получать новости
@dp.callback_query(StateFilter(FSMFillForm.fill_education), Text(text=['secondary', 'higher', 'no_edu']))
async def process_education_press(callback: CallbackQuery, state: FSMContext):
    # Cохраняем данные об образовании по ключу "education"
    await state.update_data(education=callback.data)
    # Создаем объекты инлайн-кнопок
    yes_button: InlineKeyboardButton = InlineKeyboardButton(text='Да',
                                                            callback_data='yes_news')
    no_button: InlineKeyboardButton = InlineKeyboardButton(text='Нет',
                                                           callback_data='no_news')
    # Добавляем кнопки в клавиатуру в один ряд
    keyboard: list[list[InlineKeyboardButton]] = [[yes_button, no_button]]
    # Создаем объект инлайн-клавиатуры
    markup: InlineKeyboardMarkup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    # Устанавливаем состояние ожидания выбора получать новости или нет   
    await callback.message.edit_text(text='Спасибо!\n\n'
                                          'Хотели бы вы получать новости?',
                                     reply_markup=markup)
    await state.set_state(FSMFillForm.fill_wish_news)


# Этот хэндлер будет срабатывать, если во время выбора образования
# будет введено/отправлено что-то некорректное
dp.message(StateFilter(FSMFillForm.fill_education))
async def warning_not_education(message: Message):
    await message.answer(text='Пожалуйста, пользуйтесь кнопками '
                              'при выборе образования\n\nЕсли вы хотите '
                              'прервать заполнение анкеты - отправьте '
                              'команду /cancel')
    

# Этот хэндлер будет срабатывать на выбор получать или
# не получать новости и выводить из машины состояний
@dp.callback_query(StateFilter(FSMFillForm.fill_wish_news), Text(text=['yes_news', 'no_news']))
async def process_wish_news_press(callback: CallbackQuery, state: FSMContext):
    # C помощью менеджера контекста сохраняем данные о
    # получении новостей по ключу "wish_news"
    await state.update_data(wish_news=callback.data == 'yes_news')
    # Просим пользователя ввести страну где он живет
    await callback.message.answer(text='Спасибо!\n\n'
                                  'Укажите в какой стране проживаете')
    # Устанавливаем состояние ожидания выбора в какой стране живет пользователь
    await state.set_state(FSMFillForm.fill_country)


# Этот хэндлер будет срабатывать на сообщение пользователя
# в какой стране он проживает
@dp.message(StateFilter(FSMFillForm.fill_country), F.text.isalpha())
async def process_country_command(message: Message, state: FSMContext):
    # Сохраняем страну пользователя под ключом 'country'
    await state.update_data(country=message.text)
    # Просим пользователя ввести город где он живет
    await message.answer(text='Отлично!\n\n'
                         'Теперь введите город в котором вы живете')
    # Устанавливаем состояние ожидания выбора в каком городе живет пользователь
    await state.set_state(FSMFillForm.fill_town)


# Этот хэндлер будет срабатывать, если во время выбора страны проживания
# будет введено/отправлено что-то некорректное
@dp.message(StateFilter(FSMFillForm.fill_country))
async def warning_not_country_sent(message: Message):
    await message.answer(text='Пожалуйста, введите корректно '
                              'вашу страну проживания\n\nЕсли вы хотите '
                              'прервать заполнение анкеты - отправьте '
                              'команду /cancel')


# Этот хэндер будет срабатывать на сообщение пользователя
# в каком городе он живет
@dp.message(StateFilter(FSMFillForm.fill_town), F.text.isalpha())
async def process_town_command(message: Message, state: FSMContext):
    # Сохраняем город пользователя под ключом 'town'
    await state.update_data(town=message.text)
    # Создаем инлайн-кнопки
    eng_button: InlineKeyboardButton = InlineKeyboardButton(text='Английский',
                                                            callback_data='Английский')
    ukr_button: InlineKeyboardButton = InlineKeyboardButton(text='Украинский',
                                                            callback_data='Украинский')
    rus_button: InlineKeyboardButton = InlineKeyboardButton(text='Русский',
                                                            callback_data='Русский')
    ger_button: InlineKeyboardButton = InlineKeyboardButton(text='Немецкий',
                                                             callback_data='Немецкий')
    # Создаем объект клавиатуры
    keyboard: list[list[InlineKeyboardButton]] = [[eng_button],
                                                  [rus_button],
                                                  [ukr_button],
                                                  [ger_button]]
    # Создаем клавиатуру
    markup: InlineKeyboardMarkup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    # Просим пользователя ввести язык на котором он общается
    await message.answer('Супер!\n\n'
                         'Остался последний шаг!'
                         'Введите язык на котором вы общаетесь',
                         reply_markup=markup)
    # Устанавливаем состояние ожидания выбора на каком языке общается пользователь
    await state.set_state(FSMFillForm.fill_language)


# Этот хэндлер будет срабатывать, если во время выбора страны проживания
# будет введено/отправлено что-то некорректное
@dp.message(StateFilter(FSMFillForm.fill_town))
async def warning_not_town_command(message: Message):
    await message.answer(text='Пожалуйста, введите корректно '
                              'ваш город проживания\n\nЕсли вы хотите '
                              'прервать заполнение анкеты - отправьте '
                              'команду /cancel')


# Этот хэндер будет срабатывать на инлайн-кнопку пользователя
# на каком языке он разговаривает
@dp.callback_query(StateFilter(FSMFillForm.fill_language), Text(text=['Английский', 'Украинский', 'РУсский', 'Немецкий']))
async def process_language_press(callback: CallbackQuery, state: FSMContext):
    # Сохраняем язык пользователя под ключом 'language'
    await state.update_data(time_registration=callback.message.date,
                            language=callback.data)
    # Добавляем в "базу данных" анкету пользователя
    # по ключу id пользователя
    user_dict[callback.from_user.id] = await state.get_data()
    # Завершаем машину состояний
    await state.clear()
    # Отправляем в чат сообщение о выходе из машины состояний
    await callback.message.edit_text(text='Спасибо! Ваши данные сохранены!\n\n'
                                          'Вы вышли из машины состояний')
    # Отправляем в чат сообщение с предложением посмотреть свою анкету
    await callback.message.answer(text='Чтобы посмотреть данные вашей '
                                       'анкеты - отправьте команду /showdata')


# Этот хэндлер будет срабатывать, если во время выбора языка
# будет введено/отправлено что-то некорректное
@dp.message(StateFilter(FSMFillForm.fill_language))
async def warning_not_language(message: Message):
    await message.answer(text='Пожалуйста, введите корректно '
                              'ваш язык на котором вы разговариваете\n\nЕсли вы хотите '
                              'прервать заполнение анкеты - отправьте '
                              'команду /cancel')


# Этот хэндлер будет срабатывать на отправку команды /showdata
# и отправлять в чат данные анкеты, либо сообщение об отсутствии данных
@dp.message(Command(commands='showdata'), StateFilter(default_state))
async def process_showdata_command(message: Message):
    # Отправляем пользователю анкету, если она есть в "базе данных"
    if message.from_user.id in user_dict:
        await message.answer_photo(
            photo=user_dict[message.from_user.id]['photo_id'],
            caption=f'Имя: {user_dict[message.from_user.id]["name"]}\n'
                    f'Возраст: {user_dict[message.from_user.id]["age"]}\n'
                    f'Пол: {user_dict[message.from_user.id]["gender"]}\n'
                    f'Образование: {user_dict[message.from_user.id]["education"]}\n'
                    f'Страна: {user_dict[message.from_user.id]["country"]}\n'
                    f'Город: {user_dict[message.from_user.id]["town"]}\n'
                    f'Разговорный язык: {user_dict[message.from_user.id]["language"]}\n'
                    f'Получать новости: {user_dict[message.from_user.id]["wish_news"]}\n'
                    f'Время регистрации: {str(user_dict[message.from_user.id]["time_registration"])[:-6]}')
    else:
        # Если анкеты пользователя в базе нет - предлагаем заполнить
        await message.answer(text='Вы еще не заполняли анкету. '
                                  'Чтобы приступить - отправьте '
                                  'команду /fillform')


# Этот хэндлер будет срабатывать на любые сообщения, кроме тех
# для которых есть отдельные хэндлеры, вне состояний
@dp.message(StateFilter(default_state))
async def send_echo(message: Message):
    await message.reply(text='Извините, моя твоя не понимать')


# Запускаем поллинг
if __name__ == '__main__':
    dp.run_polling(bot)
