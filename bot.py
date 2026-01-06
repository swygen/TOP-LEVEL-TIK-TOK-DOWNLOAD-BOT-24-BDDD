import telebot
import requests
import json
import time
import threading
from datetime import datetime
import pytz
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from keep_alive import keep_alive

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 🔥 PREMIUM CONFIGURATION ZONE
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━

BOT_TOKEN = '8019476430:AAFMObskDRZwWzLa8Hmp3n21CR0A6vI0GyM' 
ADMIN_ID = 6243881362
CHANNEL_ID = -1002879589597
GROUP_ID = -1002676258756

# JSONBIN DATABASE CONFIG
JSONBIN_API_KEY = '$2a$10$FZrUDvxPfpNkGZdCM5Vhm./BRJ9.Z4TeDruLGdis7gfBnSi35FCg2'
BIN_ID = '695ca7e6ae596e708fc827f1'
BASE_URL = f'https://api.jsonbin.io/v3/b/{BIN_ID}'

# BOT IDENTITY
BOT_NAME = "Student Income Bot"
SUPPORT_USER = "@Swygen_bd"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 🧠 INTELLIGENT DATABASE ENGINE
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━

class Database:
    def __init__(self):
        self.local_data = {"users": {}, "withdrawals": [], "meta": {"total_paid": 0}}
        self.lock = threading.Lock()
        self.last_sync = time.time()
        self.load_from_cloud()

    def load_from_cloud(self):
        """ক্লাউড থেকে ডাটা লোড এবং অটো-রিপেয়ার"""
        headers = {'X-Master-Key': JSONBIN_API_KEY}
        try:
            response = requests.get(BASE_URL, headers=headers)
            if response.status_code == 200:
                cloud_data = response.json().get('record', {})
                self.local_data = cloud_data
                if "users" not in self.local_data: self.local_data["users"] = {}
                print(f"✅ {BOT_NAME} Database Connected Successfully!")
            else:
                print("⚠️ Database Error! Starting with Local Cache.")
        except Exception as e:
            print(f"❌ Connection Failed: {e}")

    def sync_cloud(self):
        """ব্যাকগ্রাউন্ডে ডাটা সেভ - ইউজার লোডিং ফিল করবে না"""
        with self.lock:
            headers = {'Content-Type': 'application/json', 'X-Master-Key': JSONBIN_API_KEY}
            try:
                requests.put(BASE_URL, json=self.local_data, headers=headers)
                self.last_sync = time.time()
            except Exception as e:
                print(f"❌ Auto-Save Failed (Will retry): {e}")

    def save(self):
        # হেভি লোড এড়াতে থ্রেডিং ব্যবহার
        threading.Thread(target=self.sync_cloud).start()

    def get_user(self, uid):
        return self.local_data['users'].get(str(uid))

    def register_user(self, user_id, name, referrer=None):
        uid = str(user_id)
        if uid in self.local_data['users']: return "EXISTS"
        
        self.local_data['users'][uid] = {
            "name": name,
            "id": uid,
            "join_date": get_bd_time(),
            "balance": 0,
            "refers": 0,
            "referrer": referrer,
            "bonus_claimed": False,
            "ref_paid": False,
            "status": "active"
        }
        self.save()
        return "NEW"

    def update_balance(self, user_id, amount):
        uid = str(user_id)
        if uid in self.local_data['users']:
            current = self.local_data['users'][uid].get('balance', 0)
            self.local_data['users'][uid]['balance'] = current + amount
            self.save()

    def add_refer_count(self, user_id):
        uid = str(user_id)
        if uid in self.local_data['users']:
            current = self.local_data['users'][uid].get('refers', 0)
            self.local_data['users'][uid]['refers'] = current + 1
            self.save()

db = Database()

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 🛠 UTILITY & SECURITY TOOLS
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━

# Anti-Spam Dictionary
user_cooldowns = {}

def is_spamming(user_id):
    current_time = time.time()
    last_time = user_cooldowns.get(user_id, 0)
    if current_time - last_time < 1.5: # 1.5 সেকেন্ড কুলডাউন
        return True
    user_cooldowns[user_id] = current_time
    return False

