import telebot
import json
import base64
import requests
import time
from datetime import datetime

TOKEN = '8183725316:AAHc7eAPEykxHHpdNvcSSUIQtzWoYtTjXrc'
CHANNEL_ID = -1003382081631
SITE_URL = 'https://yello921.gt.tc'

# Очищаем старые обновления при запуске
requests.get(f'https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true')
time.sleep(2)

bot = telebot.TeleBot(TOKEN, parse_mode='HTML')
user_sessions = {}

# ========== ФУНКЦИИ ==========

def format_price(price):
    try:
        price_float = float(price)
        price_int = int(price_float)
        return f"{price_int:,}".replace(',', ' ') + " ₽"
    except (ValueError, TypeError):
        return "0 ₽"

def create_inline_keyboard(cart_id):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data=f"confirm_{cart_id}")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{cart_id}")
    )
    return keyboard

def create_main_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("🛍️ Каталог", "🛒 Корзина")
    keyboard.row("📞 Контакты", "❓ Помощь")
    return keyboard

def decode_order_data(encoded_data):
    """Расшифровывает данные заказа из base64 (с сайта)"""
    try:
        # Добавляем padding если нужно
        padding = 4 - len(encoded_data) % 4
        if padding != 4:
            encoded_data += '=' * padding
        json_str = base64.b64decode(encoded_data).decode('utf-8')
        return json.loads(json_str)
    except Exception as e:
        print(f"❌ Ошибка декодирования: {e}")
        return None

def format_cart_message(items, total, order_number=None, customer_name=None, customer_phone=None):
    """Форматирует сообщение с корзиной"""
    msg = "🛒 <b>Корзина LOFT70</b>\n\n"
    
    if order_number:
        msg += f"📋 <b>Заказ:</b> <code>{order_number}</code>\n"
    if customer_name:
        msg += f"👤 <b>Клиент:</b> {customer_name}\n"
    if customer_phone and customer_phone != 'Не указан':
        msg += f"📞 <b>Телефон:</b> {customer_phone}\n"
    
    msg += "\n<b>📦 Товары:</b>\n"
    
    for i, item in enumerate(items, 1):
        price = float(item.get('price', item.get('product_price', 0)))
        qty = item.get('quantity', item.get('qty', 1))
        size = item.get('size', '-')
        brand = item.get('brand', '')
        name = item.get('name', item.get('product_name', 'Товар'))
        old_price = item.get('old_price')
        
        msg += f"\n{i}. <b>{brand} {name}</b>\n"
        msg += f"   💰 {format_price(price)}"
        if old_price and float(old_price) > price:
            msg += f" <s>{format_price(old_price)}</s>"
        msg += f"\n   📦 x{qty} | 📏 Размер: {size}\n"
        msg += f"   💵 <b>{format_price(price * qty)}</b>\n"
    
    msg += f"\n━━━━━━━━━━━━━━━━━━\n"
    msg += f"💰 <b>Итого: {format_price(total)}</b>\n\n"
    msg += f"📦 Доставка: <b>Бесплатно</b> (от 5 000 ₽)\n"
    msg += f"🔄 Возврат: <b>30 дней</b>\n\n"
    msg += f"<i>Подтвердите заказ — менеджер свяжется с вами</i>"
    
    return msg

def send_to_channel(message_text):
    """Отправляет сообщение в канал менеджеров"""
    try:
        bot.send_message(CHANNEL_ID, message_text, parse_mode='HTML')
        print(f"✅ Сообщение отправлено в канал")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки в канал: {e}")
        return False

# ========== ОБРАБОТЧИКИ ==========

