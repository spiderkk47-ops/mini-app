import telebot
import json
import time
import logging
from threading import Thread
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BitcoinMonitorBot:
    def __init__(self, token, chat_id):
        self.bot = telebot.TeleBot(token)
        self.chat_id = chat_id
        self.monitoring = False
        
        # Загрузка конфигурации
        self.load_config()
        
        # Регистрация обработчиков
        self.setup_handlers()
    
    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except:
            self.config = {
                "monitoring": False,
                "last_checked": 0,
                "found_wallets": []
            }
    
    def save_config(self):
        with open('config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def setup_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def start_handler(message):
            self.bot.reply_to(message, 
                "🔐 Bitcoin Wallet Monitor Bot\n\n"
                "Доступные команды:\n"
                "/start - Запуск бота\n"
                "/monitor_start - Начать мониторинг\n"
                "/monitor_stop - Остановить мониторинг\n"
                "/status - Статус мониторинга\n"
                "/stats - Статистика\n"
                "/help - Помощь"
            )
        
        @self.bot.message_handler(commands=['monitor_start'])
        def monitor_start_handler(message):
            if not self.monitoring:
                self.monitoring = True
                self.bot.reply_to(message, "🟢 Мониторинг запущен!")
                self.start_monitoring()
            else:
                self.bot.reply_to(message, "⚠️ Мониторинг уже запущен!")
        
        @self.bot.message_handler(commands=['monitor_stop'])
        def monitor_stop_handler(message):
            if self.monitoring:
                self.monitoring = False
                self.bot.reply_to(message, "🔴 Мониторинг остановлен!")
            else:
                self.bot.reply_to(message, "⚠️ Мониторинг не запущен!")
        
        @self.bot.message_handler(commands=['status'])
        def status_handler(message):
            status = "🟢 Активен" if self.monitoring else "🔴 Остановлен"
            self.bot.reply_to(message, f"Статус мониторинга: {status}")
        
        @self.bot.message_handler(commands=['stats'])
        def stats_handler(message):
            stats_text = (
                f"📊 Статистика мониторинга:\n"
                f"• Найдено кошельков: {len(self.config.get('found_wallets', []))}\n"
                f"• Последняя проверка: {time.ctime(self.config.get('last_checked', 0))}\n"
                f"• Статус: {'🟢 Активен' if self.monitoring else '🔴 Остановлен'}"
            )
            self.bot.reply_to(message, stats_text)
    
    def check_balance(self, address):
        """Проверка баланса Bitcoin адреса"""
        try:
            # Для mainnet
            response = requests.get(f'https://blockchain.info/q/addressbalance/{address}')
            if response.status_code == 200:
                satoshis = int(response.text)
                return satoshis / 100000000  # Конвертация в BTC
        except Exception as e:
            logging.error(f"Error checking balance for {address}: {e}")
        
        return 0.0
    
    def send_wallet_alert(self, wallet_data):
        """Отправка уведомления о найденном кошельке"""
        try:
            message = (
                "🚨 **НАЙДЕН BITCOIN КОШЕЛЕК С БАЛАНСОМ!** 🚨\n\n"
                f"💰 **Баланс:** `{wallet_data['balance']:.8f} BTC`\n"
                f"📍 **Адрес:** `{wallet_data['address']}`\n"
                f"🗝️ **Приватный ключ:** `{wallet_data['private_key']}`\n"
                f"📝 **Мнемоническая фраза:** `{wallet_data['mnemonic']}`\n"
                f"⏰ **Время находки:** `{wallet_data['timestamp']}`\n\n"
                "⚠️ *Это тестовое уведомление в образовательных целях*"
            )
            
            self.bot.send_message(
                self.chat_id, 
                message, 
                parse_mode='Markdown'
            )
            logging.info(f"Alert sent for wallet with balance: {wallet_data['balance']} BTC")
            
        except Exception as e:
            logging.error(f"Error sending alert: {e}")
    
    def start_monitoring(self):
        """Запуск мониторинга в отдельном потоке"""
        def monitor():
            while self.monitoring:
                try:
                    # Здесь будет логика проверки новых кошельков
                    # В реальном приложении это будет чтение из базы данных или файла
                    
                    # Имитация находки для демонстрации
                    if len(self.config.get('found_wallets', [])) < 1:  # Только для демо
                        demo_wallet = {
                            'address': '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',  # Genesis block
                            'private_key': 'demo_private_key',
                            'mnemonic': 'demo mnemonic phrase',
                            'balance': 0.00123456,
                            'timestamp': time.ctime()
                        }
                        self.send_wallet_alert(demo_wallet)
                        self.config['found_wallets'].append(demo_wallet)
                        self.save_config()
                    
                    time.sleep(60)  # Проверка каждую минуту
                    
                except Exception as e:
                    logging.error(f"Monitoring error: {e}")
                    time.sleep(10)
        
        thread = Thread(target=monitor)
        thread.daemon = True
        thread.start()
    
    def run(self):
        """Запуск бота"""
        logging.info("Starting Bitcoin Monitor Bot...")
        try:
            self.bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Bot error: {e}")
            time.sleep(5)
            self.run()

# Конфигурация
if __name__ == "__main__":
    # Замените на ваши реальные данные
    BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    CHAT_ID = "YOUR_CHAT_ID"
    
    if BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("Пожалуйста, установите реальный BOT_TOKEN и CHAT_ID")
    else:
        bot = BitcoinMonitorBot(BOT_TOKEN, CHAT_ID)
        bot.run()
