import json
import threading
import time
import os
import random
import re
import requests
import sys
from dotenv import load_dotenv
from datetime import datetime
from colorama import init, Fore, Style

# Inisialisasi colorama
init(autoreset=True)
load_dotenv()

colors = {
    "cyan": Fore.CYAN,
    "yellow": Fore.YELLOW,
    "red": Fore.RED,
    "green": Fore.GREEN,
    "magenta": Fore.MAGENTA,
    "blue": Fore.BLUE,
    "white": Fore.WHITE,
    "gray": Fore.LIGHTBLACK_EX,
    "bold": Style.BRIGHT,
    "reset": Style.RESET_ALL
}

logger = {
    "info": lambda msg: print(f"{colors['cyan']}[i] {msg}{colors['reset']}"),
    "warn": lambda msg: print(f"{colors['yellow']}[!] {msg}{colors['reset']}"),
    "error": lambda msg: print(f"{colors['red']}[x] {msg}{colors['reset']}"),
    "success": lambda msg: print(f"{colors['green']}[+] {msg}{colors['reset']}"),
    "loading": lambda msg: print(f"{colors['magenta']}[*] {msg}{colors['reset']}"),
    "step": lambda msg: print(f"{colors['blue']}[>] {colors['bold']}{msg}{colors['reset']}"),
    "critical": lambda msg: print(f"{colors['red']}{colors['bold']}[FATAL] {msg}{colors['reset']}"),
    "summary": lambda msg: print(f"{colors['green']}{colors['bold']}[SUMMARY] {msg}{colors['reset']}"),
    "banner": lambda: print(
        f"\n{colors['blue']}{colors['bold']}╔═════════════════════════════════════════╗{colors['reset']}\n"
        f"{colors['blue']}{colors['bold']}║     🍉 19Seniman From Insider    🍉      ║{colors['reset']}\n"
        f"{colors['blue']}{colors['bold']}╚═════════════════════════════════════════╝{colors['reset']}\n"
    ),
    "section": lambda msg: print(
        f"\n{colors['gray']}{'─'*50}{colors['reset']}\n"
        f"{colors['white']}{colors['bold']} {msg} {colors['reset']}\n"
        f"{colors['gray']}{'─'*50}{colors['reset']}\n"
    ),
    "countdown": lambda msg: sys.stdout.write(f"\r{colors['blue']}[⏰] {msg}{colors['reset']}"),
}

# --- SCRIPT LOGIC ---

# Load environment variables
discord_tokens_env = os.getenv('DISCORD_TOKENS', '')
if discord_tokens_env:
    discord_tokens = [token.strip() for token in discord_tokens_env.split(',') if token.strip()]
else:
    discord_token = os.getenv('DISCORD_TOKEN')
    if not discord_token:
        logger['critical']("Tidak ada Discord token yang ditemukan! Harap atur DISCORD_TOKENS atau DISCORD_TOKEN di .env.")
        raise ValueError("Discord token not found")
    discord_tokens = [discord_token]

google_api_keys = os.getenv('GOOGLE_API_KEYS', '').split(',')
google_api_keys = [key.strip() for key in google_api_keys if key.strip()]
if not google_api_keys:
    logger['critical']("Tidak ada Google API Key yang ditemukan! Harap atur GOOGLE_API_KEYS di .env.")
    raise ValueError("Google API keys not found")

# Global variables
processed_message_ids = set()
used_api_keys = set()
last_generated_text = None
cooldown_time = 86400  # 24 hours in seconds

def get_random_api_key():
    available_keys = [key for key in google_api_keys if key not in used_api_keys]
    if not available_keys:
        logger['error']("Semua API key terkena error 429. Menunggu 24 jam sebelum mencoba lagi...")
        time.sleep(cooldown_time)
        used_api_keys.clear()
        return get_random_api_key()
    return random.choice(available_keys)

