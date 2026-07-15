import telebot
import requests
import json
import os
import re
import shutil
import time
import subprocess
from datetime import datetime, timedelta
from threading import Thread
from typing import List
from flask import Flask, request

# ==================== الإعدادات الأساسية ====================
API_TOKEN = "7999963241:AAHr9FpmZWzxkYBRQU_h6NkuWcAbcsFmlXA"
ADMIN_ID = 7947679527
DEVELOPER = "@ggzh9"
CHANNEL = "https://t.me/kayo_i"
OWNER_TEXT = f"👑 المطور: {DEVELOPER}\n📢 القناة: {CHANNEL}"

# ==================== إعداد Flask و Telebot ====================
app = Flask(__name__)
bot = telebot.TeleBot(API_TOKEN)

# ==================== مسارات الملفات ====================
DATA_PATH = "data/"
BACKUP_PATH = "backups/"
FILES_PATH = "files/"
os.makedirs(DATA_PATH, exist_ok=True)
os.makedirs(BACKUP_PATH, exist_ok=True)
os.makedirs(FILES_PATH, exist_ok=True)

# ==================== تحميل وحفظ البيانات ====================
def load_data(file_name: str, default: dict = None) -> dict:
    path = os.path.join(DATA_PATH, file_name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default or {}

def save_data(file_name: str, data: dict):
    path = os.path.join(DATA_PATH, file_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_all():
    save_data("bot.json", bot_data)
    save_data("app.json", app_data)
    save_data("subscription.json", subscription_data)
    save_data("statistics.json", stats_data)

# تحميل جميع البيانات
bot_data = load_data("bot.json", {})
app_data = load_data("app.json", {})
subscription_data = load_data("subscription.json", {})
stats_data = load_data("statistics.json", {"users": [], "groups": []})

# ==================== تهيئة القيم الافتراضية ====================
def init_defaults():
    if "admins" not in bot_data:
        bot_data["admins"] = [ADMIN_ID]
    if ADMIN_ID not in bot_data["admins"]:
        bot_data["admins"].append(ADMIN_ID)
    bot_data.setdefault("banned", [])
    bot_data.setdefault("promotionn", [])
    bot_data.setdefault("folder", "bots")
    bot_data.setdefault("upload", "on")
    bot_data.setdefault("check", "on")
    bot_data.setdefault("tak", "on")
    bot_data.setdefault("tawgeh", "on")
    bot_data.setdefault("bott", "on")
    bot_data.setdefault("premium", "off")
    bot_data.setdefault("VIP_button", "on")
    bot_data.setdefault("numberfiles", 7)
    bot_data.setdefault("numberban", 3)
    bot_data.setdefault("stabilizing", "off")
    bot_data.setdefault("directing", "off")
    bot_data.setdefault("radio_g_or_p", "private")
    bot_data.setdefault("from_php", {})
    bot_data.setdefault("from_json", {})
    bot_data.setdefault("from_text", {})
    bot_data.setdefault("from_py", {})
    bot_data.setdefault("from_other", {})
    bot_data.setdefault("from_ban", {})
    bot_data.setdefault("php", 0)
    bot_data.setdefault("json", 0)
    bot_data.setdefault("text", 0)
    bot_data.setdefault("py", 0)
    bot_data.setdefault("other", 0)
    bot_data.setdefault("file", 0)
    bot_data.setdefault("php_ban", 0)
    bot_data.setdefault("json_ban", 0)
    bot_data.setdefault("text_ban", 0)
    bot_data.setdefault("py_ban", 0)
    bot_data.setdefault("ban", 0)
    bot_data.setdefault("Info_uploads", {"telegram": 0, "not_telegram": 0, "curl": 0})
    app_data.setdefault("twasol", {})
    app_data.setdefault("mode", {})
    stats_data.setdefault("stats", {
        "total_users": 0,
        "total_groups": 0,
        "today": {"date": datetime.now().strftime("%Y-%m-%d"), "users": 0, "groups": 0},
        "yesterday": {"date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"), "users": 0, "groups": 0},
        "new_today": 0,
        "new_groups_today": 0,
    })

init_defaults()
save_all()

# ==================== دوال مساعدة ====================
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID or user_id in bot_data.get("admins", [])

def is_vip(user_id: int) -> bool:
    return user_id in bot_data.get("promotionn", [])

def is_banned(user_id: int) -> bool:
    return user_id in bot_data.get("banned", [])

def get_user_folder(user_id: int) -> str:
    return os.path.join(FILES_PATH, str(user_id))

def get_current_folder(user_id: int) -> str:
    return os.path.join(get_user_folder(user_id), bot_data.get("folder", "bots"))

def create_folder_if_needed(user_id: int):
    base = get_user_folder(user_id)
    os.makedirs(base, exist_ok=True)
    current = get_current_folder(user_id)
    os.makedirs(current, exist_ok=True)

def get_file_link(file_name: str, user_id: int) -> str:
    return f"https://kayo_sword.up.railway.app/{get_current_folder(user_id)}/{file_name}"

def check_file_content(content: str) -> bool:
    patterns = [
        r'H3K', r'public function create', r'.*ZipArchive.*',
        r'.*eval.*', r'.*file_put_contents.*', r'.*base64_decode.*',
        r'.*system.*', r'.*shell_exec.*', r'.*exec.*', r'.*passthru.*'
    ]
    for pat in patterns:
        if re.search(pat, content, re.IGNORECASE):
            return True
    return False

def extract_token(content: str):
    match = re.search(r'(\d{6,14}:[\w-]{35,75})', content)
    return match.group(1) if match else None

def generate_ban_message(user_id: int) -> str:
    limit = bot_data.get("numberban", 3)
    warnings = bot_data.get("from_ban", {}).get(str(user_id), 0)
    remaining = limit - warnings
    if remaining <= 0:
        return "🚫 تم حظرك نهائياً لتجاوزك عدد التحذيرات المسموح به."
    return f"⚠️ تحذير: محاولة رفع ملف مخالف.\nتبقى لديك {remaining} تحذير من {limit}."

def get_folders_list(user_id: int) -> List[str]:
    base = get_user_folder(user_id)
    if not os.path.exists(base):
        return []
    folders = []
    for root, dirs, files in os.walk(base):
        for d in dirs:
            rel = os.path.relpath(os.path.join(root, d), base)
            if rel != ".":
                folders.append(rel.replace(os.sep, " > "))
    return folders

def get_file_list(user_id: int) -> List[str]:
    base = get_user_folder(user_id)
    if not os.path.exists(base):
        return []
    items = []
    for entry in os.listdir(base):
        path = os.path.join(base, entry)
        if os.path.isdir(path):
            items.append(f"📂 {entry}")
        else:
            items.append(f"📄 {entry}")
    return items

def delete_folder_recursive(path: str) -> bool:
    if not os.path.exists(path):
        return False
    try:
        shutil.rmtree(path)
        return True
    except:
        return False

# ==================== وظيفة النسخ الاحتياطي ====================
def create_backup():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = os.path.join(BACKUP_PATH, f"backup_{timestamp}.json")
    
    all_data = {
        "bot_data": bot_data,
        "app_data": app_data,
        "subscription_data": subscription_data,
        "stats_data": stats_data,
        "timestamp": timestamp
    }
    
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    try:
        with open(backup_file, "rb") as f:
            bot.send_document(ADMIN_ID, f, caption=f"📦 نسخة احتياطية - {timestamp}")
    except:
        pass
    
    backups = sorted([f for f in os.listdir(BACKUP_PATH) if f.endswith('.json')])
    for old in backups[:-5]:
        os.remove(os.path.join(BACKUP_PATH, old))
    
    return backup_file

def restore_from_backup(backup_file: str):
    with open(backup_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    global bot_data, app_data, subscription_data, stats_data
    bot_data = data.get("bot_data", {})
    app_data = data.get("app_data", {})
    subscription_data = data.get("subscription_data", {})
    stats_data = data.get("stats_data", {"users": [], "groups": []})
    
    save_all()
    return True

# ==================== الأزرار المربعة والملونة ====================
def main_menu_keyboard(user_id: int):
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        telebot.types.InlineKeyboardButton("📤 رفع ملف", callback_data="upload_file"),
        telebot.types.InlineKeyboardButton("📁 ملفاتي", callback_data="show")
    )
    keyboard.add(
        telebot.types.InlineKeyboardButton("📁 إنشاء فولدر", callback_data="Create_folder"),
        telebot.types.InlineKeyboardButton("🎯 تعيين فولدر", callback_data="set_flowr")
    )
    keyboard.add(
        telebot.types.InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats"),
        telebot.types.InlineKeyboardButton("⭐ طلب VIP", callback_data="vip")
    )
    keyboard.add(
        telebot.types.InlineKeyboardButton("📨 الدعم الفني", callback_data="contact"),
        telebot.types.InlineKeyboardButton("🔄 تحديث", callback_data="refr")
    )
    keyboard.add(
        telebot.types.InlineKeyboardButton("👑 المطور", url="https://t.me/ggzh9"),
        telebot.types.InlineKeyboardButton("📢 القناة", url="https://t.me/kayo_i")
    )
    return keyboard

def admin_panel_keyboard():
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    
    tak_status = "✅" if bot_data.get("tak") == "on" else "❌"
    tawgeh_status = "✅" if bot_data.get("tawgeh") == "on" else "❌"
    keyboard.add(
        telebot.types.InlineKeyboardButton(f"تنبيه {tak_status}", callback_data="tak"),
        telebot.types.InlineKeyboardButton(f"توجيه {tawgeh_status}", callback_data="tawgeh")
    )
    
    bott_status = "✅" if bot_data.get("bott") == "on" else "❌"
    premium_status = "✅" if bot_data.get("premium") == "on" else "❌"
    keyboard.add(
        telebot.types.InlineKeyboardButton(f"البوت {bott_status}", callback_data="bott"),
        telebot.types.InlineKeyboardButton(f"مدفوع {premium_status}", callback_data="premium")
    )
    
    keyboard.add(
        telebot.types.InlineKeyboardButton("🔒 الحظر", callback_data="ksmblock"),
        telebot.types.InlineKeyboardButton("👥 الادمنية", callback_data="ksmadmin")
    )
    keyboard.add(
        telebot.types.InlineKeyboardButton("⭐ VIP", callback_data="ksmvip"),
        telebot.types.InlineKeyboardButton("📌 اشتراك", callback_data="eshterak")
    )
    keyboard.add(
        telebot.types.InlineKeyboardButton("📢 إذاعة", callback_data="msg"),
        telebot.types.InlineKeyboardButton("📊 إحصائيات", callback_data="statistics")
    )
    keyboard.add(
        telebot.types.InlineKeyboardButton("⚙️ إعدادات الرفع", callback_data="abdo"),
        telebot.types.InlineKeyboardButton("📦 نسخ احتياطي", callback_data="backup_menu")
    )
    keyboard.add(
        telebot.types.InlineKeyboardButton("📤 رفع بوت جديد", callback_data="upload_bot")
    )
    keyboard.add(
        telebot.types.InlineKeyboardButton("👑 المطور", url="https://t.me/ggzh9"),
        telebot.types.InlineKeyboardButton("📢 القناة", url="https://t.me/kayo_i")
    )
    return keyboard

def back_button():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="back2"))
    return keyboard

