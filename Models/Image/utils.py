import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from Models.config import SAVE_SCRIPT_TO

# Update the System Prompt to be more strict
SYSTEM_PROMPT = (
    "You are a specialized Image Prompt Generator. Your only job is to turn story lines into "
    "technical keyword strings for SDXL Lightning. "
    "\n- OUTPUT ONLY the raw tags. No introductory text."
    "\n- Use keywords like: cinematic, 8k, photorealistic, volumetric lighting, hyper-detailed."
    "\n- Structure: [Subject], [Action], [Environment], [Lighting], [Style]."
)

def ensure_save_directory(filepath):
    """Ensures the directory for a file exists before saving.
    
    Args:
        filepath (str): The full path where the file will be saved
        
    Returns:
        None
    """
    directory = os.path.dirname(filepath)
    if directory:
        os.makedirs(directory, exist_ok=True)

def load_script_lines(script_file=SAVE_SCRIPT_TO):
    """Loads script and splits it into individual lines."""
    if not os.path.exists(script_file):
        print(f"❌ Script file not found: {script_file}")
        return []

    with open(script_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def format_for_image_prompt(script_text):
    """Converts a script into a list of image prompts using tag-based logic."""
    lines = script_text.split('\n')
    image_prompts = []
    
    for line in lines:
        clean_line = line.strip()
        if clean_line:
            # REMOVED: "High quality, photorealistic image of..."
            # ADDED: A tag-based structure that works better with Lightning models
            prompt = (
                f"{clean_line}, cinematic shot, 8k resolution, "
                f"highly detailed textures, masterpiece, sharp focus, "
                f"dramatic lighting, photorealistic style"
            )
            image_prompts.append(prompt)
    
    return image_prompts