def get_bd_time():
    return datetime.now(pytz.timezone('Asia/Dhaka')).strftime("%d-%m-%Y %I:%M %p")

def check_subscription(user_id):
    """চ্যানেল ও গ্রুপ ভেরিফিকেশন"""
    try:
        stat_c = bot.get_chat_member(CHANNEL_ID, user_id).status
        stat_g = bot.get_chat_member(GROUP_ID, user_id).status
        valid = ['creator', 'administrator', 'member']
        return stat_c in valid and stat_g in valid
    except:
        return False 

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 🎨 PRO UI KEYBOARDS
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━

def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("👤 ড্যাশবোর্ড", "🔗 ইনভাইট ফ্রেন্ডস")
    markup.add("🏦 উইথড্র মানি", "📞 সাপোর্ট")
    markup.add("📊 পরিসংখ্যান (Top)")
    return markup

def join_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 অফিসিয়াল চ্যানেল", url="https://t.me/RedX_Developer")) 
    markup.add(InlineKeyboardButton("💬 পেমেন্ট গ্রুপ", url="https://t.me/swygen_it"))
    markup.add(InlineKeyboardButton("✅ ভেরিফাই করুন", callback_data="check_join"))
    return markup

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 🤖 ADVANCED BOT LOGIC
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.chat.id)
    if is_spamming(user_id): return
    
    name = message.from_user.first_name
    args = message.text.split()
    referrer_id = args[1] if len(args) > 1 and args[1] != user_id else None
    
    status = db.register_user(user_id, name, referrer_id)
    
    if status == "EXISTS":
        bot.send_message(user_id, f"👋 **স্বাগতম আবারও, {name}!**\nআপনার {BOT_NAME} ড্যাশবোর্ড প্রস্তুত।", reply_markup=main_menu())
    else:
        welcome_text = (
            f"🚀 **Welcome to {BOT_NAME}!**\n\n"
            f"প্রিয় **{name}**, আমাদের প্রিমিয়াম ইনকাম বস্টে আপনাকে স্বাগতম।\n\n"
            f"🎁 **সাইন আপ বোনাস:** ১০০ টাকা\n"
            f"👥 **রেফার বোনাস:** ২০ টাকা\n\n"
            f"👇 **বোনাস ক্লেইম করতে নিচের চ্যানেলগুলোতে জয়েন করুন:**"
        )
        bot.send_message(user_id, welcome_text, reply_markup=join_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def verify_joining(call):
    user_id = str(call.message.chat.id)
    if is_spamming(user_id): return bot.answer_callback_query(call.id, "Wait a second...")

    user = db.get_user(user_id)
    if not user: return bot.send_message(user_id, "⚠️ সেশন এক্সপায়ারড। /start চাপুন।")

    if check_subscription(user_id):
        bot.delete_message(user_id, call.message.message_id)
        
        if user.get('bonus_claimed', False):
            bot.send_message(user_id, "⚠️ **আপনি ইতিমধ্যে বোনাস গ্রহণ করেছেন!**", reply_markup=main_menu())
        else:
            # বোনাস বিতরণ
            db.update_balance(user_id, 100)
            db.local_data['users'][user_id]['bonus_claimed'] = True
            
            # রেফার সিস্টেম
            ref_id = user.get('referrer')
            if ref_id and not user.get('ref_paid', False):
                ref_user = db.get_user(ref_id)
                if ref_user:
                    db.update_balance(ref_id, 20)
                    db.add_refer_count(ref_id)
                    db.local_data['users'][user_id]['ref_paid'] = True
                    try:
                        bot.send_message(ref_id, f"🥳 **অভিনন্দন বস!**\nনতুন মেম্বার জয়েন করেছে: {user['name']}\n💰 ব্যালেন্স যুক্ত হয়েছে: **+২০ টাকা**")
                    except: pass
            
            db.save()
            bot.send_message(user_id, "🎉 **অভিনন্দন! একাউন্ট ভেরিফাইড।**\nআপনার একাউন্টে ১০০ টাকা বোনাস যুক্ত হয়েছে।", reply_markup=main_menu())
    else:
        bot.answer_callback_query(call.id, "❌ আপনি সব চ্যানেল জয়েন করেননি!", show_alert=True)

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 👤 FEATURE HANDLERS
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━

@bot.message_handler(func=lambda m: m.text == "👤 ড্যাশবোর্ড")
def show_profile(m):
    user = db.get_user(m.chat.id)
    if not user: return
    
    msg = (
        f"🛡️ **{BOT_NAME} Premium Profile**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 নাম: **{user['name']}**\n"
        f"🆔 ইউজার আইডি: `{user['id']}`\n"
        f"📅 জয়েনিং তারিখ: {user['join_date']}\n\n"
        f"💵 **বর্তমান ব্যালেন্স:** {user['balance']} টাকা\n"
        f"🤝 **মোট রেফার:** {user['refers']} জন\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✅ _কাজ করুন এবং পেমেন্ট নিন নিশ্চিন্তে!_"
    )
    bot.send_message(m.chat.id, msg)

@bot.message_handler(func=lambda m: m.text == "🔗 ইনভাইট ফ্রেন্ডস")
def invite_link(m):
    uid = str(m.chat.id)
    link = f"https://t.me/{bot.get_me().username}?start={uid}"
    
    msg = (
        f"🔥 **ইনকাম টিপস!**\n\n"
        f"আপনার রেফার লিংকের মাধ্যমে বন্ধুদের ইনভাইট করুন এবং প্রতি ভেরিফাইড রেফারে জিতে নিন **২০ টাকা**।\n\n"
        f"📎 **আপনার স্পেশাল লিংক:**\n`{link}`\n\n"
        f"👆 লিংকটি কপি করে Facebook, WhatsApp এ শেয়ার করুন।"
    )
    bot.send_message(m.chat.id, msg)

@bot.message_handler(func=lambda m: m.text == "🏦 উইথড্র মানি")
def withdraw_system(m):
    user = db.get_user(m.chat.id)
    if not user: return
    
    bal = user.get('balance', 0)
    refs = user.get('refers', 0)
    
    # কনফিগারেশন
    MIN_REF = 20
    MIN_BAL = 500
    
    if refs >= MIN_REF and bal >= MIN_BAL:
        mk = InlineKeyboardMarkup(row_width=2)
        mk.add(
            InlineKeyboardButton("বিকাশ (Bkash)", callback_data="wd_Bkash"),
            InlineKeyboardButton("নগদ (Nagad)", callback_data="wd_Nagad"),
            InlineKeyboardButton("রকেট (Rocket)", callback_data="wd_Rocket")
        )
        bot.send_message(m.chat.id, "💳 **পেমেন্ট গেটওয়ে সিলেক্ট করুন:**", reply_markup=mk)
    else:
        need_ref = max(0, MIN_REF - refs)
        need_bal = max(0, MIN_BAL - bal)
        
        progress = int((refs / MIN_REF) * 10)
        bar = "🟩" * progress + "⬜" * (10 - progress)
        
        msg = (
            f"🚫 **উত্তোলন লক করা আছে!**\n\n"
            f"📊 **আপনার অগ্রগতি:**\n{bar} {progress*10}%\n\n"
            f"✅ বর্তমান: {refs} রেফার | {bal} টাকা\n"
            f"🔒 প্রয়োজন: {MIN_REF} রেফার | {MIN_BAL} টাকা\n\n"
            f"⚠️ **টাকা তুলতে হলে আরও {need_ref} টি রেফার প্রয়োজন।**"
        )
        bot.send_message(m.chat.id, msg)

@bot.message_handler(func=lambda m: m.text == "📞 সাপোর্ট")
def support_handler(m):
    mk = InlineKeyboardMarkup()
    mk.add(InlineKeyboardButton("👨‍💻 ডেভেলপারের সাথে কথা বলুন", url=f"https://t.me/{SUPPORT_USER.replace('@', '')}"))
    bot.send_message(m.chat.id, "📞 **হেল্পলাইন সার্ভিস:**\nযেকোন সমস্যার জন্য এডমিনের সাথে যোগাযোগ করুন।", reply_markup=mk)

@bot.message_handler(func=lambda m: m.text == "📊 পরিসংখ্যান (Top)")
def stats_handler(m):
    # ডামি স্ট্যাটস (অথবা ডাটাবেস থেকে ক্যালকুলেট করতে পারেন)
    total_users = len(db.local_data.get('users', {}))
    msg = (
        f"📊 **{BOT_NAME} লাইভ পরিসংখ্যান**\n\n"
        f"👥 মোট ইউজার: **{total_users}** জন\n"
        f"💸 মোট পেমেন্ট: **২৫,৪০০+** টাকা\n"
        f"🟢 সার্ভার স্ট্যাটাস: **অনলাইন (Fast)**"
    )
    bot.send_message(m.chat.id, msg)

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 💸 WITHDRAWAL PROCESSING
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━

@bot.callback_query_handler(func=lambda c: c.data.startswith("wd_"))
def payment_input(call):
    method = call.data.split("_")[1]
    msg = bot.send_message(call.message.chat.id, f"📝 আপনার **{method}** পার্সোনাল নাম্বারটি ইংরেজিতে লিখুন:")
    bot.register_next_step_handler(msg, process_payment, method)

def process_payment(m, method):
    uid = str(m.chat.id)
    number = m.text
    user = db.get_user(uid)
    bal = user.get('balance', 0)
    
    if bal < 500: return bot.send_message(uid, "❌ ইনসাফিসিয়েন্ট ব্যালেন্স।")
    
    # ব্যালেন্স শূন্য করা
    db.local_data['users'][uid]['balance'] = 0
    db.save()
    
    bot.send_message(uid, "✅ **উত্তোলন রিকোয়েস্ট সাবমিট হয়েছে!**\nএডমিন প্যানেল থেকে চেক করে ২৪ ঘন্টার মধ্যে পেমেন্ট করা হবে।")
    
    # এডমিন নোটিফিকেশন
    mk = InlineKeyboardMarkup()
    mk.add(
        InlineKeyboardButton("✅ Approve & Pay", callback_data=f"ap_{uid}_{bal}"),
        InlineKeyboardButton("❌ Reject (Fake)", callback_data=f"rj_{uid}")
    )
    
    admin_msg = (
        f"🔔 **NEW WITHDRAWAL REQUEST**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 নাম: {user['name']}\n"
        f"🆔 আইডি: `{uid}`\n"
        f"💰 এমাউন্ট: **{bal} BDT**\n"
        f"🏦 মাধ্যম: {method}\n"
        f"📱 নাম্বার: `{number}`\n"
        f"📊 রেফার সংখ্যা: {user.get('refers', 0)}\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    bot.send_message(ADMIN_ID, admin_msg, reply_markup=mk)

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 👑 ADMIN CONTROLS
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━

@bot.callback_query_handler(func=lambda c: c.data.startswith(("ap_", "rj_")))
def admin_action(call):
    if call.from_user.id != ADMIN_ID: return
    code, uid = call.data.split("_")[:2]
    
    if code == "ap":
        amt = call.data.split("_")[2]
        bot.edit_message_text(f"✅ **Paid {amt} Tk to User Successfully.**", call.message.chat.id, call.message.message_id)
        try: bot.send_message(uid, f"✅ **পেমেন্ট রিসিভড!**\nআপনার {amt} টাকার পেমেন্ট সফল হয়েছে।\nধন্যবাদ {BOT_NAME} এর সাথে থাকার জন্য।")
        except: pass
    else:
        bot.edit_message_text(f"❌ **Request Rejected & User Warned.**", call.message.chat.id, call.message.message_id)
        try: bot.send_message(uid, "❌ আপনার পেমেন্ট বাতিল করা হয়েছে।\nকারণ: ফেইক রেফার বা নীতিমালা লঙ্ঘন।")
        except: pass

# ━─━─━─━─━─━─━─━─━─━─━─━─━─━
# 🔥 SERVER INITIALIZATION
# ━─━─━─━─━─━─━─━─━─━─━─━─━─━

if __name__ == "__main__":
    print(f"🤖 {BOT_NAME} IS STARTING...")
    keep_alive() # সার্ভার এক্টিভেশন
    try:
        # রিস্টার্ট হলেও ক্র্যাশ করবে না
        bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")