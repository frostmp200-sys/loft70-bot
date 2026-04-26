import telebot
import json
import base64

TOKEN = '8183725316:AAHc7eAPEykxHHpdNvcSSUIQtzWoYtTjXrc'
CHANNEL_ID = -1003382081631
SITE_URL = 'https://yello921.gt.tc'

bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

def format_price(price):
    try:
        return f"{int(float(price)):,}".replace(',', ' ') + " ₽"
    except:
        return "0 ₽"

def get_main_menu():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("🛍️ Каталог", "🛒 Корзина")
    keyboard.row("📞 Контакты", "❓ Помощь")
    return keyboard

def get_order_buttons(order_id):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton("✅ Подтвердить заказ", callback_data=f"confirm_{order_id}"),
        telebot.types.InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{order_id}")
    )
    return keyboard

def decode_order_data(encoded_data):
    try:
        json_str = base64.b64decode(encoded_data).decode('utf-8')
        return json.loads(json_str)
    except:
        return None

def format_order_message(order):
    items = order.get('items', [])
    total = order.get('total', 0)
    
    msg = "🛒 <b>КОРЗИНА LOFT70</b>\n\n"
    msg += f"📋 <b>Заказ:</b> <code>{order['id']}</code>\n"
    msg += f"👤 <b>Клиент:</b> {order.get('customer', 'Не указан')}\n"
    msg += f"📞 <b>Телефон:</b> {order.get('phone', 'Не указан')}\n\n"
    msg += "<b>📦 Товары:</b>\n"
    
    for i, item in enumerate(items, 1):
        price = float(item['price'])
        qty = item.get('qty', 1)
        size = item.get('size', '-')
        brand = item.get('brand', '')
        name = item.get('name', 'Товар')
        
        msg += f"\n{i}. <b>{brand} {name}</b>\n"
        msg += f"   💰 {format_price(price)} | 📦 x{qty} | 📏 {size}\n"
        msg += f"   💵 <b>{format_price(price * qty)}</b>\n"
    
    msg += f"\n━━━━━━━━━━━━━━━━━━\n"
    msg += f"💰 <b>ИТОГО: {format_price(total)}</b>\n\n"
    msg += "<i>✅ Подтвердите заказ или ❌ отмените</i>"
    
    return msg

@bot.message_handler(commands=['start'])
def start_handler(message):
    parts = message.text.split()
    encoded_data = parts[1] if len(parts) > 1 else None
    
    if encoded_data:
        order = decode_order_data(encoded_data)
        if order and order.get('items'):
            msg = format_order_message(order)
            bot.send_message(message.chat.id, msg, reply_markup=get_order_buttons(order['id']))
        else:
            bot.send_message(message.chat.id, "❌ Корзина не найдена")
    else:
        welcome = f"👋 <b>Добро пожаловать в LOFT70!</b>\n\n🛍️ {SITE_URL}/catalog.php\n🛒 {SITE_URL}/cart.php"
        bot.send_message(message.chat.id, welcome, reply_markup=get_main_menu())

@bot.message_handler(func=lambda msg: msg.text in ['🛍️ Каталог', '🛒 Корзина', '📞 Контакты', '❓ Помощь'])
def menu_handler(message):
    if message.text == '🛍️ Каталог':
        bot.send_message(message.chat.id, f"📍 {SITE_URL}/catalog.php")
    elif message.text == '🛒 Корзина':
        bot.send_message(message.chat.id, f"📍 {SITE_URL}/cart.php")
    elif message.text == '📞 Контакты':
        bot.send_message(message.chat.id, "💬 @yellozxc\n📍 Красноярск\n📞 8-800-555-35-35")
    elif message.text == '❓ Помощь':
        bot.send_message(message.chat.id, f"❓ {SITE_URL}/faq.php")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    
    if call.data.startswith('confirm_'):
        order_id = call.data.replace('confirm_', '')
        user = call.from_user
        name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        
        bot.send_message(chat_id, "✅ <b>ЗАКАЗ ПРИНЯТ!</b>\n\n🔜 Менеджер свяжется с вами\nСпасибо! 🛍️")
        
        channel_msg = f"🚨 <b>НОВЫЙ ЗАКАЗ!</b>\n\n📋 <code>{order_id}</code>\n👤 {name}\n🔗 <a href='tg://user?id={chat_id}'>Написать</a>"
        try:
            bot.send_message(CHANNEL_ID, channel_msg)
        except:
            pass
        bot.answer_callback_query(call.id, "✅ Подтвержден!")
    
    elif call.data.startswith('cancel_'):
        bot.send_message(chat_id, "❌ Заказ отменён")
        bot.answer_callback_query(call.id, "❌ Отменён")

print("🤖 Бот запущен!")
bot.infinity_polling()
