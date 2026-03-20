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

# ========== UPDATED OVR COMMAND ==========

@bot.tree.command(name="ovr-calculator", description="Calculate your team OVR instantly")
@app_commands.describe(
    players="Number of players in squad (minimum 11)",
    base_values="Base OVR separated with + (example: 115+116+117)",
    rank_values="Rank levels separated with + (example: 5+3+0)",
    badges="Total level 5 badges (optional)"
)
async def ovr_calculator(
    interaction: discord.Interaction,
    players: int,
    base_values: str,
    rank_values: str,
    badges: int = 0
):

    await interaction.response.defer()

    try:

        # convert input text into list of numbers
        base_nums = [int(v.strip()) for v in base_values.split("+")]
        rank_nums = [int(v.strip()) for v in rank_values.split("+")]

        if players < 11:
            await interaction.followup.send(
                "❌ You must have at least 11 players.",
                ephemeral=True
            )
            return

        if len(base_nums) != players or len(rank_nums) != players:
            await interaction.followup.send(
                f"❌ Values do not match player count ({players}).",
                ephemeral=True
            )
            return

        # totals
        base_sum = sum(base_nums)
        rank_sum = sum(rank_nums)

        # average formula
        base_avg = 1 + (base_sum - 1) // players
        rank_avg = 1 + (rank_sum - 1) // players

        badge_bonus = badges
        final_ovr = base_avg + rank_avg + badge_bonus

        # next level requirement
        need_base = (base_avg * players) + 1 - base_sum
        need_rank = (rank_avg * players) + 1 - rank_sum

        # embed
        em = discord.Embed(
            title="⚡ OVR Result",
            color=0x2563EB
        )

        em.add_field(name="Players", value=players, inline=True)
        em.add_field(name="Base Avg", value=base_avg, inline=True)
        em.add_field(name="Rank Avg", value=rank_avg, inline=True)

        if badges > 0:
            em.add_field(name="Badges", value=f"+{badges}", inline=True)
            em.add_field(name="Total OVR", value=f"**{final_ovr}**", inline=True)
        else:
            em.add_field(name="Total OVR", value=final_ovr, inline=True)

        # next level info
        req_list = []

        if need_base > 0:
            req_list.append(f"Base needed: +{need_base}")

        if need_rank > 0:
            req_list.append(f"Ranks needed: +{need_rank}")

        if req_list:
            em.add_field(
                name="Next OVR Requirements",
                value="\n".join(req_list),
                inline=False
            )

        # breakdown
        text = f"{base_avg} + {rank_avg}"

        if badges > 0:
            text += f" + {badges}"

        text += f" = **{final_ovr}**"

        em.add_field(
            name="Calculation",
            value=text,
            inline=False
        )

        em.set_footer(text="Use + between values")

        await interaction.followup.send(embed=em)

    except:
        await interaction.followup.send(
            "❌ Invalid input format. Use + between numbers.",
            ephemeral=True
        )


#### PROFIT LOSS CALCULATOR ###


@bot.tree.command(name="invest", description="Investment profit/loss calculator")
@app_commands.describe(
    buy_price="Buying price",
    sell_price="Selling price"
)
async def invest_calc(
    interaction: discord.Interaction,
    buy_price: float,
    sell_price: float
):

    await interaction.response.defer()

    try:

        TAX = 0.10

        tax = sell_price * TAX
        sell_after_tax = sell_price - tax
        profit = sell_after_tax - buy_price


        # ===== Color + result =====

        if sell_price > buy_price:
            color = 0x16A34A  # green
            result_text = f"Profit: {profit:,.0f}"
        elif buy_price > sell_price:
            color = 0xDC2626  # red
            result_text = f"Loss: {abs(profit):,.0f}"
        else:
            color = 0x808080  # gray
            result_text = "No Profit No Loss"


        # ===== Profit % =====

        if buy_price != 0:
            percent = (profit / buy_price) * 100
        else:
            percent = 0


        # ===== Embed =====

        embed = discord.Embed(
            title="Investment Result",
            color=color
        )

        embed.add_field(
            name="Buying Price",
            value=f"{buy_price:,.0f}",
            inline=False
        )

        embed.add_field(
            name="Selling Price",
            value=f"{sell_price:,.0f}",
            inline=False
        )

        embed.add_field(
            name="Tax (10%)",
            value=f"{tax:,.0f}",
            inline=False
        )

        embed.add_field(
            name="Result",
            value=result_text,
            inline=False
        )

        embed.add_field(
            name="Profit %",
            value=f"{percent:.2f}%",
            inline=False
        )

        await interaction.followup.send(embed=embed)

    except Exception:
        await interaction.followup.send(
            "Invalid values",
            ephemeral=True
        )

keep_alive()

bot.run(TOKEN)
