import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from openai import OpenAI
from dotenv import dotenv_values
from Models.config import SAVE_SCRIPT_TO
from Models.Script.utils import SYSTEM_PROMPT
from config import SCRIPT_MODEL_TYPE


class ScriptGenerator:
    def __init__(self):
        env_vars = dotenv_values(".env")
        self.api_key = env_vars.get("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        
        if not self.api_key:
            raise ValueError("❌ OPENROUTER_API_KEY not found. Check your .env file.")

        # Initialize OpenAI client without potential proxy conflicts
        # This avoids the 'proxies' argument error in certain OpenAI library versions
        import httpx
        http_client = httpx.Client()
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, http_client=http_client)

        os.makedirs(os.path.dirname(SAVE_SCRIPT_TO), exist_ok=True)

    def generate_script(self, topic):
        """Generates a script based on the given topic."""
        # Prepare the payload with appropriate parameters for OpenRouter
        # Some models (especially free ones) may have different parameter requirements
        response = self.client.chat.completions.create(
            model=SCRIPT_MODEL_TYPE,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": topic}
            ],
            temperature=0.7,  # Reduced from 1.2 for better reliability with free models
            top_p=0.9,
            max_tokens=1000,
            stream=False
        )
        
        script_text = response.choices[0].message.content
        with open(SAVE_SCRIPT_TO, "w", encoding="utf-8") as f:
            f.write(script_text) 
        return script_text


if __name__ == "__main__":
    generator = ScriptGenerator()
    topic = input("Enter a topic: ")
    script = generator.generate_script(topic)
    print("📝 Generated Script Successfully to:", SAVE_SCRIPT_TO)