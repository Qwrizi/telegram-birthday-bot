import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    ContextTypes, ConversationHandler, filters
)
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from bot.database import db
from bot.models import Birthday, Chat
from bot.config import Config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
GETTING_USERNAME, GETTING_DATE = range(2)

class BirthdayBot:
    def __init__(self):
        self.application = None
        self.scheduler = AsyncIOScheduler()
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        await self._save_chat(update.effective_chat)
        
        welcome_text = """
        🎉 Birthday Reminder Bot! 🎂

        Я буду напоминать о днях рождения участников!

        Команды:
        /add - Добавить участника
        /list - Показать список
        /remove - Удалить участника
        /help - Помощь

        Добавляйте участников командой /add
        """
        await update.message.reply_text(welcome_text)
    
    async def add_birthday(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать процесс добавления дня рождения"""
        await update.message.reply_text(
            "Введите username участника (например: @username):",
            reply_markup=ReplyKeyboardRemove()
        )
        return GETTING_USERNAME
    
    async def get_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получить username от пользователя"""
        username = update.message.text.strip()
        if not username.startswith('@'):
            username = '@' + username
        
        context.user_data['username'] = username
        
        await update.message.reply_text(
            f"Теперь введите дату рождения для {username} (формат: ДД.ММ.ГГГГ):"
        )
        return GETTING_DATE
    
    async def get_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получить дату рождения и сохранить"""
        try:
            date_str = update.message.text.strip()
            birth_date = datetime.strptime(date_str, "%d.%m.%Y").date()
            
            username = context.user_data['username']
            
            session = db.get_session()
            birthday = Birthday(username=username, birth_date=birth_date)
            session.add(birthday)
            session.commit()
            
            await update.message.reply_text(
                f"✅ {username} добавлен с датой рождения {birth_date.strftime('%d.%m.%Y')}"
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ\nПопробуйте снова: /add"
            )
        finally:
            session.close()
        
        return ConversationHandler.END
    
    async def list_birthdays(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать список всех дней рождения"""
        session = db.get_session()
        try:
            birthdays = session.query(Birthday).order_by(Birthday.birth_date).all()
            
            if not birthdays:
                await update.message.reply_text("📭 Список дней рождения пуст")
                return
            
            message = "🎂 Список дней рождения:\n\n"
            for bday in birthdays:
                message += f"{bday.username} - {bday.birth_date.strftime('%d.%m.%Y')}\n"
            
            await update.message.reply_text(message)
            
        finally:
            session.close()
    
    async def remove_birthday(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удалить день рождения"""
        if not context.args:
            await update.message.reply_text("Использование: /remove @username")
            return
        
        username = context.args[0]
        if not username.startswith('@'):
            username = '@' + username
        
        session = db.get_session()
        try:
            birthday = session.query(Birthday).filter(Birthday.username == username).first()
            
            if birthday:
                session.delete(birthday)
                session.commit()
                await update.message.reply_text(f"✅ {username} удален из списка")
            else:
                await update.message.reply_text(f"❌ {username} не найден в списке")
                
        finally:
            session.close()
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда помощи"""
        help_text = """
        🤖 Birthday Bot - Помощь

        Команды:
        /add - Добавить участника (запросит username и дату)
        /list - Показать всех участников
        /remove @username - Удалить участника
        /help - Эта справка

        Формат даты: ДД.ММ.ГГГГ (например: 15.12.1990)
        """
        await update.message.reply_text(help_text)
    
    async def _save_chat(self, chat):
        """Сохранить информацию о чате"""
        session = db.get_session()
        try:
            existing_chat = session.query(Chat).filter(Chat.chat_id == str(chat.id)).first()
            if not existing_chat:
                new_chat = Chat(chat_id=str(chat.id), title=chat.title)
                session.add(new_chat)
                session.commit()
                logger.info(f"Добавлен новый чат: {chat.title}")
        finally:
            session.close()
    
    async def check_birthdays(self):
        """Проверить дни рождения и отправить напоминания"""
        logger.info("Проверка дней рождения...")
        
        session = db.get_session()
        try:
            tomorrow = datetime.now() + timedelta(days=1)
            
            # Ищем дни рождения на завтра
            birthdays = session.query(Birthday).filter(
                Birthday.birth_date.day == tomorrow.day,
                Birthday.birth_date.month == tomorrow.month
            ).all()
            
            if birthdays:
                # Получаем все чаты
                chats = session.query(Chat).all()
                
                for chat in chats:
                    try:
                        message = "🎂 Завтра день рождения у:\n"
                        for bday in birthdays:
                            message += f"{bday.username}\n"
                        message += "\nНе забудьте поздравить!"
                        
                        await self.application.bot.send_message(
                            chat_id=chat.chat_id,
                            text=message
                        )
                        logger.info(f"Напоминание отправлено в чат: {chat.title}")
                        
                    except Exception as e:
                        logger.error(f"Ошибка отправки в чат {chat.chat_id}: {e}")
            
        finally:
            session.close()
    
    def setup_scheduler(self):
        """Настроить планировщик для проверки дней рождения"""
        # Проверяем каждый день в 9:00
        self.scheduler.add_job(
            self.check_birthdays,
            CronTrigger(hour=Config.REMINDER_HOUR, minute=Config.REMINDER_MINUTE),
            id='birthday_check'
        )
        self.scheduler.start()
        logger.info("Планировщик запущен")
    
    def run(self):
        """Запустить бота"""
        # Инициализация базы данных
        db.init_db()
        
        # Создание приложения
        self.application = Application.builder().token(Config.BOT_TOKEN).build()
        
        # Настройка обработчиков
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('add', self.add_birthday)],
            states={
                GETTING_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_username)],
                GETTING_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_date)],
            },
            fallbacks=[CommandHandler('cancel', self.help_command)],
        )
        
        self.application.add_handler(conv_handler)
        self.application.add_handler(CommandHandler('start', self.start))
        self.application.add_handler(CommandHandler('list', self.list_birthdays))
        self.application.add_handler(CommandHandler('remove', self.remove_birthday))
        self.application.add_handler(CommandHandler('help', self.help_command))
        
        # Запуск планировщика
        self.setup_scheduler()
        
        # Запуск бота
        logger.info("Бот запущен...")
        self.application.run_polling()

# Точка входа
if __name__ == '__main__':
    bot = BirthdayBot()
    bot.run()