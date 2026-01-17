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
        """Generate basic timestamps based on the audio duration and script, with timing estimated from word count and adjusted to match audio length."""
        if not os.path.exists(audio_path):
            print(f"❌ Audio file not found: {audio_path}")
            return None

        # Load audio to get duration
        audio_clip = AudioFileClip(audio_path)
        total_duration = audio_clip.duration
        audio_clip.close()

        # Load the formatted script (already split into lines)
        from Models.config import SAVE_SCRIPT_TO
        with open(SAVE_SCRIPT_TO, 'r', encoding='utf-8') as f:
            formatted_script = f.read()
        
        # Split by newlines to get the properly formatted segments
        sentences = [s.strip() for s in formatted_script.split('\n') if s.strip()]
        
        if not sentences:
            return None

        # Estimate duration based on typical speaking rate (words per minute) rather than just character count
        # Average speaking rate is about 150-180 words per minute, so roughly 2.5-3 words per second
        # We'll use 2.5 words per second (0.4 seconds per word) as our base rate
        words_per_second = 2.5
        
        # Calculate total word count for all sentences to determine proportional timing
        total_words = 0
        sentence_word_counts = []
        for sentence in sentences:
            word_count = len(sentence.split())
            sentence_word_counts.append(word_count)
            total_words += word_count
        
        if total_words == 0:
            return None

        words_data = []
        current_time = 0.0
        
        for i, sentence in enumerate(sentences):
            if not sentence:
                continue
            
            # Calculate duration based on word count for this sentence
            sentence_word_count = sentence_word_counts[i]
            sentence_duration = (sentence_word_count / words_per_second)
            
            # Adjust sentence duration proportionally so total matches audio duration
            # This ensures the captions align with the actual audio length
            estimated_total_duration = (total_words / words_per_second)
            if estimated_total_duration > 0:
                adjustment_factor = total_duration / estimated_total_duration
                sentence_duration *= adjustment_factor
            
            # Ensure minimum duration to prevent zero-length clips
            min_duration = 0.5  # Minimum 0.5 seconds per caption
            sentence_duration = max(sentence_duration, min_duration)
            
            start_time = current_time
            end_time = current_time + sentence_duration
            current_time = end_time
            
            # Only add if sentence is not empty
            if sentence:
                words_data.append({
                    "start": start_time,
                    "end": end_time,
                    "text": sentence  # Don't add period since it's already in the formatted text
                })

        # Adjust timing to ensure it matches the audio duration more accurately
        if words_data and len(words_data) > 0:
            actual_total_duration = words_data[-1]["end"]
            
            if actual_total_duration > 0:
                # Calculate adjustment factor to match audio duration
                duration_adjustment_factor = total_duration / actual_total_duration
                
                # Apply adjustment to all segments
                adjusted_current_time = 0.0
                for j, caption in enumerate(words_data):
                    original_duration = caption["end"] - caption["start"]
                    adjusted_duration = original_duration * duration_adjustment_factor
                    
                    caption["start"] = adjusted_current_time
                    adjusted_current_time += adjusted_duration
                    caption["end"] = adjusted_current_time
                    
                    # Ensure minimum duration after adjustment
                    min_duration = 0.5
                    if caption["end"] - caption["start"] < min_duration:
                        caption["end"] = caption["start"] + min_duration
                        adjusted_current_time = caption["end"]

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