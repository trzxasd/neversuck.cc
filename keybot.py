import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import random
from flask import Flask
from threading import Thread
import asyncio

# Web server for keeping the bot alive
app = Flask('')

@app.route('/')
def home():
    return "✅ Key Bot is alive and running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Bot settings
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Keys list
KEYS = [
    "cherniy", "beliy", "dolboeb", "neversuck", "piratemayhemhueta",
    "premiumkey", "vipaccess", "masterkey", "godmode", "ultimate"
]

# Data storage file
DATA_FILE = 'user_data.json'

def load_user_data():
    """Load user data from JSON file"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading data: {e}")
            return {}
    return {}

def save_user_data(data):
    """Save user data to JSON file"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving data: {e}")

def can_get_key(user_id):
    """Check if user can get a key (cooldown check)"""
    data = load_user_data()
    user_id = str(user_id)
    
    if user_id not in data:
        return True, None
    
    last_used = data[user_id].get('last_used')
    if not last_used:
        return True, None
    
    try:
        last_used = datetime.fromisoformat(last_used)
        cooldown_end = last_used + timedelta(days=7)
        
        if datetime.now() >= cooldown_end:
            return True, None
        else:
            return False, cooldown_end
    except Exception as e:
        print(f"Error checking cooldown: {e}")
        return True, None

def update_user_data(user_id, key):
    """Update user data after key issuance"""
    data = load_user_data()
    user_id = str(user_id)
    
    if user_id not in data:
        data[user_id] = {}
    
    data[user_id]['last_used'] = datetime.now().isoformat()
    data[user_id]['last_key'] = key
    data[user_id]['username'] = str(user_id)
    
    save_user_data(data)

def get_random_key():
    """Get a random key from the list"""
    return random.choice(KEYS)

@bot.event
async def on_ready():
    """Bot startup handler"""
    print(f'✅ Bot {bot.user} is now online!')
    print(f'✅ Bot ID: {bot.user.id}')
    print('✅ Ready to distribute keys!')
    print('------')
    
    # Set bot status
    activity = discord.Activity(type=discord.ActivityType.watching, name="/getkey for keys")
    await bot.change_presence(activity=activity)

@bot.tree.command(name="getkey", description="Get a key (7 days cooldown)")
async def getkey(interaction: discord.Interaction):
    """Command to get a key"""
    user_id = interaction.user.id
    username = interaction.user.name
    
    # Check cooldown
    can_get, cooldown_end = can_get_key(user_id)
    
    if not can_get:
        # Format remaining time
        time_left = cooldown_end - datetime.now()
        days = time_left.days
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds % 3600) // 60
        
        time_str = f"{days}d {hours}h {minutes}m"
        
        # Send message only to the user
        await interaction.response.send_message(
            f"⏰ **Cooldown Active!**\n"
            f"You've already received a key recently.\n"
            f"Next key available in: **{time_str}**",
            ephemeral=True
        )
        return
    
    # Generate key
    key = get_random_key()
    
    # Update user data
    update_user_data(user_id, key)
    
    # Send key only to the user
    await interaction.response.send_message(
        f"🎉 **Key Successfully Generated!**\n"
        f"**Your key:** `{key}`\n"
        f"⏰ Next key available in 7 days",
        ephemeral=True
    )
    
    print(f"Key '{key}' issued to {username} (ID: {user_id})")

@bot.tree.command(name="keyinfo", description="Check your key status")
async def keyinfo(interaction: discord.Interaction):
    """Command to check key status"""
    user_id = interaction.user.id
    data = load_user_data()
    user_data = data.get(str(user_id), {})
    
    if not user_data or 'last_used' not in user_data:
        await interaction.response.send_message(
            "🔍 **Key Status**\n"
            "You haven't received any keys yet.\n"
            "Use `/getkey` to get your first key!",
            ephemeral=True
        )
        return
    
    last_used = datetime.fromisoformat(user_data['last_used'])
    last_key = user_data.get('last_key', 'Unknown')
    cooldown_end = last_used + timedelta(days=7)
    
    if datetime.now() >= cooldown_end:
        status = "✅ **Ready** - You can get a new key!"
        time_left = "Available now"
    else:
        status = "⏰ **Cooldown** - Please wait"
        time_left = cooldown_end - datetime.now()
        days = time_left.days
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds % 3600) // 60
        time_left = f"{days}d {hours}h {minutes}m"
    
    await interaction.response.send_message(
        f"🔍 **Key Status**\n"
        f"Last key: `{last_key}`\n"
        f"Status: {status}\n"
        f"Time remaining: **{time_left}**",
        ephemeral=True
    )

@bot.event
async def on_connect():
    """Sync commands when bot connects"""
    await bot.tree.sync()
    print("✅ Slash commands synchronized")

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"Error: {error}")

# Bot startup
if __name__ == "__main__":
    print("🚀 Starting Discord Key Bot...")
    print("🔧 Initializing web server...")
    keep_alive()  # Start the web server
    
    TOKEN = "6038941d5c8dbbcb1f328659d6289e5df4bebd7fbfdae3ea8b634bdada4af3a1"
    
    try:
        print("🔧 Connecting to Discord...")
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ ERROR: Invalid bot token!")
    except Exception as e:
        print(f"❌ ERROR: {e}")
