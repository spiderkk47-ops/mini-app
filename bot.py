import logging
import json
import os
import asyncio
import random
from typing import Dict, Any, List
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
                'diamonds': 0,
                'total_earned': 0,
                'clicks': 0,
                'referrals': [],
                'referrer': None,
                'ads_watched': 0,
                'click_power': 1,
                'auto_click_level': 0,
                'nft_collection': [],
                'language': 'RU',
                'pvp_wins': 0,
                'pvp_losses': 0
            }
            self._write_data(data)
        return data[user_str]
    
    def update_balance(self, user_id, amount):
        data = self._read_data()
        user_str = str(user_id)
        
        if user_str in data:
            data[user_str]['balance'] += amount
            if amount > 0:
                data[user_str]['total_earned'] += amount
        else:
            data[user_str] = self.get_user_data(user_id)
        
        self._write_data(data)
        return data[user_str]['balance']
    
    def update_diamonds(self, user_id, amount):
        data = self._read_data()
        user_str = str(user_id)
        
        if user_str in data:
            data[user_str]['diamonds'] += amount
            self._write_data(data)
            return data[user_str]['diamonds']
        return 0
    
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
    
    def update_language(self, user_id, language):
        data = self._read_data()
        user_str = str(user_id)
        if user_str in data:
            data[user_str]['language'] = language
            self._write_data(data)
            return True
        return False
    
    def add_nft(self, user_id, nft_id):
        data = self._read_data()
        user_str = str(user_id)
        if user_str in data:
            if nft_id not in data[user_str]['nft_collection']:
                data[user_str]['nft_collection'].append(nft_id)
                self._write_data(data)
                return True
        return False
    
    def update_pvp_stats(self, user_id, won=True):
        data = self._read_data()
        user_str = str(user_id)
        if user_str in data:
            if won:
                data[user_str]['pvp_wins'] += 1
            else:
                data[user_str]['pvp_losses'] += 1
            self._write_data(data)
            return True
        return False

# Инициализация базы данных
db = JSONDatabase()

# Система PVP матчей
pvp_queue = []
active_battles = {}

# NFT данные
NFT_COLLECTION = {
    1: {"name": "Крипто-Воин", "price": 5, "attack": 15, "health": 100, "image": "⚔️"},
    2: {"name": "Биткоин-Дракон", "price": 10, "attack": 25, "health": 120, "image": "🐲"},
    3: {"name": "Эфириум-Маг", "price": 8, "attack": 20, "health": 90, "image": "🧙"},
    4: {"name": "Сатоши-Ниндзя", "price": 12, "attack": 30, "health": 80, "image": "🥷"},
    5: {"name": "Альткоин-Рыцарь", "price": 7, "attack": 18, "health": 110, "image": "🛡️"},
    6: {"name": "Мемкоин-Шут", "price": 3, "attack": 10, "health": 70, "image": "🤡"}
}

