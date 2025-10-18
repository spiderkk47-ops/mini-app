import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class JSONDatabase:
    def __init__(self, filename='users.json'):
        self.filename = filename
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump({}, f)
    
    def _read_data(self):
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _write_data(self, data):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_user_data(self, user_id):
        data = self._read_data()
        user_str = str(user_id)
        if user_str not in data:
            data[user_str] = {
                'balance': 0,
                'total_earned': 0,
                'clicks': 0,
                'referrals': [],
                'referrer': None,
                'ads_watched': 0
            }
            self._write_data(data)
        return data[user_str]
    
    def update_balance(self, user_id, amount):
        data = self._read_data()
        user_str = str(user_id)
        
        if user_str in data:
            data[user_str]['balance'] += amount
            data[user_str]['total_earned'] += amount
        else:
            data[user_str] = {
                'balance': amount,
                'total_earned': amount,
                'clicks': 0,
                'referrals': [],
                'referrer': None,
                'ads_watched': 0
            }
        
        self._write_data(data)
        return data[user_str]['balance']
    
    def add_click(self, user_id):
        data = self._read_data()
        user_str = str(user_id)
        if user_str in data:
            data[user_str]['clicks'] += 1
            self._write_data(data)
            return data[user_str]['clicks']
        return 0
    
    def add_referral(self, user_id, referrer_id):
        data = self._read_data()
        user_str = str(user_id)
        referrer_str = str(referrer_id)
        
        if user_str in data and referrer_str in data:
            if user_str not in data[referrer_str]['referrals']:
                data[referrer_str]['referrals'].append(user_str)
                data[user_str]['referrer'] = referrer_str
                self._write_data(data)
                return True
        return False
    
    def add_ad_watch(self, user_id):
        data = self._read_data()
        user_str = str(user_id)
        if user_str in data:
            data[user_str]['ads_watched'] += 1
            self._write_data(data)
            return data[user_str]['ads_watched']
        return 0

db = JSONDatabase()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user_data(user_id)
    
    # Проверяем реферальную систему
    if context.args:
        referrer_id = int(context.args[0])
        if referrer_id != user_id:
            db.add_referral(user_id, referrer_id)
            # Награда рефереру
            db.update_balance(referrer_id, 50)
    
    # URL для мини-приложения (замените на ваш)
    web_app_url = "https://your-username.github.io/clicker-app/index.html"
    
    keyboard = [
        [InlineKeyboardButton("🎮 Начать игру", web_app={'url': web_app_url})],
        [InlineKeyboardButton("💰 Мой баланс", callback_data='balance'),
         InlineKeyboardButton("👥 Реф система", callback_data='referral')],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Добро пожаловать в Clicker Game!\n\n"
        f"💰 Ваш баланс: {user_data['balance']} монет\n"
        f"🎯 Всего кликов: {user_data['clicks']}\n"
        f"📺 Просмотрено рекламы: {user_data['ads_watched']}\n\n"
        f"Нажмите '🎮 Начать игру' чтобы открыть кликер!",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user_data = db.get_user_data(user_id)
    
    if query.data == 'balance':
        text = (f"💰 Ваш баланс: {user_data['balance']} монет\n"
                f"🏆 Всего заработано: {user_data['total_earned']} монет\n"
                f"🎯 Кликов: {user_data['clicks']}\n"
                f"📺 Рекламы: {user_data['ads_watched']}")
        await query.answer(text, show_alert=True)
    
    elif query.data == 'referral':
        ref_count = len(user_data['referrals'])
        ref_link = f"https://t.me/{(await context.bot.get_me()).username}?start={user_id}"
        text = (f"👥 Реферальная система\n\n"
                f"🔗 Ваша ссылка:\n{ref_link}\n\n"
                f"👥 Приглашено: {ref_count} человек\n"
                f"💰 Бонус за приглашение: 50 монет")
        await query.answer(text, show_alert=True)
    
    elif query.data == 'help':
        text = ("ℹ️ Помощь\n\n"
                "🎮 Кликер - кликайте по монете для заработка\n"
                "👥 Реф система - приглашайте друзей\n"
                "📺 Реклама - смотрите рекламу за монеты\n\n"
                "По вопросам: @support")
        await query.answer(text, show_alert=True)

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        
        if data.get('type') == 'click':
            coins_per_click = data.get('coins', 1)
            new_balance = db.update_balance(user_id, coins_per_click)
            clicks = db.add_click(user_id)
            
            await update.message.reply_text(
                f"🪙 +{coins_per_click} монет!\n"
                f"💰 Баланс: {new_balance} монет\n"
                f"🎯 Всего кликов: {clicks}"
            )
        
        elif data.get('type') == 'ad_watched':
            reward = data.get('reward', 15)
            new_balance = db.update_balance(user_id, reward)
            ads_watched = db.add_ad_watch(user_id)
            
            await update.message.reply_text(
                f"📺 +{reward} монет за рекламу!\n"
                f"💰 Баланс: {new_balance} монет\n"
                f"🎬 Всего рекламы: {ads_watched}"
            )
            
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("❌ Ошибка обработки данных")

def main():
    application = Application.builder().token("8434490262:AAF1qCQr9Mx_Q7RBKrAQDFWi7YK5tSRbB8g").build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    
    print("🟢 Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()