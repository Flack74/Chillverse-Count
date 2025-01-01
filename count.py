import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import math
import requests
import time
from flask import Flask

# Intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

# Bot setup
bot = commands.Bot(command_prefix='!', intents=intents)

# Current count
count = 0

# Channel ID for counting
COUNTING_CHANNEL_ID = 1022075494100910160  # Replace with your actual channel ID

# Last user who counted
last_user_id = None

# Function to handle rate limiting
def handle_rate_limit(response):
    if response.status_code == 429:
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            retry_after = int(retry_after)
            print(f"Rate-limited. Retrying after {retry_after} seconds.")
            time.sleep(retry_after)
            return True  # Return True to indicate retrying
    return False

# Update bot status and bio with better logging
async def update_bot_status_and_bio():
    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Game("Counting 📊")
    )
    print("Status updated to idle with activity.")
    
    url = "https://discord.com/api/v10/users/@me"
    headers = {
        "Authorization": f"Bot {os.getenv('DISCORD_TOKEN')}",
        "Content-Type": "application/json"
    }
    data = {
        "bio": "Made by Flack ✨🚀"
    }

    # Retry logic for updating the bio
    for _ in range(3):  # Retry up to 3 times
        try:
            print(f"Attempting to update bio...")
            response = requests.patch(url, json=data, headers=headers, timeout=10)
            if handle_rate_limit(response):
                continue  # Retry if rate-limited
            response.raise_for_status()  # Raise exception for HTTP errors
            print("Bio updated successfully!")
            return  # Exit if bio update is successful
        except requests.exceptions.RequestException as e:
            print(f"Error updating bio: {e}")
            time.sleep(5)  # Wait a bit before retrying
        except Exception as e:
            print(f"Unexpected error: {e}")
            break  # Stop retrying after failure

@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}')
    # Update the status and bio when the bot is ready
    await update_bot_status_and_bio()

@bot.event
async def on_message(message):
    global count, last_user_id

    # Ignore messages not in the counting channel or from bots
    if message.channel.id != COUNTING_CHANNEL_ID or message.author.bot:
        return

    try:
        # Handle math expressions using eval (with safety)
        if message.content.startswith('!calc'):
            expression = message.content[6:].strip()  # Remove "!calc " from the start
            try:
                result = eval(expression)
                await message.channel.send(f"Result of {expression}: {result}")
            except Exception as e:
                await message.channel.send(f"Error evaluating the expression: {e}")
            return

        # Check if the message content is numeric
        num = int(message.content)  # Convert message content to an integer

        # Check if the user is allowed to count
        if message.author.id == last_user_id:
            if count > 0:
                reduction = max(1, math.floor(count * 0.5))  # Reduce by 50%
                count -= reduction  # Apply reduction
            else:
                count = 0  # Reset to zero if count is already low
            last_user_id = None  # Reset the last user
            await message.channel.send(
                f"{message.author.mention}, you cannot count consecutively! The count is reduced to {count}. Start again from {count + 1}."
            )
            return

        # Check if the number is correct
        if num == count + 1:
            count += 1
            last_user_id = message.author.id 
            await message.add_reaction('<:CheckChillversecount:1324017578821156874>')  # Using standard emoji as fallback
        else:
            # Incorrect count: reduce by 50% or reset to 0
            if count > 10:
                reduction = max(1, math.floor(count * 0.5))  # Reduce by 50%
                count -= reduction  # Apply reduction
            else:
                count = 0  # Reset to zero
            last_user_id = None  # Reset the last user
            await message.channel.send(
                f"{message.author.mention} messed up! The count is reduced to {count}. Start again from {count + 1}."
            )
    except ValueError:
        # Silently ignore non-numeric messages
        pass

# Create Flask web server to bind to Render's expected port
app = Flask(__name__)

@app.route('/')
def index():
    return 'Bot is running!'

# Run the bot and the web server (Render expects a port)
if __name__ == '__main__':
    load_dotenv()

    # Get port from environment variable for Render
    port = int(os.getenv("PORT", 5000))  # Default to 5000 if not set
    bot.loop.create_task(bot.start(os.getenv('DISCORD_TOKEN')))  # Run the bot
    app.run(host='0.0.0.0', port=port)  # Start Flask server
