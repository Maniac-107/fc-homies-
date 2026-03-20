import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
import json
from flask import Flask
from threading import Thread
from datetime import datetime, timezone, timedelta
import time
import sqlite3
import uuid

# ========== DATABASE SETUP ==========

def init_announcements_db():
    conn = sqlite3.connect('announcements.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS announcements(
        id TEXT,
        title TEXT,
        description TEXT,
        role_id TEXT,
        channel_id TEXT,
        announce_time TEXT,
        created_by TEXT,
        status TEXT
    )
    ''')

    conn.commit()
    conn.close()


def init_lfm_db():
    conn = sqlite3.connect('lfm.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS lfm(
        id INTEGER PRIMARY KEY,
        last_used TEXT
    )
    ''')

    conn.commit()
    conn.close()


init_announcements_db()
init_lfm_db()

# ========== KEEP ALIVE ==========

app = Flask('')

@app.route('/')
def home():
    return "Bot running"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ========== BOT SETUP ==========

TOKEN = os.getenv("BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ========== READY ==========

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot started")
    print(bot.user)


keep_alive()

bot.run(TOKEN)
