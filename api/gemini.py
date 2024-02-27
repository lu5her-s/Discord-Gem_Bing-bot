from typing import List
import google.generativeai as genai
import os
import json
from discord import Attachment
from dotenv import load_dotenv

load_dotenv()

max_bytes = 4 * 1024 * 1024  # 4MB

# genai.configure(api_key=os.getenv("GEMINI_KEY"))
GEMINI_KEY = os.getenv("GOOGLE_AI_KEY")
genai.configure(api_key=GEMINI_KEY)
BOT_NAME = os.getenv("BOT_NAME")


def create_client() -> genai.ChatSession:
        # Set up the model
    generation_config = {
        "temperature": 0.9,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 2048,
    }

    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        }
    ]
    history = [
        {
            "role": "user",
            "parts": f'You are {BOT_NAME} a helpful assistant.'
        },
        {
            "role": "model",
            "parts": f'Hello I am {BOT_NAME} a helpful assistant.'
        }
    ]
    data = json.load(open(f'data/{BOT_NAME}.json', encoding='utf-8'))
    for i in data:
        history.append({
            "role": "user",
            "parts": i
        })
        history.append({
            "role": "model",
            "parts": data[i]
        })



    model = genai.GenerativeModel(model_name="gemini-pro",
                                  generation_config=generation_config,
                                  safety_settings=safety_settings)

    return model.start_chat(history=history)


# def log(guild, channel, user):
#     data = json.load(open(f'data/{}.json', encoding='utf-8'))
#     data[channel] = user
#     with open(f'data/{guild}.json', 'w', encoding='utf-8') as f:
#         json.dump(data, f, ensure_ascii=False, indent=4)


async def log(guild, channel, user):
    convers = await create_client()
    api = GEMINI_KEY
    genai.configure(api_key=api)
    await convers.send_message_async(user)
    bot = f"{BOT_NAME}: {convers.last.text}" 
    print(f"==========\n{guild} | {user}\n{guild} | {bot}")
    async with aiofiles.open("bot-log.txt", "a", encoding="utf-8") as file:
        await file.write(f"==========\n{guild} | {user}\n{guild} | {bot}\n")
    data = json.load(open(f"data/{channel}.json", encoding="utf-8"))
    if len(data) >= 50:
        del data[next(iter(data))]
    data[user] = convers.last.text
    with open(f"data/{channel}.json", "w", encoding="utf-8") as file:
        json.dump(data,file, indent=2, ensure_ascii=False)
    return convers


async def reply(message: str, attachments: List[Attachment]) -> str:
    if attachments:
        return await _reply_with_attachments(message, attachments)
    return _reply_only_message(message)


def _reply_only_message(message: str) -> str:
    client = create_client()
    reponse = client.send_message(message)
    return reponse.text


async def _reply_with_attachments(prompt: str, attachments: List[Attachment]) -> str:
    model = genai.GenerativeModel("gemini-pro-vision")
    image = attachments[0]
    image_data = await image.read()

    if image.size > max_bytes:
        return "the image size limitation is 4MB. Please reduce your image size."

    contents = {
        "parts": [
            {"mime_type": "image/jpeg", "data": image_data},
            {
                "text": f"Describe this picture as detailed as possible in order to dalle-3 painting plus this {prompt}"
            },
        ]
    }
    response = model.generate_content(contents=contents)
    return response.text


def rewrite_prompt(prompt: str):
    prompt = f"revise `{prompt}` to a DALL-E prompt, return the content in English only return the scene and detail"
    return _reply_only_message(prompt)
