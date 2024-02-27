from typing import List
from BingImageCreator import ImageGen 
from dotenv import load_dotenv
import os

load_dotenv()

BING_TOKEN = os.getenv("BING_TOKEN")

def create_image(prompt:str) -> List[str]:
    cookie = BING_TOKEN
    # print(cookie)
    image_gen = ImageGen(cookie)
    images = image_gen.get_images(prompt)
    return images
