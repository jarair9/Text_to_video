import sys
import os
import requests
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
sys.dont_write_bytecode = True
from Models.config import SAVE_IMAGES_TO
from Models.Image.utils import ensure_save_directory


class ImageGenerator:
    def __init__(self):
        self.prompt_generator = None
        # Cloudflare Direct API Configuration
        self.account_id = "0c27843ed41f48522815727e4fbf5c3c"  # Your Account ID
        self.auth_token = "6GFEGqXK55bHnm90r3kWUOLnJSk4-kviMH7u2Was"   # Your API Token
        self.api_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/@cf/bytedance/stable-diffusion-xl-lightning"
        
        # Cloudflare Direct API headers
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
    def set_prompt_generator(self, prompt_generator):
        self.prompt_generator = prompt_generator
        
    def generate_image_prompt(self, text):
        if self.prompt_generator:
            return self.prompt_generator.generate_prompt(text)
        else:
            return text
            
    def download_image(self, prompt, img_number):
        print(f"🎨 Generating image {img_number} with prompt: {prompt}")
        
        # Optimize prompt for Cloudflare Direct API
        # Extract the core subject from the tag-based prompt
        core_subject = prompt.split(',')[0]  # Get the first part before commas
        optimized_prompt = core_subject[:100]  # Limit length for API
        
        # Cloudflare Direct API payload format
        payload = {
            "prompt": optimized_prompt,
            "num_steps": 4,      # Fast inference
            "width": 768,        # 9:16 aspect ratio width
            "height": 1024       # 9:16 aspect ratio height
        }
        
        max_retries = 2  # Reduced retries for Cloudflare
        retry_delay = 3  # Shorter delay for faster feedback
        
        for attempt in range(max_retries):
            try:
                # Use the already optimized headers
                response = requests.post(
                    self.api_url, 
                    json=payload, 
                    headers=self.headers,
                    timeout=300,  # Cloudflare Direct API allows longer timeouts
                    stream=True   # Stream for better memory handling
                )
                response.raise_for_status()
                
                filename = os.path.join(SAVE_IMAGES_TO, f"image_{img_number}.jpg")
                ensure_save_directory(os.path.dirname(filename))
                
                # Stream and save the image for better memory management
                with open(filename, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                    
                print(f"✅ Image {img_number} saved successfully as {filename}")
                print(f"⏱️  Generated with full prompt length")
                return  # Success, exit retry loop
                
            except requests.exceptions.HTTPError as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ HTTP Error on attempt {attempt + 1}/{max_retries}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    print(f"❌ HTTP Error for image {img_number} after {max_retries} attempts: {e}")
                    print(f"Response: {response.text if response else 'No response'}")
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"⚠️ Timeout on attempt {attempt + 1}/{max_retries}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    print(f"❌ Timeout error for image {img_number} after {max_retries} attempts")
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Error on attempt {attempt + 1}/{max_retries}: {e}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    print(f"❌ Error generating image {img_number} after {max_retries} attempts: {e}")

    def generate_images_from_script(self, script_lines):
        for i, line in enumerate(script_lines, start=1):
            print(f"🎨 Generating prompt for line {i}/{len(script_lines)}...")
            image_prompt = self.generate_image_prompt(line)
            print(f"📜 Prompt {i}: {image_prompt}")
            
            self.download_image(image_prompt, i)
            time.sleep(1)  # Small delay to be respectful to the API
