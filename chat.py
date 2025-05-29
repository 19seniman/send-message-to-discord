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

kimi_api_key = os.getenv('KIMI_API_KEY')
if not kimi_api_key:
    raise ValueError("Tidak ada Kimi AI API Key yang ditemukan! Harap atur KIMI_API_KEY di .env.")

processed_message_ids = set()
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

def get_random_message_from_file():
    try:
        with open("pesan.txt", "r", encoding="utf-8") as file:
            messages = [line.strip() for line in file.readlines() if line.strip()]
            return random.choice(messages) if messages else "Tidak ada pesan tersedia di file."
    except FileNotFoundError:
        return "File pesan.txt tidak ditemukan!"

def generate_language_specific_prompt(user_message, prompt_language):
    if prompt_language == 'id':
        return f"Balas pesan berikut dalam bahasa Indonesia: {user_message}"
    elif prompt_language == 'en':
        return f"Reply to the following message in English: {user_message}"
    else:
        log_message(f"Bahasa prompt '{prompt_language}' tidak valid. Pesan dilewati.", "WARNING")
        return None

def generate_reply(prompt, prompt_language, use_kimi_ai=True):
    global last_generated_text
    if use_kimi_ai:
        lang_prompt = generate_language_specific_prompt(prompt, prompt_language)
        if lang_prompt is None:
            return None
        ai_prompt = f"{lang_prompt}\n\nBuatlah menjadi 1 kalimat menggunakan bahasa sehari hari manusia."
        url = "https://api.kimi.ai/v1/generate"  # Replace with the actual Kimi AI endpoint
        headers = {'Authorization': f'Bearer {kimi_api_key}', 'Content-Type': 'application/json'}
        data = {'prompt': ai_prompt}
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            generated_text = result['text']
            if generated_text == last_generated_text:
                log_message("AI menghasilkan teks yang sama, meminta teks baru...", "WAIT")
                return generate_reply(prompt, prompt_language, use_kimi_ai)
            last_generated_text = generated_text
            return generated_text
        except requests.exceptions.RequestException as e:
            log_message(f"Request failed: {e}", "ERROR")
            return None
    else:
        return get_random_message_from_file()

# The rest of the script remains the same, except for any references to Google API keys.
