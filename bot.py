import discord
import google.generativeai as genai
from discord.ext import commands
import aiohttp
import re
import traceback
from config import *
from discord import app_commands
from typing import Optional, Dict
from urllib.parse import urlparse
from api.bing import create_image


# ---------------------------------------------AI Configuration-------------------------------------------------
genai.configure(api_key=GOOGLE_AI_KEY)

text_model = genai.GenerativeModel(
    model_name="gemini-pro",
    generation_config=text_generation_config,
    safety_settings=safety_settings,
)
image_model = genai.GenerativeModel(
    model_name="gemini-pro-vision",
    generation_config=image_generation_config,
    safety_settings=safety_settings,
)

message_history: Dict[int, genai.ChatSession] = {}

# ---------------------------------------------Discord Code-------------------------------------------------
# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(
    command_prefix=[],
    intents=intents,
    help_command=None,
    activity=discord.Game("with your feelings"),
)


# On Message Function
@bot.event
async def on_message(message: discord.Message):
    # Ignore messages sent by the bot
    if message.author == bot.user:
        return
    # Check if the bot is mentioned or the message is a DM
    if not (
        bot.user.mentioned_in(message)
        or isinstance(message.channel, discord.DMChannel)
        or message.channel.id in tracked_channels
    ):
        return
    # Start Typing to seem like something happened
    try:
        async with message.channel.typing():
            # Check for image attachments
            if message.attachments:
                print(
                    "New Image Message FROM:"
                    + str(message.author.id)
                    + ": "
                    + message.content
                )
                # Currently no chat history for images
                for attachment in message.attachments:
                    # these are the only image extentions it currently accepts
                    if any(
                        attachment.filename.lower().endswith(ext)
                        for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]
                    ):
                        await message.add_reaction("🎨")

                        async with aiohttp.ClientSession() as session:
                            async with session.get(attachment.url) as resp:
                                if resp.status != 200:
                                    await message.channel.send(
                                        "Unable to download the image."
                                    )
                                    return
                                image_data = await resp.read()
                                response_text = (
                                    await generate_response_with_image_and_text(
                                        image_data, message.content
                                    )
                                )
                                # Split the Message so discord does not get upset
                                await split_and_send_messages(
                                    message, response_text, 1700
                                )
                                return
            # Not an Image do text response
            else:
                print("FROM:" + str(message.author.name) + ": " + message.content)
                query = f'@{message.author.name} said "{message.clean_content}"'

                # Fetch message that is being replied to
                if message.reference is not None:
                    reply_message = await message.channel.fetch_message(
                        message.reference.message_id
                    )
                    if reply_message.author.id != bot.user.id:
                        query = f'{query} while quoting @{reply_message.author.name} "{reply_message.clean_content}"'

                response_text = await generate_response_with_text(
                    message.channel.id, query
                )
                # Split the Message so discord does not get upset
                await split_and_send_messages(message, response_text, 1700)
                return
    except Exception as e:
        await message.reply("Some error has occurred, please check logs!")


# ---------------------------------------------AI Generation History-------------------------------------------------


async def generate_response_with_text(channel_id, message_text):
    try:
        formatted_text = format_discord_message(message_text)
        if not (channel_id in message_history):
            message_history[channel_id] = text_model.start_chat(history=bot_template)
        response = message_history[channel_id].send_message(formatted_text)
        return response.text
    except Exception as e:
        with open("errors.log", "a+") as errorlog:
            errorlog.write("\n##########################\n")
            errorlog.write("Message: " + message_text)
            errorlog.write("\n-------------------\n")
            errorlog.write("Traceback:\n" + traceback.format_exc())
            errorlog.write("\n-------------------\n")
            errorlog.write("History:\n" + str(message_history[channel_id].history))
            errorlog.write("\n-------------------\n")
            errorlog.write("Candidates:\n" + str(response.candidates))
            errorlog.write("\n-------------------\n")
            errorlog.write("Parts:\n" + str(response.parts))
            errorlog.write("\n-------------------\n")
            errorlog.write("Prompt feedbacks:\n" + str(response.prompt_feedbacks))