# Тексты на разных языках
TEXTS = {
    'RU': {
        'welcome': '👋 Добро пожаловать в Zephurium Game!',
        'balance': '💰 Баланс: {} монет',
        'diamonds': '💎 Алмазы: {}',
        'clicks': '🎯 Кликов: {}',
        'ads_watched': '📺 Рекламы: {}',
        'start_game': '🎮 Начать игру',
        'my_balance': '💰 Мой баланс',
        'referral_system': '👥 Реф система',
        'help': 'ℹ️ Помощь'
    },
    'ENG': {
        'welcome': '👋 Welcome to Zephurium Game!',
        'balance': '💰 Balance: {} coins',
        'diamonds': '💎 Diamonds: {}',
        'clicks': '🎯 Clicks: {}',
        'ads_watched': '📺 Ads: {}',
        'start_game': '🎮 Start Game',
        'my_balance': '💰 My Balance',
        'referral_system': '👥 Referral',
        'help': 'ℹ️ Help'
    },
    'DE': {
        'welcome': '👋 Willkommen bei Zephurium Game!',
        'balance': '💰 Guthaben: {} Münzen',
        'diamonds': '💎 Diamanten: {}',
        'clicks': '🎯 Klicks: {}',
        'ads_watched': '📺 Werbung: {}',
        'start_game': '🎮 Spiel starten',
        'my_balance': '💰 Mein Guthaben',
        'referral_system': '👥 Empfehlungen',
        'help': 'ℹ️ Hilfe'
    }
}

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
    
    # URL для мини-приложения
    web_app_url = "https://spiderkk47-ops.github.io/mini-app/mini-app.html"
    
    texts = TEXTS[user_data.get('language', 'RU')]
    
    keyboard = [
        [InlineKeyboardButton(texts['start_game'], web_app={'url': web_app_url})],
        [InlineKeyboardButton(texts['my_balance'], callback_data='balance'),
         InlineKeyboardButton(texts['referral_system'], callback_data='referral')],
        [InlineKeyboardButton(texts['help'], callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"{texts['welcome']}\n\n"
        f"{texts['balance'].format(user_data['balance'])}\n"
        f"{texts['diamonds'].format(user_data['diamonds'])}\n"
        f"{texts['clicks'].format(user_data['clicks'])}\n"
        f"{texts['ads_watched'].format(user_data['ads_watched'])}\n\n"
        f"Нажмите '{texts['start_game']}' чтобы открыть игру!",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user_data = db.get_user_data(user_id)
    texts = TEXTS[user_data.get('language', 'RU')]
    
    if query.data == 'balance':
        text = (f"💰 {texts['balance'].format(user_data['balance'])}\n"
                f"💎 {texts['diamonds'].format(user_data['diamonds'])}\n"
                f"🏆 Всего заработано: {user_data['total_earned']} монет\n"
                f"🎯 {texts['clicks'].format(user_data['clicks'])}\n"
                f"📺 {texts['ads_watched'].format(user_data['ads_watched'])}")
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
                "🎮 Zephurium Game - игра с крипто-тематикой\n"
                "👥 Реф система - приглашайте друзей\n"
                "📺 Реклама - смотрите рекламу за монеты\n"
                "💎 Алмазы - премиальная валюта\n"
                "⚔️ PVP - сражения с другими игроками\n\n"
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
        
        elif data.get('type') == 'language_change':
            language = data.get('language', 'RU')
            db.update_language(user_id, language)
            await update.message.reply_text(f"🌐 Язык изменен на {language}")
        
        elif data.get('type') == 'exchange':
            amount = data.get('amount', 0)
            direction = data.get('direction', 'coins_to_diamonds')
            
            user_data = db.get_user_data(user_id)
            
            if direction == 'coins_to_diamonds':
                # Обмен монет на алмазы (100000:1)
                coins_needed = amount * 100000
                if user_data['balance'] >= coins_needed:
                    db.update_balance(user_id, -coins_needed)
                    db.update_diamonds(user_id, amount)
                    await update.message.reply_text(
                        f"💱 Обмен успешен!\n"
                        f"💎 Получено: {amount} алмазов\n"
                        f"💰 Списано: {coins_needed} монет"
                    )
                else:
                    await update.message.reply_text("❌ Недостаточно монет для обмена")
            
            elif direction == 'diamonds_to_coins':
                # Обмен алмазов на монеты (1:100000)
                diamonds_needed = amount
                if user_data['diamonds'] >= diamonds_needed:
                    db.update_diamonds(user_id, -diamonds_needed)
                    db.update_balance(user_id, amount * 100000)
                    await update.message.reply_text(
                        f"💱 Обмен успешен!\n"
                        f"💰 Получено: {amount * 100000} монет\n"
                        f"💎 Списано: {amount} алмазов"
                    )
                else:
                    await update.message.reply_text("❌ Недостаточно алмазов для обмена")
        
        elif data.get('type') == 'buy_nft':
            nft_id = data.get('nft_id')
            nft_data = NFT_COLLECTION.get(nft_id)
            
            if nft_data:
                user_data = db.get_user_data(user_id)
                if user_data['diamonds'] >= nft_data['price']:
                    db.update_diamonds(user_id, -nft_data['price'])
                    db.add_nft(user_id, nft_id)
                    await update.message.reply_text(
                        f"🎉 NFT приобретено!\n"
                        f"🖼️ {nft_data['image']} {nft_data['name']}\n"
                        f"⚔️ Атака: {nft_data['attack']}\n"
                        f"❤️ Здоровье: {nft_data['health']}\n"
                        f"💎 Списано: {nft_data['price']} алмазов"
                    )
                else:
                    await update.message.reply_text("❌ Недостаточно алмазов")
        
        elif data.get('type') == 'pvp_result':
            battle_id = data.get('battle_id')
            result = data.get('result')  # 'win' or 'lose'
            
            if result == 'win':
                db.update_balance(user_id, 2500)
                db.update_diamonds(user_id, 0.01)
                db.update_pvp_stats(user_id, won=True)
                await update.message.reply_text(
                    "🎉 Вы выиграли битву!\n"
                    "💎 +0.01 алмаза\n"
                    "💰 +2500 монет"
                )
            else:
                db.update_pvp_stats(user_id, won=False)
                await update.message.reply_text("💔 Вы проиграли битву")
            
    except Exception as e:
        logging.error(f"Error processing web app data: {e}")
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