def get_random_message_from_file():
    """
    Membaca pesan acak dari file pesan2.txt.
    """
    try:
        with open("pesan2.txt", "r", encoding="utf-8") as file:
            messages = [line.strip() for line in file.readlines() if line.strip()]
            return random.choice(messages) if messages else "Tidak ada pesan tersedia di file."
    except FileNotFoundError:
        return "File pesan2.txt tidak ditemukan!"

def generate_language_specific_prompt(user_message, prompt_language):
    if prompt_language == 'id':
        return f"Balas pesan berikut dalam bahasa Indonesia: {user_message}"
    elif prompt_language == 'en':
        return f"Reply to the following message in English: {user_message}"
    else:
        logger['warn'](f"Bahasa prompt '{prompt_language}' tidak valid. Pesan dilewati.")
        return None

def generate_reply(prompt, prompt_language, use_google_ai=True):
    global last_generated_text
    if use_google_ai:
        google_api_key = get_random_api_key()
        lang_prompt = generate_language_specific_prompt(prompt, prompt_language)
        if lang_prompt is None:
            return None
        ai_prompt = f"{lang_prompt}\n\nBuatlah menjadi 1 kalimat menggunakan bahasa sehari hari manusia."
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={google_api_key}'
        headers = {'Content-Type': 'application/json'}
        data = {'contents': [{'parts': [{'text': ai_prompt}]}]}
        while True:
            try:
                response = requests.post(url, headers=headers, json=data)
                if response.status_code == 429:
                    logger['warn'](f"API key {google_api_key[:5]}... terkena rate limit (429). Menggunakan API key lain...")
                    used_api_keys.add(google_api_key)
                    return generate_reply(prompt, prompt_language, use_google_ai)
                response.raise_for_status()
                result = response.json()
                generated_text = result['candidates'][0]['content']['parts'][0]['text']
                if generated_text == last_generated_text:
                    logger['loading']("AI menghasilkan teks yang sama, meminta teks baru...")
                    continue
                last_generated_text = generated_text
                return generated_text
            except requests.exceptions.RequestException as e:
                logger['error'](f"Request failed: {e}")
                time.sleep(2)
    else:
        return get_random_message_from_file()

def get_channel_info(channel_id, token):
    headers = {'Authorization': token}
    channel_url = f"https://discord.com/api/v9/channels/{channel_id}"
    try:
        channel_response = requests.get(channel_url, headers=headers)
        channel_response.raise_for_status()
        channel_data = channel_response.json()
        channel_name = channel_data.get('name', 'Unknown Channel')
        guild_id = channel_data.get('guild_id')
        server_name = "Direct Message"
        if guild_id:
            guild_url = f"https://discord.com/api/v9/guilds/{guild_id}"
            guild_response = requests.get(guild_url, headers=headers)
            guild_response.raise_for_status()
            guild_data = guild_response.json()
            server_name = guild_data.get('name', 'Unknown Server')
        return server_name, channel_name
    except requests.exceptions.RequestException as e:
        logger['error'](f"Error mengambil info channel {channel_id} dengan token {token[:5]}...: {e}")
        return "Unknown Server", "Unknown Channel"

def get_bot_info(token):
    headers = {'Authorization': token}
    try:
        response = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
        response.raise_for_status()
        data = response.json()
        username = data.get("username", "Unknown")
        discriminator = data.get("discriminator", "0") # Default to 0 for new username system
        if discriminator == "0":
            full_username = username
        else:
            full_username = f"{username}#{discriminator}"
        bot_id = data.get("id", "Unknown")
        return full_username, bot_id
    except requests.exceptions.RequestException as e:
        logger['error'](f"Gagal mengambil info akun bot: {e}")
        return "Unknown", "Unknown"