def back_to_admin():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("🔙 رجوع للوحة التحكم", callback_data="bot"))
    return keyboard

def vip_request_keyboard(user_id: int):
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("✅ قبول", callback_data=f"accept_vip:{user_id}"),
        telebot.types.InlineKeyboardButton("❌ رفض", callback_data=f"reject_vip:{user_id}")
    )
    return keyboard

# ==================== رفع بوت جديد ====================
@bot.message_handler(commands=['upload_bot'])
def upload_bot_start(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "⛔ غير مصرح")
        return
    
    msg = bot.reply_to(message, "📤 أرسل ملف البوت (bot.py) أولاً.")
    bot.register_next_step_handler(msg, process_bot_file)

def process_bot_file(message):
    if not message.document:
        bot.reply_to(message, "❌ يرجى إرسال ملف bot.py", reply_markup=back_to_admin())
        return
    
    if not message.document.file_name.endswith('.py'):
        bot.reply_to(message, "❌ يرجى إرسال ملف Python (.py)", reply_markup=back_to_admin())
        return
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        bot_file_path = os.path.join(FILES_PATH, "uploaded_bot.py")
        with open(bot_file_path, "wb") as f:
            f.write(downloaded_file)
        
        bot.reply_to(message, "✅ تم استلام ملف البوت. أرسل الآن ملف requirements.txt")
        bot.register_next_step_handler(message, process_requirements_file)
        
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)}", reply_markup=back_to_admin())

def process_requirements_file(message):
    if not message.document:
        bot.reply_to(message, "❌ يرجى إرسال ملف requirements.txt", reply_markup=back_to_admin())
        return
    
    if not message.document.file_name.endswith('.txt'):
        bot.reply_to(message, "❌ يرجى إرسال ملف requirements.txt", reply_markup=back_to_admin())
        return
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        req_file_path = os.path.join(FILES_PATH, "requirements.txt")
        with open(req_file_path, "wb") as f:
            f.write(downloaded_file)
        
        bot.reply_to(message, "⏳ جاري تثبيت المتطلبات...")
        
        result = subprocess.run(['pip', 'install', '-r', req_file_path, '--user'], 
                               capture_output=True, text=True)
        
        bot_file_path = os.path.join(FILES_PATH, "uploaded_bot.py")
        
        process = subprocess.Popen(['python3', bot_file_path], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
        
        bot.reply_to(
            message,
            f"✅ تم رفع وتشغيل البوت الجديد بنجاح!\n"
            f"📁 الملف: {bot_file_path}\n"
            f"📦 المتطلبات: {req_file_path}\n"
            f"🔄 PID: {process.pid}",
            reply_markup=back_to_admin()
        )
        
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)}", reply_markup=back_to_admin())

