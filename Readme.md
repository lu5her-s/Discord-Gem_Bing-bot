# Discord Bot to interact with Gemini API as ChatBot and Image Recognizer, Create images with Bing
Inspiration - https://github.com/Echoshard/Gemini_Discordbot

This bot acts as a Chatbot. It uses Google's Gemini API which is free for upto 60 calls/min as of Jan 2023.

The bot can be talked to by mentioning it or DMing it.

Each channel/thread has it's own context and can be erased by using /forget.

Due to API restrictions, the bot cannot remember image interactions.

Current version erases anything between < and > so any mentions or emojis

## Requirements

Get a Google Gemini api key from ai.google.dev

Make a discord bot at discord.com/developers/applications

[How to get BING_TOKEN](https://github.com/yihong0618/tg_bing_dalle#method-1-run-python-directly)
1. Open https://bing.com/create
2. Create an account or login
3. Create an image and F12 for open DevTools
4. in Network tab select Fetch/XHR
5. Click on first request, (show urls like https://bing.com/images/create/... )
6. Find Cookie start with _C_Auth and copy it
7. Paste it in BING_TOKEN

## Usage

1. Clone repository
2. Install all dependencies as specified in requirements.txt
3. Create a .env file and add GOOGLE_AI_KEY and DISCORD_BOT_TOKEN in as specified in .env.development file
4. Run as `python bot.py`

## Commands
`/forget` - erases the chat history
`/bing-prompt` - creates an image using Bing
`/bing-prompt-pro` - creates an image using Gemini revise prompt and create Image with Bing

## Running

Clone repository

Install all dependencies as specified in requirements.txt

Create a .env file and add GOOGLE_AI_KEY and DISCORD_BOT_TOKEN in as specified in .env.development file

Run as `python bot.py`

## Customization

Optionally, you can configure the bot as follows using config.py:

Add custom initial conversation for every chat by editing the bot_template variable as follows:

```
bot_template = [
	{'role':'user','parts': ["Hi!"]},
	{'role':'model','parts': ["Hello! I am a Discord bot!"]},
	{'role':'user','parts': ["Please give short and concise answers!"]},
	{'role':'model','parts': ["I will try my best!"]},
]
```

Change content safety settings as follows:
```
safety_settings = [
	{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
	{"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
	{"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
	{"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
]
```

Change AI generation parameters using the variables text_generation_config and image_generation_config

Error logs are stored in the errors.log file created at runtime.
