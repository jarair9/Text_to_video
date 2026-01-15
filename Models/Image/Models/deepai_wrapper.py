import requests
import hashlib
import random
import time
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
sys.dont_write_bytecode = True
from Models.config import SAVE_IMAGES_TO
from Models.Image.utils import ensure_save_directory

class DeepAI:
    def __init__(self, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'):
        self.user_agent = user_agent
        self.base_url = "https://api.deepai.org/api/text2img"
        # Generate API key once at initialization and reuse it
        self.api_key = self._get_api_key()
        print(f"🔑 Generated DeepAI API Key: {self.api_key}")

    def _reverse_md5(self, s):
        """Standard MD5 but returns the reversed hexdigest."""
        return hashlib.md5(s.encode('utf-8')).hexdigest()[::-1]

    def _get_api_key(self):
        """
        Reverse engineered key generation logic.
        JS Logic:
        tryit-{random}-{h3}
        where:
        h1 = rev_md5(ua + random + salt)
        h2 = rev_md5(ua + h1)
        h3 = rev_md5(ua + h2)
        """
        random_str = str(round(random.random() * 100000000000))
        salt = 'hackers_become_a_little_stinkier_every_time_they_hack'
        
        h1 = self._reverse_md5(self.user_agent + self._reverse_md5(self.user_agent + self._reverse_md5(self.user_agent + random_str + salt)))
        # Wait, re-reading the JS:
        # myhashfunction(navigator.userAgent+myhashfunction(navigator.userAgent+myhashfunction(navigator.userAgent+myrandomstr+'hackers_become_a_little_stinkier_every_time_they_hack')))
        # Inner most: myhashfunction(navigator.userAgent+myrandomstr+'hackers_become_a_little_stinkier_every_time_they_hack')
        # ... actually looking at the nesting:
        # inner = myhashfunction(navigator.userAgent + myrandomstr + salt)
        # middle = myhashfunction(navigator.userAgent + inner)
        # outer = myhashfunction(navigator.userAgent + middle)
        # return tryit-{random}-{outer}
        
        # Let's correctness check the JS snippet I read:
        # myhashfunction(
        #   navigator.userAgent + myhashfunction(
        #     navigator.userAgent + myhashfunction(
        #       navigator.userAgent + myrandomstr + 'hackers_become_a_little_stinkier_every_time_they_hack'
        #     )
        #   )
        # )
        
        inner = self._reverse_md5(self.user_agent + random_str + salt)
        middle = self._reverse_md5(self.user_agent + inner)
        outer = self._reverse_md5(self.user_agent + middle)
        
        return f'tryit-{random_str}-{outer}'

    def generate(self, prompt, width=512, height=512, grid_size=1):
        """
        Generates an image.
        """
        headers = {
            'User-Agent': self.user_agent,
            'api-key': self.api_key,  # Use the persistent API key
            # Origin and Referer might be needed
            'Origin': 'https://deepai.org',
            'Referer': 'https://deepai.org/machine-learning-model/text2img'
        }
        
        # Determine closest standard dimensions or send as is
        # The API seems to accept width/height directly in some modes, or likely ignored if not 'hd'.
        
        data = {
            'text': prompt,
            'grid_size': str(grid_size),
            'width': str(width),
            'height': str(height),
            'image_generator_version': 'standard', # Using 'standard' instead of 'hd' to avoid auth issues
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                print(f"❌ 401 Unauthorized. Response: {response.text}")
                print(f"❌ Headers sent: {headers}")
                print(f"❌ Data sent: {data}")
                return {'error': 'Unauthorized. API Key generation might have failed.', 'response': response.text}
            return {'error': f"HTTP Error: {e}", 'details': response.text}
        except Exception as e:
            return {'error': f"Unexpected Error: {e}"}

if __name__ == "__main__":
    # verification
    bot = DeepAI()
    print("Generating image...")
    result = bot.generate("A futuristic city optimized for aesthetics", width=800, height=600)
    print(result)

class ImageGenerator:
    def __init__(self):
        self.prompt_generator = None
        self.client = DeepAI()

    def set_prompt_generator(self, prompt_generator):
        self.prompt_generator = prompt_generator

    def generate_image_prompt(self, text):
        if self.prompt_generator:
            return self.prompt_generator.generate_prompt(text)
        else:
            return text

    def download_image(self, prompt, img_number):
        print(f"🎨 Generating image {img_number} with prompt: {prompt}")
        max_retries = 3
        retry_delay = 3
        
        for attempt in range(max_retries):
            try:
                # Attempt to use 9:16 aspect ratio
                # DeepAI Free might not respect custom resolutions fully, but we try.
                response_json = self.client.generate(prompt, width=1024, height=1820)
                
                if 'output_url' in response_json:
                    image_url = response_json['output_url']
                    
                    img_response = requests.get(image_url)
                    if img_response.status_code == 200:
                        filename = os.path.join(SAVE_IMAGES_TO, f"image_{img_number}.jpg")
                        ensure_save_directory(os.path.dirname(filename))
                        with open(filename, "wb") as file:
                            file.write(img_response.content)
                        print(f"✅ Image {img_number} saved successfully as {filename}")
                        return  # Success, exit retry loop
                    else:
                        print(f"❌ Failed to download image from URL: {image_url}")
                elif 'error' in response_json and attempt < max_retries - 1:
                    print(f"⚠️ Attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"❌ DeepAI Error: {response_json}")
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Error on attempt {attempt + 1}: {e}, retrying...")
                    time.sleep(retry_delay)
                else:
                    print(f"❌ Error generating image {img_number} after {max_retries} attempts: {e}")

    def generate_images_from_script(self, script_lines):
        for i, line in enumerate(script_lines, start=1):
            print(f"🎨 Generating prompt for line {i}/{len(script_lines)}...")
            image_prompt = self.generate_image_prompt(line)
            print(f"📜 Prompt {i}: {image_prompt}")
            
            self.download_image(image_prompt, i)
            time.sleep(3) # Be nice to the API, increased delay to avoid rate limiting
