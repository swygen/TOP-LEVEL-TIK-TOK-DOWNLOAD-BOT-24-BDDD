from flask import Flask
from threading import Thread
import logging

# ফ্লাস্ক অ্যাপ ইনিশিয়ালাইজেশন
app = Flask('')

# সার্ভার লগ অফ রাখা (কনসোল ক্লিন রাখার জন্য)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def home():
    return {
        "status": "Online",
        "service": "ProEarn X Bot",
        "uptime": "24/7 Active"
    }

def run():
    try:
        app.run(host='0.0.0.0', port=8080)
    except Exception as e:
        print(f"Server Error: {e}")

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()