def auto_reply(channel_id, settings, token, bot_user_id):
    headers = {'Authorization': token}
    
    while True:
        try:
            if settings["use_google_ai"]:
                # Logic for AI replies
                logger['loading'](f"[{bot_user_id[-4:]}][Channel {channel_id}] Menunggu {settings['read_delay']} detik...")
                time.sleep(settings["read_delay"])
                prompt = None
                reply_to_id = None
                try:
                    response = requests.get(f'https://discord.com/api/v9/channels/{channel_id}/messages?limit=1', headers=headers)
                    response.raise_for_status()
                    messages = response.json()
                    if messages:
                        most_recent_message = messages[0]
                        message_id = most_recent_message.get('id')
                        author_id = most_recent_message.get('author', {}).get('id')
                        
                        if author_id != bot_user_id and message_id not in processed_message_ids:
                            user_message = most_recent_message.get('content', '').strip()
                            if user_message and not most_recent_message.get('attachments'):
                                logger['info'](f"[{bot_user_id[-4:]}][Channel {channel_id}] Received: {user_message}")
                                prompt = user_message
                                reply_to_id = message_id
                                processed_message_ids.add(message_id)
                            else:
                                logger['info'](f"[{bot_user_id[-4:]}][Channel {channel_id}] Pesan terakhir bukan teks, dilewati.")
                except requests.exceptions.RequestException as e:
                    logger['error'](f"[{bot_user_id[-4:]}][Channel {channel_id}] Request error: {e}")
                
                if prompt:
                    result = generate_reply(prompt, settings["prompt_language"], settings["use_google_ai"])
                    if result:
                        send_message(channel_id, result, token, bot_user_id, reply_to=reply_to_id if settings["use_reply"] else None, delete_after=settings["delete_bot_reply"], delete_immediately=settings["delete_immediately"])
                else:
                    logger['info'](f"[{bot_user_id[-4:]}][Channel {channel_id}] Tidak ada pesan baru.")
                
                logger['loading'](f"[{bot_user_id[-4:]}][Channel {channel_id}] Menunggu iterasi berikutnya {settings['delay_interval']} detik...")
                time.sleep(settings["delay_interval"])

            else:
                # Logic for sending messages from file
                message_text = generate_reply("", settings["prompt_language"], use_google_ai=False)
                send_message(channel_id, message_text, token, bot_user_id, delete_after=settings["delete_bot_reply"], delete_immediately=settings["delete_immediately"])

                delay = settings["delay_interval"]
                # PERUBAHAN: Pesan log disesuaikan menjadi 5 jam
                logger['loading'](f"[{bot_user_id[-4:]}][Channel {channel_id}] Pesan berikutnya dalam 5 jam...")
                time.sleep(delay)
        except Exception as e:
            logger['error'](f"[{bot_user_id[-4:]}][Thread {channel_id}] Terjadi error: {e}. Restart dalam 10 detik.")
            time.sleep(10)

def send_message(channel_id, message_text, token, bot_user_id, reply_to=None, delete_after=None, delete_immediately=False):
    headers = {'Authorization': token, 'Content-Type': 'application/json'}
    payload = {'content': message_text}
    if reply_to:
        payload["message_reference"] = {"message_id": reply_to}
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        message_id = data.get("id")
        logger['success'](f"[{bot_user_id[-4:]}][Channel {channel_id}] Pesan terkirim: \"{message_text}\"")
        
        if delete_after is not None and delete_after >= 0:
            if delete_immediately:
                threading.Thread(target=delete_message, args=(channel_id, message_id, token, bot_user_id), daemon=True).start()
            elif delete_after > 0:
                threading.Thread(target=delayed_delete, args=(channel_id, message_id, delete_after, token, bot_user_id), daemon=True).start()
    except requests.exceptions.RequestException as e:
        logger['error'](f"[{bot_user_id[-4:]}][Channel {channel_id}] Gagal mengirim pesan: {e}")

def delayed_delete(channel_id, message_id, delay, token, bot_user_id):
    time.sleep(delay)
    delete_message(channel_id, message_id, token, bot_user_id)

