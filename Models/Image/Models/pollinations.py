import sys
import os
import requests
import time
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
sys.dont_write_bytecode = True
from Models.config import SAVE_IMAGES_TO
from config import IMG_MODEL_TYPE
from Models.Image.utils import ensure_save_directory


class ImageGenerator():
    def __init__(self):
        self.prompt_generator = None
        
    def set_prompt_generator(self, prompt_generator):
        self.prompt_generator = prompt_generator
        
    def generate_image_prompt(self, text):
        if self.prompt_generator:
            return self.prompt_generator.generate_prompt(text)
        else:
            return text
            
    def download_image(self, prompt, img_number):
        # Pollinations API endpoint
        url = "https://image.pollinations.ai/prompt/"
        
        # Format the prompt for the API
        formatted_prompt = f"{prompt}, masterpiece, detailed, high quality"
        
        # API parameters with seed for variation
        import random
        # Use the image number to create a deterministic but different seed for each image
        seed = hash(str(img_number) + prompt) % 10000
        params = {
            'prompt': formatted_prompt,
            'width': 1024,
            'height': 1820, # 9:16 aspect ratio for vertical videos (1024x1820)
            'model': IMG_MODEL_TYPE,  # Using the model type from config
            'nologo': 'true',
            'seed': seed  # Adding seed for variation between images
        }
        
        try:
            response = requests.get(url, params=params, timeout=60)
            
            if response.status_code == 200:
                filename = os.path.join(SAVE_IMAGES_TO, f"image_{img_number}.jpg")
                ensure_save_directory(os.path.dirname(filename))
                
                with open(filename, "wb") as file:
                    file.write(response.content)
                    
                print(f"✅ Image {img_number} saved successfully as {filename}")
            else:
                print(f"❌ Failed to fetch image {img_number}. Status Code: {response.status_code}")
                print(f"Response: {response.text}")
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Error downloading image {img_number}: {e}")

    def generate_images_from_script(self, script_lines):
        for i, line in enumerate(script_lines, start=1):
            print(f"🎨 Generating prompt for line {i}/{len(script_lines)}...")
            image_prompt = self.generate_image_prompt(line)
            print(f"📜 Prompt {i}: {image_prompt}")
            
            self.download_image(image_prompt, i)
            time.sleep(1)