# ==================== أوامر البوت ====================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    create_folder_if_needed(user_id)
    
    if user_id not in stats_data["users"]:
        stats_data["users"].append(user_id)
        stats_data["stats"]["total_users"] = len(stats_data["users"])
        stats_data["stats"]["today"]["users"] += 1
        stats_data["stats"]["new_today"] += 1
        save_all()
        bot.send_message(
            ADMIN_ID,
            f"🆕 مستخدم جديد\nالايدي: {user_id}\nاليوزر: @{message.from_user.username or 'لا يوجد'}",
            parse_mode="HTML"
        )
    
    user_upload_count = sum([
        bot_data.get("from_php", {}).get(str(user_id), 0),
        bot_data.get("from_json", {}).get(str(user_id), 0),
        bot_data.get("from_text", {}).get(str(user_id), 0),
        bot_data.get("from_py", {}).get(str(user_id), 0),
        bot_data.get("from_other", {}).get(str(user_id), 0)
    ])
    total_uploads = bot_data.get("file", 0)
    total_users = stats_data["stats"]["total_users"]
    current_folder = bot_data.get("folder", "bots")
    
    if is_admin(user_id):
        msg = (
            f"<b>👋 اهلاً بك في لوحة التحكم</b>\n\n"
            f"📁 الفولدر الحالي: {current_folder}\n"
            f"📄 إجمالي الملفات: {total_uploads}\n"
            f"👥 المستخدمين: {total_users}\n\n"
            f"{OWNER_TEXT}"
        )
        bot.reply_to(message, msg, parse_mode="HTML", reply_markup=admin_panel_keyboard())
    else:
        msg = (
            f"<b>👋 اهلاً بك في بوت رفع الملفات</b>\n\n"
            f"🆔 ايديك: <code>{user_id}</code>\n"
            f"⭐ {'<b>عضو VIP</b>' if is_vip(user_id) else 'عضو عادي'}\n\n"
            f"📁 الفولدر الحالي: <b>{current_folder}</b>\n"
            f"📄 ملفاتك المرفوعة: <b>{user_upload_count}</b>\n"
            f"👥 عدد المستخدمين: <b>{total_users}</b>\n"
            f"📊 إجمالي المرفوعات: <b>{total_uploads}</b>\n\n"
            f"💡 أرسل ملفاً لرفعه على السيرفر\n\n"
            f"{OWNER_TEXT}"
        )
        bot.reply_to(message, msg, parse_mode="HTML", reply_markup=main_menu_keyboard(user_id))

