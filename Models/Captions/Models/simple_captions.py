import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
sys.dont_write_bytecode = True
from moviepy.editor import *
from Models.config import SAVE_TIMESTAMPS_TO, SAVE_VOICEOVER_TO
from Models.Captions.caption_processor import process_video as process_with_captions
from Models.Captions.utils import get_available_caption_styles, get_available_fonts
from config import CAPTION_STYLE
from Models.Captions.utils import load_caption_style, create_text_image
import numpy as np
from PIL import Image as PILImage


class CaptionGenerator:
    def __init__(self):
        pass

    def generate_word_timestamps(self, audio_path, output_json=SAVE_TIMESTAMPS_TO):
        """Generate basic timestamps based on the audio duration and script."""
        if not os.path.exists(audio_path):
            print(f"❌ Audio file not found: {audio_path}")
            return None

        # Load audio to get duration
        audio_clip = AudioFileClip(audio_path)
        total_duration = audio_clip.duration
        audio_clip.close()

        # Load the script to create basic segment timestamps
        from Models.config import SAVE_SCRIPT_TO
        with open(SAVE_SCRIPT_TO, 'r', encoding='utf-8') as f:
            script_text = f.read()

        # Split script into sentences for basic timing
        sentences = [s.strip() for s in script_text.split('.') if s.strip()]
        
        if not sentences:
            return None

        # Calculate duration per sentence
        duration_per_sentence = total_duration / len(sentences)
        
        words_data = []
        current_time = 0.0
        
        for i, sentence in enumerate(sentences):
            start_time = current_time
            end_time = current_time + duration_per_sentence
            current_time = end_time
            
            # Only add if sentence is not empty
            if sentence:
                words_data.append({
                    "start": start_time,
                    "end": end_time,
                    "text": sentence + "."
                })

        # Save to JSON
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(words_data, f, indent=4)

        print(f"✅ Basic timestamps saved to {output_json} ({len(words_data)} segments)")
        return output_json

    def process_video(self, video_path, style_name=None, output_path=None):
        """Process video with captions using the centralized processor."""
        if style_name is None:
            style_name = CAPTION_STYLE
            
        return process_with_captions(self, video_path, style_name, output_path)

    def get_available_styles(self):
        """Lists all available caption styles"""
        styles = get_available_caption_styles()
        print(f"\n📚 Available caption styles:")
        for style in styles:
            marker = "✓" if style == CAPTION_STYLE else " "
            print(f" [{marker}] {style}")
        return styles
        
    def get_available_fonts(self):
        """Lists all available fonts"""
        fonts = get_available_fonts()
        print(f"\n🔠 Available fonts:")
        for font in fonts:
            print(f" - {font}")
        return fonts


if __name__ == "__main__":
    caption_generator = CaptionGenerator()
    
    available_styles = caption_generator.get_available_styles()
    available_fonts = caption_generator.get_available_fonts()
    
    video_path = input("\nEnter video path: ")
    print(f"Using caption style: {CAPTION_STYLE}")
    
    use_different_style = input(f"Would you like to use a different style? (y/n): ").lower() == 'y'
    
    if use_different_style and available_styles:
        style_name = input(f"Enter style name ({', '.join(available_styles)}): ") or CAPTION_STYLE
    else:
        style_name = CAPTION_STYLE
        
    caption_generator.process_video(video_path, style_name)