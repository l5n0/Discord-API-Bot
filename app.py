import os
import asyncio
import signal
import aiohttp
from flask import Flask, request, jsonify, render_template
import discord
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from contextlib import suppress

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Retrieve configuration from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')

DISCORD_API_BASE_URL = "https://discord.com/api"
DISCORD_USER_URL = f"{DISCORD_API_BASE_URL}/users"

# Discord bot setup
intents = discord.Intents.default()
intents.members = True
intents.presences = True
client = discord.Client(intents=intents)

# ThreadPoolExecutor for running blocking Flask app
executor = ThreadPoolExecutor(1)

# Flask route to serve the form
@app.route('/')
def home():
    return render_template('index.html')

# Flask route to fetch user data
@app.route('/fetch_user', methods=['GET'])
def fetch_user():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    loop = client.loop
    try:
        user_data = asyncio.run_coroutine_threadsafe(get_user_data(user_id), loop).result()
        return render_template('index.html', user_data=user_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Function to fetch user data and presence
async def get_user_data(user_id):
    await client.wait_until_ready()
    guild = client.guilds[0]  # Assuming the bot is in only one guild
    member = guild.get_member(int(user_id)) if guild else None

    if member:
        presence = {
            "status": member.status.name,
            "activities": [activity.name for activity in member.activities]
        }
        avatar_url = str(member.avatar.url) if member.avatar else None
        profile_color = str(member.color) if member.color else None

        # Additional data
        nickname = member.nick
        joined_at = member.joined_at.strftime("%Y-%m-%d %H:%M:%S") if member.joined_at else None
        created_at = member.created_at.strftime("%Y-%m-%d %H:%M:%S")
        boosting_since = member.premium_since.strftime("%Y-%m-%d %H:%M:%S") if member.premium_since else None

        user_data = {
            "username": member.name,
            "id": member.id,
            "avatar": avatar_url,
            "profile_color": profile_color,
            "status": presence["status"],
            "activities": presence["activities"],
            "nickname": nickname,
            "joined_at": joined_at,
            "created_at": created_at,
            "boosting_since": boosting_since
        }
    else:
        # Fetch user data directly from the Discord API
        user_data = await fetch_user_data_from_api(user_id)

    return user_data

async def fetch_user_data_from_api(user_id):
    url = f"{DISCORD_USER_URL}/{user_id}"
    headers = {
        "Authorization": f"Bot {BOT_TOKEN}"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                user_data = {
                    "username": data["username"],
                    "id": data["id"],
                    "avatar": f"https://cdn.discordapp.com/avatars/{data['id']}/{data['avatar']}.png" if data["avatar"] else None,
                    "profile_color": None,
                    "status": "unknown",
                    "activities": [],
                    "nickname": None,
                    "joined_at": None,
                    "created_at": None,
                    "boosting_since": None
                }
                return user_data
            else:
                return {"error": "User not found"}

# Start the bot
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

def run_flask():
    app.run(host='0.0.0.0', port=5000, use_reloader=False)

async def main():
    # Run the Flask app in an executor
    loop = asyncio.get_event_loop()
    loop.run_in_executor(executor, run_flask)
    await client.start(BOT_TOKEN)

async def shutdown():
    await client.close()
    executor.shutdown(wait=True)

def signal_handler(sig, frame):
    print("Shutdown signal received")
    loop = asyncio.get_event_loop()
    loop.create_task(shutdown())

if __name__ == '__main__':
    # Handle termination signals for a graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Keyboard interrupt received, shutting down...")
    finally:
        print("Shutting down...")
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
            with suppress(asyncio.CancelledError):
                loop.run_until_complete(task)
        loop.run_until_complete(shutdown())
        loop.close()