def delete_message(channel_id, message_id, token, bot_user_id):
    headers = {'Authorization': token}
    url = f'https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}'
    try:
        response = requests.delete(url, headers=headers)
        if response.status_code == 204:
            logger['success'](f"[{bot_user_id[-4:]}][Channel {channel_id}] Pesan {message_id} berhasil dihapus.")
        else:
            logger['error'](f"[{bot_user_id[-4:]}][Channel {channel_id}] Gagal hapus pesan. Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger['error'](f"[{bot_user_id[-4:]}][Channel {channel_id}] Gagal hapus pesan: {e}")

def get_channel_settings(channel_id, channel_name):
    logger['section'](f"Pengaturan untuk Channel: {channel_name} ({channel_id})")
    use_google_ai = input(f"{colors['blue']}[?] Gunakan Google Gemini AI? (y/n): {colors['reset']}").strip().lower() == 'y'
    
    if use_google_ai:
        prompt_language = input(f"{colors['blue']}[?] Pilih bahasa prompt (en/id) [default: id]: {colors['reset']}").strip().lower() or "id"
        read_delay = int(input(f"{colors['blue']}[?] Masukkan delay membaca pesan (detik): {colors['reset']}"))
        delay_interval = int(input(f"{colors['blue']}[?] Masukkan interval iterasi auto reply (detik): {colors['reset']}"))
    else:
        prompt_language = "id"  
        read_delay = 0
        # PERUBAHAN: Interval diubah menjadi 5 jam (dalam detik)
        delay_interval = 5 * 60 * 60
        # PERUBAHAN: Pesan info disesuaikan menjadi 5 jam
        logger['info']("Mode 'Kirim dari File' dipilih. Interval diatur ke 5 jam.")

    use_reply = input(f"{colors['blue']}[?] Kirim pesan sebagai reply? (y/n): {colors['reset']}").strip().lower() == 'y'
    hapus_balasan = input(f"{colors['blue']}[?] Hapus balasan bot setelah dikirim? (y/n): {colors['reset']}").strip().lower() == 'y'
    delete_bot_reply = None
    delete_immediately = False
    if hapus_balasan:
        delete_bot_reply_input = input(f"{colors['blue']}[?] Setelah berapa detik balasan dihapus? (0 untuk langsung): {colors['reset']}")
        delete_bot_reply = int(delete_bot_reply_input)
        if delete_bot_reply == 0:
            delete_immediately = True

    return {
        "prompt_language": prompt_language, "use_google_ai": use_google_ai,
        "read_delay": read_delay, "delay_interval": delay_interval,
        "use_reply": use_reply, "delete_bot_reply": delete_bot_reply,
        "delete_immediately": delete_immediately
    }

if __name__ == "__main__":
    logger['banner']()
    
    # --- Verifikasi Akun ---
    logger['section']("Memverifikasi Akun Discord")
    valid_accounts = []
    for token in discord_tokens:
        username, bot_id = get_bot_info(token)
        if bot_id != "Unknown":
            valid_accounts.append({"username": username, "bot_id": bot_id, "token": token})
            logger['success'](f"Akun terverifikasi: {username} (ID: {bot_id})")
        else:
            logger['error'](f"Token tidak valid: {token[:7]}...")

    if not valid_accounts:
        logger['critical']("Tidak ada token Discord yang valid. Keluar dari program.")
        sys.exit(1)

    # --- Input Channel ---
    logger['section']("Input Konfigurasi Channel")
    channel_ids_input = input(f"{colors['blue']}[?] Masukkan ID channel (pisahkan dengan koma): {colors['reset']}")
    channel_ids = [cid.strip() for cid in channel_ids_input.split(",") if cid.strip()]

    # --- LOGIKA BARU: Pemilihan Akun & Pengaturan ---
    configs = []
    
    print("\n" + f"{colors['bold']}Akun yang tersedia:{colors['reset']}")
    for i, acc in enumerate(valid_accounts):
        print(f"  {colors['yellow']}[{i+1}] {acc['username']}{colors['reset']}")

    use_different_accounts = input(f"\n{colors['blue']}[?] Gunakan akun berbeda untuk tiap channel? (y/n): {colors['reset']}").strip().lower() == 'y'
    
    default_account_indices = []
    if not use_different_accounts:
        choices_input = input(f"{colors['blue']}[?] Pilih akun untuk semua channel (bisa lebih dari satu, pisahkan dgn koma/spasi): {colors['reset']}")
        default_account_indices = [int(num.strip()) - 1 for num in choices_input.replace(',', ' ').split() if num.strip().isdigit()]

    use_same_settings = input(f"{colors['blue']}[?] Gunakan pengaturan yang sama untuk semua channel? (y/n): {colors['reset']}").strip().lower() == 'y'
    
    default_settings = None
    if use_same_settings:
        temp_token = valid_accounts[0]['token']
        _, temp_channel_name = get_channel_info(channel_ids[0], temp_token)
        default_settings = get_channel_settings(channel_ids[0], f"{temp_channel_name} (sebagai template)")

    for cid in channel_ids:
        account_indices_to_use = default_account_indices
        if use_different_accounts:
            choices_input = input(f"\n{colors['blue']}[?] Pilih akun untuk Channel ID {cid} (bisa lebih dari satu, pisahkan dgn koma/spasi): {colors['reset']}")
            account_indices_to_use = [int(num.strip()) - 1 for num in choices_input.replace(',', ' ').split() if num.strip().isdigit()]

        # Ambil info channel & settings sekali saja per channel
        first_valid_index = account_indices_to_use[0]
        server_name, channel_name = get_channel_info(cid, valid_accounts[first_valid_index]['token'])
        logger['info'](f"Info Channel: ID={cid}, Server='{server_name}', Channel='{channel_name}'")

        settings_to_use = default_settings
        if not use_same_settings:
            settings_to_use = get_channel_settings(cid, channel_name)
        
        for index in account_indices_to_use:
            if 0 <= index < len(valid_accounts):
                account_to_use = valid_accounts[index]
                configs.append({
                    "channel_id": cid,
                    "channel_name": channel_name,
                    "account": account_to_use,
                    "settings": settings_to_use
                })
            else:
                logger['warn'](f"Nomor akun '{index + 1}' tidak valid dan akan dilewati.")


    # --- Ringkasan & Memulai Bot ---
    logger['section']("Ringkasan Konfigurasi & Memulai Bot")
    threads = []
    for config in configs:
        settings = config['settings']
        account = config['account']
        
        interval_display = f"{settings['delay_interval']} detik"
        # PERUBAHAN: Tampilan ringkasan diubah agar lebih dinamis
        if not settings['use_google_ai']:
            hours = settings['delay_interval'] // 3600
            interval_display = f"{hours} jam"

        summary_msg = (
            f"Channel: {config['channel_name']} ({config['channel_id']}) | Bot: {account['username']}\n"
            f"  Mode: {'Gemini AI' if settings['use_google_ai'] else 'Kirim dari File'}\n"
            f"  Interval: {interval_display}\n"
            f"  Reply: {'Ya' if settings['use_reply'] else 'Tidak'}\n"
            f"  Hapus Pesan: {'Ya' if settings['delete_bot_reply'] is not None else 'Tidak'}"
        )
        logger['summary'](summary_msg)

        thread = threading.Thread(
            target=auto_reply, 
            args=(config['channel_id'], settings, account['token'], account['bot_id']), 
            daemon=True
        )
        threads.append(thread)
        thread.start()
        logger['success'](f"Thread untuk [{account['username']}] di channel [{config['channel_name']}] telah dimulai.")

    logger['info']("\nSemua bot sedang berjalan... Tekan CTRL+C untuk menghentikan.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger['warn']("\nMenutup bot... Selamat tinggal!")