# ==================== معالجات الأزرار ====================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    
    if call.data == "bot":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        msg = (
            f"<b>👋 اهلاً بك في لوحة التحكم</b>\n\n"
            f"{OWNER_TEXT}"
        )
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=admin_panel_keyboard()
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "back2":
        user_upload_count = sum([
            bot_data.get("from_php", {}).get(str(user_id), 0),
            bot_data.get("from_json", {}).get(str(user_id), 0),
            bot_data.get("from_text", {}).get(str(user_id), 0),
            bot_data.get("from_py", {}).get(str(user_id), 0),
            bot_data.get("from_other", {}).get(str(user_id), 0)
        ])
        total_uploads = bot_data.get("file", 0)
        total_users = stats_data["stats"]["total_users"]
        current_folder = bot_data.get("folder", "bots")
        
        msg = (
            f"<b>👋 اهلاً بك {call.from_user.full_name}</b>\n\n"
            f"🆔 ايديك: <code>{user_id}</code>\n"
            f"⭐ {'<b>عضو VIP</b>' if is_vip(user_id) else 'عضو عادي'}\n\n"
            f"📁 الفولدر الحالي: <b>{current_folder}</b>\n"
            f"📄 ملفاتك المرفوعة: <b>{user_upload_count}</b>\n"
            f"👥 عدد المستخدمين: <b>{total_users}</b>\n"
            f"📊 إجمالي المرفوعات: <b>{total_uploads}</b>\n\n"
            f"{OWNER_TEXT}"
        )
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(user_id)
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "upload_file":
        bot.edit_message_text(
            "📤 أرسل الملف الذي تريد رفعه.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_button()
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "my_stats":
        user_upload_count = sum([
            bot_data.get("from_php", {}).get(str(user_id), 0),
            bot_data.get("from_json", {}).get(str(user_id), 0),
            bot_data.get("from_text", {}).get(str(user_id), 0),
            bot_data.get("from_py", {}).get(str(user_id), 0),
            bot_data.get("from_other", {}).get(str(user_id), 0)
        ])
        msg = (
            f"<b>📊 إحصائياتك</b>\n\n"
            f"🆔 ايديك: <code>{user_id}</code>\n"
            f"⭐ {'عضو VIP' if is_vip(user_id) else 'عضو عادي'}\n"
            f"📁 الفولدر الحالي: {bot_data.get('folder', 'bots')}\n"
            f"📄 ملفاتك المرفوعة: <b>{user_upload_count}</b>\n"
            f"📊 إجمالي المرفوعات: <b>{bot_data.get('file', 0)}</b>\n"
            f"👥 عدد المستخدمين: <b>{stats_data['stats']['total_users']}</b>"
        )
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=back_button()
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "vip":
        bot.send_message(
            ADMIN_ID,
            f"⭐ طلب اشتراك VIP\nمن: {call.from_user.full_name}\nالايدي: {user_id}\nاليوزر: @{call.from_user.username or 'لا يوجد'}",
            parse_mode="HTML",
            reply_markup=vip_request_keyboard(user_id)
        )
        bot.edit_message_text(
            "✅ تم إرسال طلب الاشتراك إلى المطور.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_button()
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data.startswith("accept_vip:"):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        target_id = int(call.data.split(":")[1])
        if target_id not in bot_data.get("promotionn", []):
            bot_data["promotionn"].append(target_id)
            save_all()
        bot.edit_message_text(
            f"✅ تم قبول طلب VIP للمستخدم.",
            call.message.chat.id,
            call.message.message_id
        )
        bot.send_message(target_id, "✅ تم تفعيل اشتراك VIP الخاص بك! أرسل /start للبدء.")
        bot.answer_callback_query(call.id)
        return
    
    if call.data.startswith("reject_vip:"):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        target_id = int(call.data.split(":")[1])
        bot.edit_message_text(
            f"❌ تم رفض طلب VIP للمستخدم.",
            call.message.chat.id,
            call.message.message_id
        )
        bot.send_message(target_id, "❌ تم رفض طلب الاشتراك VIP الخاص بك.")
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "contact":
        msg = bot.edit_message_text(
            "📨 أرسل رسالتك للدعم الفني.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_button()
        )
        bot.register_next_step_handler(msg, process_contact)
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "refr":
        bot.edit_message_text("♻️ جاري التحديث...", call.message.chat.id, call.message.message_id)
        time.sleep(1)
        bot.edit_message_text("✅ تم التحديث بنجاح.", call.message.chat.id, call.message.message_id)
        time.sleep(1)
        if is_admin(user_id):
            msg = (
                f"<b>👋 اهلاً بك في لوحة التحكم</b>\n\n"
                f"{OWNER_TEXT}"
            )
            bot.edit_message_text(
                msg,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=admin_panel_keyboard()
            )
        else:
            user_upload_count = sum([
                bot_data.get("from_php", {}).get(str(user_id), 0),
                bot_data.get("from_json", {}).get(str(user_id), 0),
                bot_data.get("from_text", {}).get(str(user_id), 0),
                bot_data.get("from_py", {}).get(str(user_id), 0),
                bot_data.get("from_other", {}).get(str(user_id), 0)
            ])
            msg = (
                f"<b>👋 اهلاً بك {call.from_user.full_name}</b>\n\n"
                f"🆔 ايديك: <code>{user_id}</code>\n"
                f"⭐ {'<b>عضو VIP</b>' if is_vip(user_id) else 'عضو عادي'}\n\n"
                f"📁 الفولدر الحالي: <b>{bot_data.get('folder', 'bots')}</b>\n"
                f"📄 ملفاتك المرفوعة: <b>{user_upload_count}</b>\n"
                f"👥 عدد المستخدمين: <b>{stats_data['stats']['total_users']}</b>\n"
                f"📊 إجمالي المرفوعات: <b>{bot_data.get('file', 0)}</b>\n\n"
                f"{OWNER_TEXT}"
            )
            bot.edit_message_text(
                msg,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=main_menu_keyboard(user_id)
            )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "Create_folder":
        if not is_vip(user_id) and not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ هذه الميزة للمشتركين VIP فقط", show_alert=True)
            return
        msg = bot.edit_message_text(
            "📁 أرسل اسم المجلد الجديد.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_button()
        )
        bot.register_next_step_handler(msg, process_create_folder)
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "set_flowr":
        if bot_data.get("folder") == "off":
            bot.answer_callback_query(call.id, "⛔ المالك عطل هذه الميزة.", show_alert=True)
            return
        folders = get_folders_list(user_id)
        if not folders:
            bot.answer_callback_query(call.id, "⚠️ لا توجد مجلدات متاحة.", show_alert=True)
            return
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
        for folder in folders:
            keyboard.add(telebot.types.InlineKeyboardButton(f"📁 {folder}", callback_data=f"select_folder:{folder}"))
        keyboard.add(telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="back2"))
        bot.edit_message_text(
            "📁 اختر المجلد لتعيينه كفولدر رفع.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data.startswith("select_folder:"):
        selected = call.data.split(":", 1)[1]
        bot_data["folder"] = selected
        save_all()
        bot.edit_message_text(
            f"✅ تم تعيين فولدر الرفع إلى:\n<code>{selected}</code>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=back_button()
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "show":
        items = get_file_list(user_id)
        if not items:
            bot.edit_message_text(
                "📂 لا توجد ملفات أو مجلدات.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=back_button()
            )
            bot.answer_callback_query(call.id)
            return
        total_folders = sum(1 for item in items if item.startswith("📂"))
        total_files = len(items) - total_folders
        display_items = items[:15]
        text = f"<b>📁 المجلدات:</b> {total_folders}\n<b>📄 الملفات:</b> {total_files}\n\n"
        text += "\n".join(display_items)
        if len(items) > 15:
            text += "\n... (يوجد المزيد)"
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=back_button()
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "abdo":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        check_status = "✅" if bot_data.get("check") == "on" else "❌"
        upload_status = "✅" if bot_data.get("upload") == "on" else "❌"
        folder_status = "✅" if bot_data.get("folder") == "on" else "❌"
        numberfiles = bot_data.get("numberfiles", 7)
        numberban = bot_data.get("numberban", 3)
        
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            telebot.types.InlineKeyboardButton(f"فحص {check_status}", callback_data="check"),
            telebot.types.InlineKeyboardButton(f"رفع {upload_status}", callback_data="upload")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton(f"فولدرات {folder_status}", callback_data="folder")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton("🚫 المحظورين", callback_data="banall")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton(f"📄 {numberfiles}", callback_data="set_numberfiles"),
            telebot.types.InlineKeyboardButton(f"⚠️ {numberban}", callback_data="set_numberban")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="bot")
        )
        
        bot.edit_message_text(
            f"<b>⚙️ إعدادات الرفع</b>\n\n{OWNER_TEXT}",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data in ["check", "upload", "folder"]:
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        key = call.data
        bot_data[key] = "off" if bot_data.get(key) == "on" else "on"
        save_all()
        bot.answer_callback_query(call.id, f"✅ تم {'تفعيل' if bot_data[key]=='on' else 'تعطيل'}")
        handle_callbacks(call)
        return
    
    if call.data in ["set_numberfiles", "set_numberban"]:
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        label = "الملفات" if call.data == "set_numberfiles" else "التحذيرات"
        msg = bot.edit_message_text(
            f"📝 أرسل العدد الجديد لـ {label}.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_to_admin()
        )
        bot.register_next_step_handler(msg, process_set_number, call.data)
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "upload_bot":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        bot.edit_message_text(
            "📤 أرسل ملف البوت (bot.py) لرفعه وتشغيله.\n\n"
            "📌 الخطوات:\n"
            "1️⃣ أرسل ملف bot.py\n"
            "2️⃣ أرسل ملف requirements.txt\n"
            "3️⃣ سيتم التثبيت والتشغيل تلقائياً",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_to_admin()
        )
        bot.answer_callback_query(call.id)
        bot.register_next_step_handler(call.message, process_bot_file)
        return
    
    if call.data == "ksmblock":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            telebot.types.InlineKeyboardButton("🔒 حظر", callback_data="block"),
            telebot.types.InlineKeyboardButton("🔓 إلغاء حظر", callback_data="unblock")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton("📋 المحظورين", callback_data="blocks")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton("🗑 حذف الكل", callback_data="unblocks")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="bot")
        )
        bot.edit_message_text(
            "<b>🔒 قسم الحظر</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data in ["block", "unblock"]:
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        mode = "حظره" if call.data == "block" else "إلغاء حظره"
        msg = bot.edit_message_text(
            f"📝 أرسل ايدي المستخدم لـ {mode}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_to_admin()
        )
        bot.register_next_step_handler(msg, process_block_user, call.data)
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "blocks":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        banned_list = bot_data.get("banned", [])
        if not banned_list:
            text = "📭 لا يوجد محظورين."
        else:
            text = "<b>🚫 المحظورين:</b>\n" + "\n".join([f"🆔 {uid}" for uid in banned_list])
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=back_to_admin()
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "unblocks":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(
            telebot.types.InlineKeyboardButton("✅ نعم", callback_data="confirm_unblocks"),
            telebot.types.InlineKeyboardButton("❌ إلغاء", callback_data="ksmblock")
        )
        bot.edit_message_text(
            "⚠️ هل أنت متأكد من حذف جميع المحظورين؟",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "confirm_unblocks":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        bot_data["banned"] = []
        save_all()
        bot.edit_message_text(
            "✅ تم حذف جميع المحظورين.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_to_admin()
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "ksmadmin":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            telebot.types.InlineKeyboardButton("⬆️ رفع ادمن", callback_data="admins"),
            telebot.types.InlineKeyboardButton("⬇️ حذف ادمن", callback_data="unadmins")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton("📋 الادمنية", callback_data="adminss")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton("🗑 حذف الكل", callback_data="unadminss")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="bot")
        )
        bot.edit_message_text(
            "<b>👥 قسم الادمنية</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data in ["admins", "unadmins"]:
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        mode = "رفعه ادمن" if call.data == "admins" else "حذف ادمنيته"
        msg = bot.edit_message_text(
            f"📝 أرسل ايدي المستخدم لـ {mode}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_to_admin()
        )
        bot.register_next_step_handler(msg, process_admin_user, call.data)
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "adminss":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        admins = bot_data.get("admins", [])
        if not admins:
            text = "📭 لا يوجد ادمنية."
        else:
            text = "<b>👥 الادمنية:</b>\n"
            for uid in admins:
                try:
                    chat_member = bot.get_chat_member(uid, uid)
                    name = chat_member.user.full_name
                    text += f"• {name} - 🆔 {uid}\n"
                except:
                    text += f"• 🆔 {uid}\n"
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=back_to_admin()
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "unadminss":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(
            telebot.types.InlineKeyboardButton("✅ نعم", callback_data="confirm_unadminss"),
            telebot.types.InlineKeyboardButton("❌ إلغاء", callback_data="ksmadmin")
        )
        bot.edit_message_text(
            "⚠️ هل أنت متأكد من حذف جميع الادمنية؟",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "confirm_unadminss":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        bot_data["admins"] = [ADMIN_ID]
        save_all()
        bot.edit_message_text(
            "✅ تم حذف جميع الادمنية.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_to_admin()
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "ksmvip":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            telebot.types.InlineKeyboardButton("➕ إضافة VIP", callback_data="addvip"),
            telebot.types.InlineKeyboardButton("➖ حذف VIP", callback_data="removevip")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton("📋 عرض VIP", callback_data="viewvips")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton("🗑 حذف الكل", callback_data="clearvips")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="bot")
        )
        bot.edit_message_text(
            "<b>⭐ قسم VIP</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data in ["addvip", "removevip"]:
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        mode = "إضافته إلى VIP" if call.data == "addvip" else "حذفه من VIP"
        msg = bot.edit_message_text(
            f"📝 أرسل ايدي المستخدم لـ {mode}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_to_admin()
        )
        bot.register_next_step_handler(msg, process_vip_user, call.data)
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "viewvips":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        vips = bot_data.get("promotionn", [])
        if not vips:
            text = "📭 لا يوجد أعضاء VIP."
        else:
            text = "<b>⭐ أعضاء VIP:</b>\n"
            for uid in vips:
                try:
                    chat_member = bot.get_chat_member(uid, uid)
                    name = chat_member.user.full_name
                    text += f"• {name} - 🆔 {uid}\n"
                except:
                    text += f"• 🆔 {uid}\n"
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=back_to_admin()
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "clearvips":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(
            telebot.types.InlineKeyboardButton("✅ نعم", callback_data="confirm_clearvips"),
            telebot.types.InlineKeyboardButton("❌ إلغاء", callback_data="ksmvip")
        )
        bot.edit_message_text(
            "⚠️ هل أنت متأكد من حذف جميع VIP؟",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "confirm_clearvips":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        bot_data["promotionn"] = []
        save_all()
        bot.edit_message_text(
            "✅ تم حذف جميع VIP.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_to_admin()
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "eshterak":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            telebot.types.InlineKeyboardButton("➕ إضافة قناة", callback_data="esh"),
            telebot.types.InlineKeyboardButton("➖ حذف قناة", callback_data="unesh")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton("👁 عرض القنوات", callback_data="eshh")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton("🗑 حذف الكل", callback_data="uneshh")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="bot")
        )
        bot.edit_message_text(
            "<b>📌 قسم الاشتراك الإجباري</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "esh":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        msg = bot.edit_message_text(
            "📝 أرسل معرف القناة (@username)، أو ايدي القناة.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_to_admin()
        )
        bot.register_next_step_handler(msg, process_eshterak)
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "unesh":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        msg = bot.edit_message_text(
            "📝 أرسل معرف أو ايدي القناة المراد حذفها.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_to_admin()
        )
        bot.register_next_step_handler(msg, process_uneshterak)
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "eshh":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        if not subscription_data:
            text = "❌ لا توجد قنوات في الاشتراك الإجباري."
        else:
            text = "<b>📌 قنوات الاشتراك الإجباري:</b>\n"
            for ch_id, count in subscription_data.items():
                try:
                    chat = bot.get_chat(int(ch_id))
                    name = chat.title
                except:
                    name = "غير معروف"
                text += f"• {name} - العدد: {count}\n"
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=back_to_admin()
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "uneshh":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(
            telebot.types.InlineKeyboardButton("✅ نعم", callback_data="confirm_uneshh"),
            telebot.types.InlineKeyboardButton("❌ إلغاء", callback_data="eshterak")
        )
        bot.edit_message_text(
            "⚠️ هل أنت متأكد من حذف جميع قنوات الاشتراك الإجباري؟",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "confirm_uneshh":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        subscription_data.clear()
        save_all()
        bot.edit_message_text(
            "✅ تم حذف جميع القنوات.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_to_admin()
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "msg":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            telebot.types.InlineKeyboardButton("🚀 بدء الإذاعة", callback_data="start_radio")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="bot")
        )
        bot.edit_message_text(
            "<b>📢 قسم الإذاعة</b>\n\nأرسل محتوى الإذاعة (نص، صورة، فيديو، مستند).",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "start_radio":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        msg = bot.edit_message_text(
            "📨 أرسل الآن محتوى الإذاعة.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_to_admin()
        )
        bot.register_next_step_handler(msg, process_broadcast)
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "statistics":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        stats = stats_data["stats"]
        msg = (
            "<b>📊 الإحصائيات العامة</b>\n\n"
            f"👥 المستخدمون الكلي: <b>{stats['total_users']}</b>\n"
            f"📁 إجمالي الملفات: <b>{bot_data.get('file', 0)}</b>\n"
            f"🔒 المحظورين: <b>{len(bot_data.get('banned', []))}</b>\n"
            f"⭐ أعضاء VIP: <b>{len(bot_data.get('promotionn', []))}</b>\n"
            f"👑 الادمنية: <b>{len(bot_data.get('admins', []))}</b>\n"
            f"📦 النسخ الاحتياطية: <b>{len(os.listdir(BACKUP_PATH)) if os.path.exists(BACKUP_PATH) else 0}</b>"
        )
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=back_to_admin()
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "backup_menu":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            telebot.types.InlineKeyboardButton("📦 إنشاء نسخة", callback_data="create_backup")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton("📋 عرض النسخ", callback_data="list_backups")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton("🔄 استعادة نسخة", callback_data="restore_backup")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="bot")
        )
        bot.edit_message_text(
            "<b>📦 قسم النسخ الاحتياطي</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "create_backup":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        bot.edit_message_text(
            "⏳ جاري إنشاء النسخة الاحتياطية...",
            call.message.chat.id,
            call.message.message_id
        )
        backup_file = create_backup()
        bot.edit_message_text(
            f"✅ تم إنشاء النسخة الاحتياطية:\n<code>{os.path.basename(backup_file)}</code>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=back_to_admin()
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "list_backups":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        backups = sorted([f for f in os.listdir(BACKUP_PATH) if f.endswith('.json')])
        if not backups:
            text = "📭 لا توجد نسخ احتياطية."
        else:
            text = "<b>📦 النسخ الاحتياطية:</b>\n"
            for i, b in enumerate(backups, 1):
                size = os.path.getsize(os.path.join(BACKUP_PATH, b)) / 1024
                text += f"{i}. {b} - {size:.1f} كيلوبايت\n"
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=back_to_admin()
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "restore_backup":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        msg = bot.edit_message_text(
            "📤 أرسل ملف النسخة الاحتياطية (JSON) لاستعادتها.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_to_admin()
        )
        bot.register_next_step_handler(msg, process_restore_backup)
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "banall":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        banned = bot_data.get("from_ban", {})
        if not banned:
            text = "📭 لا يوجد محظورين من الرفع."
        else:
            text = "<b>🚫 المحظورين من الرفع:</b>\n"
            for uid, count in banned.items():
                text += f"• 🆔 {uid} - تحذيرات: {count}\n"
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=back_to_admin()
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data in ["tak", "tawgeh", "bott", "premium"]:
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        bot_data[call.data] = "off" if bot_data.get(call.data) == "on" else "on"
        save_all()
        bot.answer_callback_query(call.id, f"✅ تم {'تفعيل' if bot_data[call.data]=='on' else 'تعطيل'}")
        msg = (
            f"<b>👋 اهلاً بك في لوحة التحكم</b>\n\n"
            f"{OWNER_TEXT}"
        )
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=admin_panel_keyboard()
        )
        return
    
    if call.data.startswith("delete_file:"):
        _, file_name, owner_id = call.data.split(":")
        owner_id = int(owner_id)
        if user_id != owner_id and not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        file_path = os.path.join(get_current_folder(owner_id), file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            bot.answer_callback_query(call.id, "✅ تم حذف الملف", show_alert=True)
            bot.edit_message_text("🗑 تم حذف الملف.", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ الملف غير موجود", show_alert=True)
        return
    
    if call.data.startswith("delete_all:"):
        _, owner_id = call.data.split(":")
        owner_id = int(owner_id)
        if user_id != owner_id and not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        folder = get_user_folder(owner_id)
        if os.path.exists(folder):
            shutil.rmtree(folder)
            create_folder_if_needed(owner_id)
            bot.answer_callback_query(call.id, "✅ تم حذف جميع ملفاتك", show_alert=True)
            bot.edit_message_text("🗑 تم حذف جميع الملفات.", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ لا توجد ملفات", show_alert=True)
        return
    
    if call.data.startswith("up_webhook:"):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        _, file_name, owner_id = call.data.split(":")
        owner_id = int(owner_id)
        file_path = os.path.join(get_current_folder(owner_id), file_name)
        if not os.path.exists(file_path):
            bot.answer_callback_query(call.id, "❌ الملف غير موجود", show_alert=True)
            return
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        token = extract_token(content)
        if not token:
            bot.answer_callback_query(call.id, "❌ لا يوجد توكن صالح في الملف", show_alert=True)
            return
        webhook_url = get_file_link(file_name, owner_id)
        try:
            response = requests.get(f"https://api.telegram.org/bot{token}/setwebhook?url={webhook_url}")
            result = response.json()
            if result.get("ok"):
                bot.answer_callback_query(call.id, "✅ تم تعيين ويب هوك", show_alert=True)
                bot.send_message(owner_id, f"✅ تم تعيين ويب هوك بنجاح.\n{OWNER_TEXT}", parse_mode="HTML")
            else:
                bot.answer_callback_query(call.id, f"❌ فشل: {result.get('description')}", show_alert=True)
        except:
            bot.answer_callback_query(call.id, "❌ فشل في الاتصال", show_alert=True)
        return
    
    if call.data.startswith("del_webhook:"):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        _, file_name, owner_id = call.data.split(":")
        owner_id = int(owner_id)
        file_path = os.path.join(get_current_folder(owner_id), file_name)
        if not os.path.exists(file_path):
            bot.answer_callback_query(call.id, "❌ الملف غير موجود", show_alert=True)
            return
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        token = extract_token(content)
        if not token:
            bot.answer_callback_query(call.id, "❌ لا يوجد توكن صالح في الملف", show_alert=True)
            return
        try:
            response = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook")
            result = response.json()
            if result.get("ok"):
                bot.answer_callback_query(call.id, "✅ تم حذف ويب هوك", show_alert=True)
                bot.send_message(owner_id, f"✅ تم حذف ويب هوك بنجاح.\n{OWNER_TEXT}", parse_mode="HTML")
            else:
                bot.answer_callback_query(call.id, f"❌ فشل: {result.get('description')}", show_alert=True)
        except:
            bot.answer_callback_query(call.id, "❌ فشل في الاتصال", show_alert=True)
        return
    
    if call.data.startswith("info_bot:"):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ غير مصرح", show_alert=True)
            return
        _, file_name, owner_id = call.data.split(":")
        owner_id = int(owner_id)
        file_path = os.path.join(get_current_folder(owner_id), file_name)
        if not os.path.exists(file_path):
            bot.answer_callback_query(call.id, "❌ الملف غير موجود", show_alert=True)
            return
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        token = extract_token(content)
        if not token:
            bot.answer_callback_query(call.id, "❌ لا يوجد توكن صالح في الملف", show_alert=True)
            return
        try:
            response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
            result = response.json()
            if result.get("ok"):
                info = result["result"]
                msg = (
                    f"<b>🤖 معلومات البوت</b>\n"
                    f"الاسم: {info['first_name']}\n"
                    f"اليوزر: @{info.get('username', 'لا يوجد')}\n"
                    f"ايدي: {info['id']}\n"
                    f"خاص: {'عام' if info.get('can_join_groups') else 'خاص'}"
                )
                bot.send_message(user_id, msg, parse_mode="HTML")
                bot.answer_callback_query(call.id, "✅ تم إرسال المعلومات")
            else:
                bot.answer_callback_query(call.id, "❌ توكن غير صحيح", show_alert=True)
        except:
            bot.answer_callback_query(call.id, "❌ فشل في الاتصال", show_alert=True)
        return
    
    bot.answer_callback_query(call.id, "⚠️ جاري التطوير...")

# ==================== دوال معالجة الخطوات ====================
def process_contact(message):
    user_id = message.from_user.id
    text = message.text
    if not text:
        bot.reply_to(message, "❌ أرسل نص الرسالة.", reply_markup=back_button())
        return
    bot.send_message(
        ADMIN_ID,
        f"📩 رسالة من {message.from_user.full_name}\nالايدي: {user_id}\n\n{text}",
        parse_mode="HTML"
    )
    bot.reply_to(message, "✅ تم إرسال رسالتك، سيتم الرد قريباً.", reply_markup=back_button())

def process_create_folder(message):
    user_id = message.from_user.id
    folder_name = message.text.strip()
    if not folder_name:
        bot.reply_to(message, "❌ اسم المجلد لا يمكن أن يكون فارغاً.", reply_markup=back_button())
        return
    folder_path = os.path.join(get_user_folder(user_id), folder_name)
    os.makedirs(folder_path, exist_ok=True)
    bot.reply_to(
        message,
        f"✅ تم إنشاء المجلد <b>{folder_name}</b> بنجاح.",
        parse_mode="HTML",
        reply_markup=back_button()
    )

def process_set_number(message, key):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return
    text = message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        bot.reply_to(message, "⚠️ يرجى إرسال رقم صحيح موجب.", reply_markup=back_to_admin())
        return
    num = int(text)
    if key == "set_numberfiles":
        bot_data["numberfiles"] = num
    else:
        bot_data["numberban"] = num
    save_all()
    bot.reply_to(
        message,
        f"✅ تم تعيين العدد الجديد: <b>{num}</b>",
        parse_mode="HTML",
        reply_markup=back_to_admin()
    )

def process_block_user(message, mode):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return
    target_id_str = message.text.strip()
    if not re.match(r'\b\d{8,12}\b', target_id_str):
        bot.reply_to(message, "❌ ايدي غير صحيح، حاول مرة أخرى.", reply_markup=back_to_admin())
        return
    target_id = int(target_id_str)
    
    if mode == "block":
        if target_id in bot_data.get("banned", []):
            bot.reply_to(message, "⚠️ المستخدم محظور بالفعل.", reply_markup=back_to_admin())
            return
        bot_data["banned"].append(target_id)
        bot.reply_to(message, f"✅ تم حظر المستخدم.", reply_markup=back_to_admin())
    else:
        if target_id not in bot_data.get("banned", []):
            bot.reply_to(message, "⚠️ المستخدم غير محظور.", reply_markup=back_to_admin())
            return
        bot_data["banned"].remove(target_id)
        bot.reply_to(message, f"✅ تم إلغاء حظر المستخدم.", reply_markup=back_to_admin())
    save_all()

def process_admin_user(message, mode):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return
    target_id_str = message.text.strip()
    if not re.match(r'\b\d{8,12}\b', target_id_str):
        bot.reply_to(message, "❌ ايدي غير صحيح، حاول مرة أخرى.", reply_markup=back_to_admin())
        return
    target_id = int(target_id_str)
    
    if mode == "admins":
        if target_id in bot_data.get("admins", []):
            bot.reply_to(message, "⚠️ المستخدم بالفعل ادمن.", reply_markup=back_to_admin())
            return
        bot_data["admins"].append(target_id)
        bot.reply_to(message, f"✅ تم رفع المستخدم ادمن.", reply_markup=back_to_admin())
        try:
            bot.send_message(target_id, "✅ تم رفعك ادمن في البوت بواسطة المطور.")
        except:
            pass
    else:
        if target_id not in bot_data.get("admins", []):
            bot.reply_to(message, "⚠️ المستخدم ليس ادمن.", reply_markup=back_to_admin())
            return
        if target_id == ADMIN_ID:
            bot.reply_to(message, "⚠️ لا يمكن حذف المالك.", reply_markup=back_to_admin())
            return
        bot_data["admins"].remove(target_id)
        bot.reply_to(message, f"✅ تم سحب الادمن من المستخدم.", reply_markup=back_to_admin())
        try:
            bot.send_message(target_id, "❌ تم سحب الادمنية منك بواسطة المطور.")
        except:
            pass
    save_all()

def process_vip_user(message, mode):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return
    target_id_str = message.text.strip()
    if not re.match(r'\b\d{8,12}\b', target_id_str):
        bot.reply_to(message, "❌ ايدي غير صحيح، حاول مرة أخرى.", reply_markup=back_to_admin())
        return
    target_id = int(target_id_str)
    
    if mode == "addvip":
        if target_id in bot_data.get("promotionn", []):
            bot.reply_to(message, "⚠️ المستخدم بالفعل في VIP.", reply_markup=back_to_admin())
            return
        bot_data["promotionn"].append(target_id)
        bot.reply_to(message, f"✅ تم إضافة المستخدم إلى VIP.", reply_markup=back_to_admin())
        try:
            bot.send_message(target_id, "✅ تم ترقيتك إلى VIP في البوت.")
        except:
            pass
    else:
        if target_id not in bot_data.get("promotionn", []):
            bot.reply_to(message, "⚠️ المستخدم ليس في VIP.", reply_markup=back_to_admin())
            return
        bot_data["promotionn"].remove(target_id)
        bot.reply_to(message, f"✅ تم حذف المستخدم من VIP.", reply_markup=back_to_admin())
        try:
            bot.send_message(target_id, "❌ تم سحب عضوية VIP منك.")
        except:
            pass
    save_all()

def process_eshterak(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return
    text = message.text.strip()
    channel_id = None
    if text.startswith('@'):
        try:
            chat = bot.get_chat(text)
            channel_id = chat.id
        except:
            pass
    elif text.isdigit():
        channel_id = -1000000000000 + int(text)
    else:
        bot.reply_to(message, "❌ لم أتمكن من استخراج ايدي القناة، حاول مرة أخرى.", reply_markup=back_to_admin())
        return
    
    if channel_id is None:
        bot.reply_to(message, "❌ لم أتمكن من استخراج ايدي القناة، حاول مرة أخرى.", reply_markup=back_to_admin())
        return
    
    subscription_data[str(channel_id)] = 1
    save_all()
    try:
        chat = bot.get_chat(channel_id)
        name = chat.title
    except:
        name = "غير معروف"
    bot.reply_to(
        message,
        f"✅ تم إضافة القناة <b>{name}</b>.",
        parse_mode="HTML",
        reply_markup=back_to_admin()
    )

def process_uneshterak(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return
    text = message.text.strip()
    channel_id = None
    if text.startswith('@'):
        try:
            chat = bot.get_chat(text)
            channel_id = chat.id
        except:
            pass
    elif text.isdigit():
        channel_id = -1000000000000 + int(text)
    else:
        bot.reply_to(message, "❌ لم أتمكن من استخراج ايدي القناة، حاول مرة أخرى.", reply_markup=back_to_admin())
        return
    
    if channel_id is None or str(channel_id) not in subscription_data:
        bot.reply_to(message, "❌ القناة غير موجودة في قائمة الاشتراك الإجباري.", reply_markup=back_to_admin())
        return
    
    del subscription_data[str(channel_id)]
    save_all()
    bot.reply_to(
        message,
        "✅ تم حذف القناة من قائمة الاشتراك الإجباري.",
        parse_mode="HTML",
        reply_markup=back_to_admin()
    )

def process_broadcast(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return
    
    targets = stats_data["users"]
    if not targets:
        bot.reply_to(message, "❌ لا يوجد مستهدفون للإذاعة.", reply_markup=back_to_admin())
        return
    
    bot.reply_to(message, f"⏳ جاري بدء الإذاعة لـ {len(targets)} مستخدم...")
    
    succeeded = 0
    failed = 0
    
    for target in targets[:100]:
        try:
            if message.text:
                bot.send_message(target, message.text)
            elif message.photo:
                bot.send_photo(target, message.photo[-1].file_id, caption=message.caption)
            elif message.document:
                bot.send_document(target, message.document.file_id, caption=message.caption)
            elif message.video:
                bot.send_video(target, message.video.file_id, caption=message.caption)
            elif message.audio:
                bot.send_audio(target, message.audio.file_id, caption=message.caption)
            elif message.voice:
                bot.send_voice(target, message.voice.file_id, caption=message.caption)
            succeeded += 1
        except:
            failed += 1
        time.sleep(0.05)
    
    bot.reply_to(
        message,
        f"✅ اكتملت الإذاعة\n• تم الإرسال: {succeeded}\n• فشل: {failed}",
        reply_markup=back_to_admin()
    )

def process_restore_backup(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return
    
    if not message.document:
        bot.reply_to(message, "❌ يرجى إرسال ملف JSON.", reply_markup=back_to_admin())
        return
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        temp_file = os.path.join(BACKUP_PATH, "temp_restore.json")
        with open(temp_file, "wb") as f:
            f.write(downloaded_file)
        
        if restore_from_backup(temp_file):
            bot.reply_to(message, "✅ تم استعادة البيانات بنجاح!", reply_markup=back_to_admin())
        else:
            bot.reply_to(message, "❌ فشل في استعادة البيانات.", reply_markup=back_to_admin())
        
        os.remove(temp_file)
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)}", reply_markup=back_to_admin())

# ==================== رفع الملفات ====================
@bot.message_handler(content_types=['document'])
def handle_document(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.reply_to(message, "⛔ أنت محظور")
        return
    
    if bot_data.get("upload") != "on":
        bot.reply_to(message, "⛔ رفع الملفات معطل حالياً")
        return
    
    if bot_data.get("premium") == "on" and not is_admin(user_id) and not is_vip(user_id):
        bot.reply_to(message, "💰 هذا البوت مدفوع، يرجى الاشتراك VIP")
        return
    
    total_user_files = sum([
        bot_data.get("from_php", {}).get(str(user_id), 0),
        bot_data.get("from_json", {}).get(str(user_id), 0),
        bot_data.get("from_text", {}).get(str(user_id), 0),
        bot_data.get("from_py", {}).get(str(user_id), 0),
        bot_data.get("from_other", {}).get(str(user_id), 0)
    ])
    max_files = bot_data.get("numberfiles", 7)
    if total_user_files >= max_files:
        bot.reply_to(
            message,
            f"⚠️ لقد تجاوزت الحد الأقصى للملفات المسموح بها ({max_files}).",
            reply_markup=back_button()
        )
        return
    
    create_folder_if_needed(user_id)
    
    file = message.document
    file_name = file.file_name or f"file_{int(time.time())}"
    file_path = os.path.join(get_current_folder(user_id), file_name)
    
    try:
        file_info = bot.get_file(file.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(file_path, "wb") as f:
            f.write(downloaded_file)
        
        ext = file_name.split('.')[-1].lower() if '.' in file_name else 'unknown'
        if ext == 'php':
            bot_data["from_php"][str(user_id)] = bot_data["from_php"].get(str(user_id), 0) + 1
            bot_data["php"] = bot_data.get("php", 0) + 1
        elif ext == 'json':
            bot_data["from_json"][str(user_id)] = bot_data["from_json"].get(str(user_id), 0) + 1
            bot_data["json"] = bot_data.get("json", 0) + 1
        elif ext == 'py':
            bot_data["from_py"][str(user_id)] = bot_data["from_py"].get(str(user_id), 0) + 1
            bot_data["py"] = bot_data.get("py", 0) + 1
        elif ext in ['txt', 'text']:
            bot_data["from_text"][str(user_id)] = bot_data["from_text"].get(str(user_id), 0) + 1
            bot_data["text"] = bot_data.get("text", 0) + 1
        else:
            bot_data["from_other"][str(user_id)] = bot_data["from_other"].get(str(user_id), 0) + 1
            bot_data["other"] = bot_data.get("other", 0) + 1
        bot_data["file"] = bot_data.get("file", 0) + 1
        save_all()
        
        file_link = get_file_link(file_name, user_id)
        token = extract_token(downloaded_file.decode('utf-8', errors='ignore')) if ext in ['php', 'py', 'txt', 'json'] else None
        
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        if token:
            keyboard.add(
                telebot.types.InlineKeyboardButton("🔗 تعيين ويب هوك", callback_data=f"up_webhook:{file_name}:{user_id}"),
                telebot.types.InlineKeyboardButton("🔗 حذف ويب هوك", callback_data=f"del_webhook:{file_name}:{user_id}")
            )
            keyboard.add(
                telebot.types.InlineKeyboardButton("ℹ️ معلومات البوت", callback_data=f"info_bot:{file_name}:{user_id}")
            )
        keyboard.add(
            telebot.types.InlineKeyboardButton("🗑 حذف الملف", callback_data=f"delete_file:{file_name}:{user_id}"),
            telebot.types.InlineKeyboardButton("🗑 حذف الكل", callback_data=f"delete_all:{user_id}")
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="back2")
        )
        
        msg = (
            f"<b>✅ تم رفع الملف بنجاح</b>\n"
            f"📁 المسار: {bot_data.get('folder', 'bots')}\n"
            f"📄 الملف: {file_name}\n"
            f"🔗 الرابط: <code>{file_link}</code>\n"
            f"🔑 التوكن: <code>{token if token else 'لا يوجد'}</code>"
        )
        bot.reply_to(message, msg, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)}")

# ==================== التواصل مع الدعم ====================
@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/') and m.chat.type == 'private')
def forward_to_admin(message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        return
    if bot_data.get("tawgeh") == "on":
        try:
            forward = bot.forward_message(ADMIN_ID, user_id, message.message_id)
            app_data["twasol"][str(forward.message_id)] = user_id
            save_data("app.json", app_data)
        except:
            pass

# ==================== Webhook ====================
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return ''

# ==================== تشغيل البوت ====================
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 جاري تشغيل البوت...")
    print(f"👑 المطور: {DEVELOPER}")
    print(f"📢 القناة: {CHANNEL}")
    print("=" * 50)
    
    # إزالة الويب هوك القديم
    bot.remove_webhook()
    
    # تعيين الويب هوك الجديد - رابط Railway الصحيح
    WEBHOOK_URL = "https://kayo_sword.up.railway.app/webhook"
    bot.set_webhook(url=WEBHOOK_URL)
    print(f"✅ تم تعيين Webhook: {WEBHOOK_URL}")
    
    # تشغيل Flask
    app.run(host="0.0.0.0", port=5000)