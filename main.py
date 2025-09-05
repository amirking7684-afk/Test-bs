import os
import json
import re
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import InputPeerChannel
from pyrubi import Client as RubikaClient
import socks

# ====== تنظیمات تلگرام ======
api_id = 2040
api_hash = 'b18441a1ff607e10a989891a5462e627'
phone_number = '+989152171348'  # شماره تلگرام خودت
tg_source_channel = 'Sorkhon'   # کانال مبدا تلگرام

# ====== تنظیمات پروکسی ======
proxy = (socks.SOCKS5, '146.103.119.233', 443, True)  # (نوع، سرور، پورت، rdns)

# ====== تنظیمات روبیکا ======
rb_client = RubikaClient("riper2")
rb_target_channel = "c0CusS702bf9f47324f1db408daa6a74"
username = "📲 @League_epror"
mandatory_str = '@Sorkhon'

# ====== فیلتر کلمات ======
filter_list = [
    "اختصاصی","شبتون","کلیک","غزه","اسرائیل",
    "جنگ","Https","بخیر","جوین","طلا","هدیه","صبحتون","ترامپ"
]

# ====== مسیر فایل ذخیره‌سازی و موقت ======
downloads_base = os.path.join(os.path.expanduser("~"), "Downloads")
downloads_temp = os.path.join(downloads_base, "rb_temp")
if not os.path.exists(downloads_temp):
    os.makedirs(downloads_temp)

STATE_FILE = os.path.join(downloads_base, "last_message_telegram.json")

# ====== توابع کمکی ======
def replace_text(text: str) -> str:
    if mandatory_str not in text:
        return None
    text = text.replace(mandatory_str, username)
    text = re.sub(r'@\w+', lambda m: username if username not in text else m.group(0), text)
    text = text.replace("Join Us :", "")
    return text

def bold_except_last_tag(text: str) -> str:
    lines = text.split("\n")
    if not lines:
        return text
    if lines[-1].strip() == username:
        bolded = ["**" + line + "**" if line != "" else "" for line in lines[:-1]]
        if bolded and bolded[-1] != "":
            bolded.append("")  # خط خالی قبل تگ آخر
        bolded.append(username)
        return "\n".join(bolded)
    else:
        bolded = ["**" + line + "**" if line != "" else "" for line in lines]
        return "\n".join(bolded)

def load_last_message_id():
    if not os.path.exists(STATE_FILE):
        save_last_message_id(None)
        return None
    try:
        with open(STATE_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                save_last_message_id(None)
                return None
            data = json.loads(content)
            return data.get("last_id")
    except (json.JSONDecodeError, ValueError):
        save_last_message_id(None)
        return None

def save_last_message_id(message_id):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({"last_id": message_id}, f)
    except Exception as e:
        print("❌ خطا در ذخیره‌سازی:", e)

# ====== حلقه اصلی ======
async def main():
    tg_client = TelegramClient('user', api_id, api_hash, proxy=proxy)
    await tg_client.start(phone=phone_number)
    last_id = load_last_message_id()

    async for message in tg_client.iter_messages(tg_source_channel, limit=10, reverse=True):
        if last_id and message.id <= last_id:
            continue

        text_content = message.text or ""

        # فیلتر
        if any(word.lower() in text_content.lower() for word in filter_list):
            print(f"⛔ پست {message.id} به دلیل فیلتر ارسال نشد")
            last_id = message.id
            save_last_message_id(last_id)
            continue

        # رشته اجباری
        text_ = replace_text(text_content)
        if text_ is None:
            print(f"⛔ پست {message.id} شامل رشته اجباری نبود و ارسال نشد")
            last_id = message.id
            save_last_message_id(last_id)
            continue

        text_ = bold_except_last_tag(text_)

        # دانلود و ارسال رسانه‌ها
        if message.media:
            file_path = os.path.join(downloads_temp, f"{message.id}")
            await tg_client.download_media(message, file=file_path)
            try:
                if message.photo:
                    print(rb_client.send_image(rb_target_channel, text=text_, file=file_path))
                elif message.video:
                    print(rb_client.send_video(rb_target_channel, text=text_, file=file_path))
                else:
                    print(f"⏭ پست {message.id} شامل رسانه پشتیبانی نشده است")
            except Exception as e:
                print(f"❌ خطا در ارسال فایل {message.id}:", e)
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            if text_.strip():
                print(rb_client.send_text(rb_target_channel, text_))

        last_id = message.id
        save_last_message_id(last_id)

asyncio.run(main())