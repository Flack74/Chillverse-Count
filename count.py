import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import math

# Intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

# Bot setup
bot = commands.Bot(command_prefix='!', intents=intents)

# Current count
count = 0

# Channel ID for counting
COUNTING_CHANNEL_ID = 1022075494100910160  # Replace with your actual channel ID

# Last user who counted
last_user_id = None


@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}')


@bot.event
async def on_message(message):
    global count, last_user_id

    # Ignore messages not in the counting channel or from bots
    if message.channel.id != COUNTING_CHANNEL_ID or message.author.bot:
        return

    try:
        # Evaluate the message content
        expression = message.content
        result = eval(expression)  # Evaluate mathematical expressions
        if not isinstance(result, (int, float)):  # Ensure the result is numeric
            raise ValueError("Result is not numeric")

        num = int(result)  # Convert to an integer for comparison

        # Check if the user is allowed to count
        if message.author.id == last_user_id:
            if count > 0:
                reduction = max(1, math.floor(count * 0.1))  # Ensure at least a reduction of 1
                count -= reduction  # Apply reduction
            else:
                count = 0  # Reset to zero if count is already very low
            last_user_id = None  # Reset the last user
            await message.channel.send(
                f"{message.author.mention}, you cannot count consecutively! The count is reduced to {count}. Start again from {count + 1}."
            )
            return

        # Check if the number is correct
        if num == count + 1:
            count += 1
            last_user_id = message.author.id
            await message.add_reaction("✅")  # React with a checkmark
        else:
            # Incorrect count: reduce by 10% or reset to 0
            if count > 0:
                reduction = max(1, math.floor(count * 0.1))  # Ensure at least a reduction of 1
                count -= reduction  # Apply reduction
            else:
                count = 0  # Reset to zero
            last_user_id = None  # Reset the last user
            await message.channel.send(
                f"{message.author.mention} messed up! The count is reduced to {count}. Start again from {count + 1}."
            )
    except (ValueError, SyntaxError):
        # Silently ignore invalid or non-numeric messages
        return


# Run the bot
load_dotenv()
bot.run(os.getenv('DISCORD_TOKEN'))  # Use environment variable for the token
