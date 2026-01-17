import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from mistralai import Mistral
from dotenv import dotenv_values
from Models.Image.utils import SYSTEM_PROMPT
from Models.config import SAVE_SCRIPT_TO
from config import PROMPT_MODEL_TYPE


class PromptGenerator:
    def __init__(self):
        env_vars = dotenv_values(".env")
        self.api_key = env_vars.get("MISTRAL_API_KEY")
        
        if not self.api_key:
            raise ValueError("❌ MISTRAL_API_KEY not found. Check your .env file.")

        self.client = Mistral(api_key=self.api_key)

    def generate_prompt(self, scene_text):
        """Generates an image prompt based on the scene text."""
        Generated_Script = open(SAVE_SCRIPT_TO, "r").read()
        
        full_prompt = f"{SYSTEM_PROMPT}\n\nScript: {Generated_Script}\n\nScene: {scene_text}\n\nGenerate an image prompt:"
        response = self.client.chat.complete(
            model=PROMPT_MODEL_TYPE,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        return response.choices[0].message.content


if __name__ == "__main__":
    prompt_generator = PromptGenerator()
    prompt = prompt_generator.generate_prompt("A beautiful sunset landscape.")
    print(prompt)