@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    parts = message.text.split()
    encoded_data = parts[1] if len(parts) > 1 else None
    
    # Если передан заказ с сайта (base64)
    if encoded_data:
        print(f"🔍 Получены данные заказа")
        order = decode_order_data(encoded_data)
        
        if order and order.get('items'):
            items = order['items']
            total = order['total']
            order_id = order['id']
            customer = order.get('customer', '')
            phone = order.get('phone', '')
            
            print(f"✅ Заказ: {order_id}, товаров: {len(items)}, сумма: {total}")
            
            # Сохраняем в сессию
            user_sessions[chat_id] = {
                'cart_id': order_id,
                'items': items,
                'total': total,
                'customer': customer,
                'phone': phone
            }
            
            msg = format_cart_message(items, total, order_id, customer, phone)
            bot.send_message(chat_id, msg, reply_markup=create_inline_keyboard(order_id))
            
            # Уведомление в канал о новом клиенте
            try:
                chat = bot.get_chat(chat_id)
                username = chat.username if chat.username else None
                full_name = f"{chat.first_name or ''} {chat.last_name or ''}".strip()
            except:
                username = None
                full_name = "Пользователь"
            
            user_info = f"@{username}" if username else full_name
            channel_msg = f"🆕 <b>Новый клиент в боте!</b>\n\n👤 {user_info}\n🛒 Заказ: <code>{order_id}</code>\n💰 Сумма: {format_price(total)}"
            send_to_channel(channel_msg)
        else:
            bot.send_message(chat_id, "❌ Не удалось загрузить корзину\n\n🛍️ Перейдите в каталог: " + SITE_URL + "/catalog.php")
    
    # Обычный старт без параметров
    else:
        bot.send_message(
            chat_id,
            f"👋 <b>Добро пожаловать в LOFT70!</b>\n\n"
            f"Для заказа:\n"
            f"1. Перейдите на сайт\n"
            f"2. Добавьте товары в корзину\n"
            f"3. Нажмите 'Оформить через Telegram'\n\n"
            f"📍 {SITE_URL}",
            reply_markup=create_main_keyboard()
        )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    
    if call.data.startswith('confirm_'):
        cart_id = call.data.replace('confirm_', '')
        
        if chat_id in user_sessions:
            session = user_sessions[chat_id]
            order_id = f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Информация о пользователе
            try:
                chat = bot.get_chat(chat_id)
                username = chat.username if chat.username else None
                first_name = chat.first_name or ""
                last_name = chat.last_name or ""
                full_name = f"{first_name} {last_name}".strip()
            except:
                username = None
                full_name = "Пользователь"
            
            # Сообщение клиенту
            bot.send_message(chat_id, 
                f"✅ <b>ЗАКАЗ ПРИНЯТ!</b>\n\n"
                f"📋 Номер: <code>{order_id}</code>\n"
                f"💰 Сумма: {format_price(session['total'])}\n\n"
                f"<b>Что дальше?</b>\n"
                f"1. Менеджер свяжется с вами\n"
                f"2. Подтвердит детали заказа\n\n"
                f"💬 По вопросам: @yellozxc\n\n"
                f"Спасибо за покупку! 🛍️",
                parse_mode='HTML')
            
            # Формируем информацию для менеджера
            if username:
                user_text = f"👤 <b>Username:</b> @{username}\n🔗 <b>Ссылка:</b> <a href='tg://user?id={chat_id}'>Написать</a>"
            else:
                user_text = f"👤 <b>Имя:</b> {full_name}\n🆔 <b>ID:</b> <code>{chat_id}</code>\n🔗 <b>Ссылка:</b> <a href='tg://user?id={chat_id}'>Написать</a>"
            
            # Товары
            items_text = ""
            for item in session['items']:
                price = float(item.get('price', item.get('product_price', 0)))
                qty = item.get('quantity', item.get('qty', 1))
                size = item.get('size', '-')
                brand = item.get('brand', '')
                name = item.get('name', item.get('product_name', 'Товар'))
                items_text += f"   • {brand} {name} x{qty} ({size} размер) = {format_price(price * qty)}\n"
            
            # Отправляем в канал
            channel_order = f"""
🚨 <b>НОВЫЙ ЗАКАЗ!</b>

🆔 <b>Номер:</b> <code>{order_id}</code>
🛒 <b>Корзина:</b> <code>{cart_id}</code>
⏰ <b>Время:</b> {datetime.now().strftime('%H:%M:%S')}
💰 <b>Сумма:</b> {format_price(session['total'])}

<b>Клиент:</b>
{user_text}

<b>Товары:</b>
{items_text}

<b>Действия менеджера:</b>
• Нажмите на ссылку выше, чтобы написать клиенту
• Проверьте заказ
• Подтвердите наличие

<b>Статус:</b> 🔄 Ожидает обработки
"""
            send_to_channel(channel_order)
            
            del user_sessions[chat_id]
        else:
            # Если сессии нет, всё равно подтверждаем
            order_id = f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            bot.send_message(chat_id, f"✅ <b>ЗАКАЗ ПРИНЯТ!</b>\n\n📋 Номер: <code>{order_id}</code>\n\nМенеджер свяжется с вами!")
            send_to_channel(f"🚨 <b>НОВЫЙ ЗАКАЗ!</b>\n\n📋 <code>{order_id}</code>\n🛒 <code>{cart_id}</code>")
        
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        bot.answer_callback_query(call.id, "✅ Заказ подтвержден! Менеджер свяжется с вами")
    
    elif call.data.startswith('cancel_'):
        if chat_id in user_sessions:
            del user_sessions[chat_id]
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        bot.send_message(chat_id, "❌ Заказ отменен")
        bot.answer_callback_query(call.id, "❌ Заказ отменен")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    chat_id = message.chat.id
    text = message.text
    
    if text == "🛍️ Каталог":
        bot.send_message(chat_id, f"📍 {SITE_URL}/catalog.php")
    elif text == "🛒 Корзина":
        bot.send_message(chat_id, f"📍 {SITE_URL}/cart.php")
    elif text == "📞 Контакты":
        bot.send_message(chat_id, "💬 Telegram: @yellozxc\n📍 Красноярск, ул. Спандаряна, 15\n🕒 10:00–21:00")
    elif text == "❓ Помощь":
        bot.send_message(chat_id, f"❓ Для оформления заказа:\n1. Добавьте товары в корзину на сайте\n2. Нажмите 'Оформить через Telegram'\n3. Подтвердите заказ в боте\n\n📞 {SITE_URL}/support.php")
    else:
        bot.send_message(chat_id, "Используйте кнопки меню 👇 или перейдите на сайт", reply_markup=create_main_keyboard())

@bot.message_handler(commands=['test'])
def test_channel(message):
    if send_to_channel("🔔 Бот работает! Тест канала."):
        bot.reply_to(message, "✅ Тест отправлен в канал")
    else:
        bot.reply_to(message, "❌ Ошибка отправки в канал")

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    print("=" * 50)
    print("🤖 БОТ LOFT70 ЗАПУЩЕН!")
    print(f"Сайт: {SITE_URL}")
    print(f"Канал: {CHANNEL_ID}")
    print("=" * 50)
    
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            print("🔄 Перезапуск через 5 сек...")
            time.sleep(5)
