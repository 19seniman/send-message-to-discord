**Menghapus Modul `shareithub` dari Script**

Untuk menghapus modul `shareithub` dari script yang Anda berikan, Anda perlu melakukan beberapa perubahan. Berikut adalah langkah-langkah yang perlu diambil:

1. **Hapus Import `shareithub`**  
   Hapus baris yang mengimpor modul `shareithub`.

2. **Hapus Penggunaan `shareithub`**  
   Pastikan tidak ada referensi atau penggunaan dari `shareithub` di dalam kode.

Berikut adalah versi yang telah dimodifikasi dari script Anda tanpa modul `shareithub`:

```python
import json
import threading
import time
import os
import random
import re
import requests
from dotenv import load_dotenv
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)
load_dotenv()

discord_tokens_env = os.getenv('DISCORD_TOKENS', '')
if discord_tokens_env:
    discord_tokens = [token.strip() for token in discord_tokens_env.split(',') if token.strip()]
else:
    discord_token = os.getenv('DISCORD_TOKEN')
    if not discord_token:
        raise ValueError("Tidak ada Discord token yang ditemukan! Harap atur DISCORD_TOKENS atau DISCORD_TOKEN di .env.")
    discord_tokens = [discord_token]

google_api_keys = os.getenv('GOOGLE_API_KEYS', '').split(',')
google_api_keys = [key.strip() for key in google_api_keys if key.strip()]
if not google_api_keys:
    raise ValueError("Tidak ada Google API Key yang ditemukan! Harap atur GOOGLE_API_KEYS di .env.")

processed_message_ids = set()
used_api_keys = set()
last_generated_text = None
cooldown_time = 86400

def log_message(message, level="INFO"):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if level.upper() == "SUCCESS":
        color, icon = Fore.GREEN, "✅"
    elif level.upper() == "ERROR":
        color, icon = Fore.RED, "🚨"
    elif level.upper() == "WARNING":
        color, icon = Fore.YELLOW, "⚠️"
    elif level.upper() == "WAIT":
        color, icon = Fore.CYAN, "⌛"
    else:
        color, icon = Fore.WHITE, "ℹ️"

    border = f"{Fore.MAGENTA}{'=' * 80}{Style.RESET_ALL}"
    formatted_message = f"{color}[{timestamp}] {icon} {message}{Style.RESET_ALL}"
    print(border)
    print(formatted_message)
    print(border)

def get_random_api_key():
    available_keys = [key for key in google_api_keys if key not in used_api_keys]
    if not available_keys:
        log_message("Semua API key terkena error 429. Menunggu 24 jam sebelum mencoba lagi...", "ERROR")
        time.sleep(cooldown_time)
        used_api_keys.clear()
        return get_random_api_key()
    return random.choice(available_keys)

def get_random_message_from_file():
    try