async def generate_response_with_image_and_text(image_data, text):
    image_parts = [{"mime_type": "image/jpeg", "data": image_data}]
    prompt_parts = [
        image_parts[0],
        f"\n{text if text else 'What is this a picture of?'}",
    ]
    response = image_model.generate_content(prompt_parts)
    if response._error:
        return "❌" + str(response._error)
    return response.text


@bot.tree.command(name="forget", description="Forget message history")
@app_commands.describe(persona="Persona of bot")
async def forget(interaction: discord.Interaction, persona: Optional[str] = None):
    try:
        message_history.pop(interaction.channel_id)
        if persona:
            temp_template = bot_template.copy()
            temp_template.append(
                {
                    "role": "user",
                    "parts": ["Forget what I said earlier! You are " + persona],
                }
            )
            temp_template.append({"role": "model", "parts": ["Ok!"]})
            message_history[interaction.channel_id] = text_model.start_chat(
                history=temp_template
            )
    except Exception as e:
        pass
    await interaction.response.send_message("Message history for channel erased.")


@bot.tree.command(
    name="createthread",
    description="Create a thread in which bot will respond to every message.",
)
@app_commands.describe(name="Thread name")
async def create_thread(interaction: discord.Interaction, name: str):
    try:
        thread = await interaction.channel.create_thread(
            name=name, auto_archive_duration=60
        )
        tracked_channels.append(thread.id)
        await interaction.response.send_message(f"Thread {name} created!")
    except Exception as e:
        await interaction.response.send_message("Error creating thread!")


# ---------------------------------------------Sending Messages-------------------------------------------------
async def split_and_send_messages(message_system: discord.Message, text, max_length):
    # Split the string into parts
    messages = []
    for i in range(0, len(text), max_length):
        sub_message = text[i : i + max_length]
        messages.append(sub_message)

    # Send each part as a separate message
    for string in messages:
        message_system = await message_system.reply(string)


def format_discord_message(input_string):
    # Replace emoji with name
    cleaned_content = re.sub(r"<(:[^:]+:)[^>]+>", r"\1", input_string)
    return cleaned_content


def rewrite_prompt(prompt: str):
    prompt = f"revise `{prompt}` to a DALL-E prompt, return the content in English only return the scene and detail"
    response_text = text_model.generate_content(prompt)
    # print(response_text.text)
    return response_text.text


@bot.tree.command(name="bing-prompt", description="use bing create to create images")
@app_commands.describe(
    prompt="prompt for create images",
)
async def prompt_bing(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer()
    image_list = create_image(prompt)
    parsed_url = urlparse(image_list[0])
    embeds = [
        discord.Embed(url=f"{parsed_url.scheme}://{parsed_url.netloc}").set_image(
            url=image
        )
        for image in image_list
    ]
    await interaction.followup.send(content=prompt, embeds=embeds)


@bot.tree.command(
    name="bing-prompt-pro",
    description="use gemini to enhance bing create to create better images",
)
@app_commands.describe(
    prompt="prompt for create images",
)
async def prompt_bing_pro(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer()
    prompt = rewrite_prompt(prompt)
    image_list = create_image(prompt)
    parsed_url = urlparse(image_list[0])
    embeds = [
        discord.Embed(url=f"{parsed_url.scheme}://{parsed_url.netloc}").set_image(
            url=image
        )
        for image in image_list
    ]
    await interaction.followup.send(content=f"gemini rewrite:{prompt}", embeds=embeds)


@bot.tree.command(
    name="reprompt",
    description="Rewrite prompt with gemini",
)
@app_commands.describe(
    prompt="Rewrite prompt with gemini",
)
async def re_prompt(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer()
    prompt = rewrite_prompt(prompt)
    await interaction.followup.send(content=f"gemini rewrite:{prompt}")


# ---------------------------------------------Run Bot-------------------------------------------------


async def sync():
    synced = await bot.tree.sync()
    # await send(f"Synced {len(synced)} commands")
    return synced


@bot.event
async def on_ready():
    await bot.tree.sync()
    s = await sync()
    print("----------------------------------------")
    print(f"Gemini Bot Logged in as {bot.user} - {s}")
    print("----------------------------------------")


bot.run(DISCORD_BOT_TOKEN)
