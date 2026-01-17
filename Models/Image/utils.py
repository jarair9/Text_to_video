import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from Models.config import SAVE_SCRIPT_TO

# Update the System Prompt to be more strict
SYSTEM_PROMPT = (
    "You are an expert at converting scene descriptions into detailed image generation prompts. "
    "Create vivid, descriptive prompts that capture the key visual elements and mood of the scene. "
    "Focus on visual details, style, lighting, and composition. "
    "Include technical terms like: cinematic, 8k, photorealistic, highly detailed, sharp focus, dramatic lighting, masterpiece, atmospheric. "
    "Keep prompts under 120 characters for API compatibility."
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
    """Converts a script into a list of image prompts using descriptive visual logic."""
    lines = script_text.split('\n')
    image_prompts = []
    
    for line in lines:
        clean_line = line.strip()
        if clean_line:
            # Transform narrative text into visual descriptions
            # Focus on what the viewer sees, not abstract concepts
            prompt = f"Cinematic, ultra detailed, 8k, photorealistic image of {clean_line}, professional photography, sharp focus, dramatic lighting, masterpiece, atmospheric"
            image_prompts.append(prompt)
    
    return image_prompts