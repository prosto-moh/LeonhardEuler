import telebot
import json
import schedule
import time
import threading
from datetime import datetime, timedelta
import pytz

message = "⏰ Пора записать, что ты делаешь! Просто отправь мне сообщение."

# Настройки
with open('.env', 'r') as f:
    lines = f.readlines()
    BOT_TOKEN = lines[0].strip().split('=')[1]
    USER_ID = lines[1].strip().split('=')[1]
TIMEZONE = pytz.timezone('Europe/Moscow')

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Файл для хранения данных
DATA_FILE = "user_messages.json"

# Загрузка данных из файла
def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Сохранение данных в файл
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Получение ключа для текущей даты (в московском времени)
def get_date_key():
    now = datetime.now(TIMEZONE)
    return now.strftime("%Y-%m-%d")

# Функция отправки напоминания
def send_reminder():
    try:
        bot.send_message(USER_ID, message)
        print(f"Напоминание отправлено в {datetime.now(TIMEZONE)}")
    except Exception as e:
        print(f"Ошибка отправки напоминания: {e}")

# Функция отправки ежедневного отчета
def send_daily_report():
    try:
        # Определяем дату для отчета (вчерашний день)
        today = datetime.now(TIMEZONE)
        report_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Загружаем данные
        data = load_data()
        
        if report_date in data and data[report_date]:
            # Формируем сообщение отчета
            report_message = f"📊 Отчет за {report_date}:\n\n"
            
            for entry in data[report_date]:
                time_str = entry['time']
                message = entry['message']
                report_message += f"⏰ {time_str}: {message}\n"
            
            bot.send_message(USER_ID, report_message)
            print(f"Отчет за {report_date} отправлен")
            
            # Очищаем данные за этот день (опционально)
            # data.pop(report_date, None)
            # save_data(data)
        else:
            bot.send_message(USER_ID, f"📊 За {report_date} сообщений не было")
            print(f"Нет данных для отчета за {report_date}")
            
    except Exception as e:
        print(f"Ошибка отправки отчета: {e}")

# Настройка расписания
def setup_schedule():
    # Напоминания
    schedule.every().day.at("11:30").do(send_reminder)
    schedule.every().day.at("14:30").do(send_reminder)
    schedule.every().day.at("17:30").do(send_reminder)
    schedule.every().day.at("20:30").do(send_reminder)
    schedule.every().day.at("23:30").do(send_reminder)
    schedule.every().day.at("02:30").do(send_reminder)
    
    # Ежедневный отчет
    schedule.every().day.at("03:00").do(send_daily_report)
    
    print("Расписание настроено")

# Запуск планировщика в отдельном потоке
def run_scheduler():
    setup_schedule()
    while True:
        schedule.run_pending()
        time.sleep(1)

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if str(message.from_user.id) == USER_ID:
        # Сохраняем сообщение
        data = load_data()
        date_key = get_date_key()
        
        if date_key not in data:
            data[date_key] = []
        
        message_data = {
            'time': datetime.now(TIMEZONE).strftime("%H:%:%S"),
            'message': message.text,
            'timestamp': datetime.now(TIMEZONE).isoformat()
        }
        
        data[date_key].append(message_data)
        save_data(data)
        
        bot.reply_to(message, "✅ Сообщение сохранено!")
        print(f"Сообщение сохранено: {message.text}")

# Основная функция
def main():
    print("Бот запускается...")
    print(f"Текущее время: {datetime.now(TIMEZONE)}")
    
    # Запускаем планировщик в отдельном потоке
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Запускаем бота
    print("Бот начал работу")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    main()