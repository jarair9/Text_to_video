from Models.config import SAVE_SCRIPT_TO
import re
import os
SYSTEM_PROMPT = (
    "You are a skilled storyteller who creates engaging, viral content for YouTube Shorts and TikTok. "
    "Write a compelling 30-45 second script about [TOPIC] that captivates viewers from the start. "
    "Begin with a strong hook that immediately grabs attention and draws the audience in. "
    "Tell a fast-paced, narrative-driven story with a clear takeaway or surprising insight. "
    "Use conversational, punchy language that resonates with a broad audience—avoid complex jargon. "
    "End with a memorable closing line that encourages reflection or action. "
    "STRICT FORMATTING: Output must be plain text in a single paragraph format. "
    "No line breaks, stage directions, bullet points, or labels. "
    "Example: You're scrolling through your phone and see the same post from three different friends. "
    "Suddenly you realize social media isn't connecting you—it's conditioning you. "
    "Every like trains your brain to seek validation from strangers instead of building real relationships. "
    "Your phone isn't a window to the world; it's a mirror reflecting your deepest insecurities. "
    "When was the last time you felt truly connected without a screen between you and another person?"
)

def format_script(text):
    """Formats the script for better readability."""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\(.*?\)', '', text)
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    formatted_script = "\n".join(sentence.strip() for sentence in sentences if sentence.strip())
    return formatted_script

def save_formatted_script(script_text, file_path=None):
    """Saves the formatted script to a file."""
    if file_path is None:
        file_path = SAVE_SCRIPT_TO
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    formatted_text = format_script(script_text)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(formatted_text)
    
    return formatted_text
