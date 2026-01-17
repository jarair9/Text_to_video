import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from mistralai import Mistral
from dotenv import dotenv_values
from Models.config import SAVE_SCRIPT_TO
from Models.Script.utils import SYSTEM_PROMPT

class ScriptGenerator:
    def __init__(self):
        env_vars = dotenv_values(".env")
        self.api_key = env_vars.get("MISTRAL_API_KEY")
        self.base_url = "https://api.mistral.ai/v1"
        
        if not self.api_key:
            raise ValueError("❌ MISTRAL_API_KEY not found. Check your .env file.")
        
        # Initialize Mistral AI client
        self.client = Mistral(api_key=self.api_key)
        
        os.makedirs(os.path.dirname(SAVE_SCRIPT_TO), exist_ok=True)

    def generate_script(self, topic):
        """Generates a script based on the given topic using Mistral AI."""
        try:
            response = self.client.chat.complete(
                model="mistral-large-latest",  # or "mistral-medium" or "mistral-small"
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": topic}
                ],
                temperature=0.7,
                top_p=0.9,
                max_tokens=1000
            )
            
            script_text = response.choices[0].message.content
            with open(SAVE_SCRIPT_TO, "w", encoding="utf-8") as f:
                f.write(script_text) 
            return script_text
            
        except Exception as e:
            print(f"❌ Error generating script with Mistral AI: {str(e)}")
            # Fallback to a basic script if Mistral fails
            fallback_script = f"This is a video about {topic}. The content would discuss various aspects of this topic in an engaging way."
            with open(SAVE_SCRIPT_TO, "w", encoding="utf-8") as f:
                f.write(fallback_script)
            return fallback_script


if __name__ == "__main__":
    generator = ScriptGenerator()
    topic = input("Enter a topic: ")
    script = generator.generate_script(topic)
    print("📝 Generated Script Successfully to:", SAVE_SCRIPT_TO)