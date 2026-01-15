import os
import json
import numpy as np
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
from Models.Captions.utils import load_caption_style, create_text_image
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from config import CAPTION_STYLE
from Models.config import SAVE_VOICEOVER_TO

def generate_video_path(video_path, suffix="_captioned"):
    """Generate an output path based on input video path."""
    file_name = os.path.basename(video_path)
    name_without_ext = os.path.splitext(file_name)[0]
    extension = os.path.splitext(file_name)[1]
    return f"Video/{name_without_ext}{suffix}{extension}"

def extract_audio(video_path, audio_path=None):
    """Extract audio from video file."""
    if audio_path is None:
        voiceover_dir = os.path.dirname(SAVE_VOICEOVER_TO)
        audio_path = os.path.join(voiceover_dir, "temp_audio.wav")
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return None
        
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path, codec="pcm_s16le")
    return audio_path

def add_animated_word_captions(video_path, timestamps_file, output_path=None, style_name=None):
    """Adds word-by-word animated captions to video."""
    if not os.path.exists(video_path) or not os.path.exists(timestamps_file):
        print(f"❌ File(s) not found: {video_path} or {timestamps_file}")
        return None
    
    if style_name is None:
        style_name = CAPTION_STYLE
        
    if output_path is None:
        output_path = generate_video_path(video_path)
    
    with open(timestamps_file, "r", encoding="utf-8") as f:
        captions = json.load(f)

    video = VideoFileClip(video_path)
    video_width, video_height = video.size
    
    style = load_caption_style(style_name)
    
    text_clips = []
    current_time = 0.0

    for caption in captions:
        start, end, text = caption.get("start", 0), caption.get("end", 0), caption.get("text", "")
        if not text.strip():
            continue

        # Split sentence into individual words
        words = text.strip().split()
        sentence_duration = end - start
        
        # Calculate time per word
        if len(words) > 0:
            word_duration = sentence_duration / len(words)
        else:
            word_duration = sentence_duration
            words = [text]  # Handle case where split results in empty list
        
        # Create clip for each word
        for i, word in enumerate(words):
            word_start = start + (i * word_duration)
            word_end = word_start + word_duration
            
            # Add space after word except for last word
            display_word = word + (" " if i < len(words) - 1 else "")
            
            text_np = create_text_image(display_word, video_width, video_height, style)

            position = style.get("position", "bottom")
            vertical_offset = style.get("vertical_offset", 300)
            
            if position == "bottom":
                pos = ("center", video_height - vertical_offset)
            elif position == "top":
                pos = ("center", vertical_offset)
            elif position == "center":
                pos = ("center", "center")
            else:
                pos = ("center", video_height - vertical_offset)

            text_clip = (ImageClip(text_np)
                        .set_duration(word_duration)
                        .set_start(word_start)
                        .set_position(pos))

            text_clips.append(text_clip)

    final_video = CompositeVideoClip([video] + text_clips)
    final_video.write_videofile(output_path, fps=video.fps, codec="libx264", preset="ultrafast")

    print(f"✅ Word-by-word captions added! Video saved at {output_path}")
    return output_path

def add_captions_to_video(video_path, timestamps_file, output_path=None, style_name=None):
    """Adds captions to video based on timestamp data."""
    if not os.path.exists(video_path) or not os.path.exists(timestamps_file):
        print(f"❌ File(s) not found: {video_path} or {timestamps_file}")
        return None
    
    if style_name is None:
        style_name = CAPTION_STYLE
        
    if output_path is None:
        output_path = generate_video_path(video_path)
    
    with open(timestamps_file, "r", encoding="utf-8") as f:
        captions = json.load(f)

    video = VideoFileClip(video_path)
    video_width, video_height = video.size
    
    style = load_caption_style(style_name)
    
    text_clips = []

    for caption in captions:
        start, end, text = caption.get("start", 0), caption.get("end", 0), caption.get("text", "")
        if not text.strip():
            continue

        word_duration = end - start
        
        text_np = create_text_image(text, video_width, video_height, style)

        position = style.get("position", "bottom")
        vertical_offset = style.get("vertical_offset", 300)
        
        if position == "bottom":
            pos = ("center", video_height - vertical_offset)
        elif position == "top":
            pos = ("center", vertical_offset)
        elif position == "center":
            pos = ("center", "center")
        else:
            pos = ("center", video_height - vertical_offset)

        text_clip = (ImageClip(text_np)
                    .set_duration(word_duration)
                    .set_start(start)
                    .set_position(pos))

        text_clips.append(text_clip)

    final_video = CompositeVideoClip([video] + text_clips)
    final_video.write_videofile(output_path, fps=video.fps, codec="libx264", preset="ultrafast")

    print(f"✅ Captions added! Video saved at {output_path}")
    return output_path

def process_video(caption_generator, video_path, style_name=None, output_path=None):
    """Generic video processing pipeline for any caption model with word-by-word animation."""
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return None
        
    if style_name is None:
        style_name = CAPTION_STYLE

    if output_path is None:
        output_path = generate_video_path(video_path)
    
    print(f"\n⏳ Extracting audio from '{os.path.basename(video_path)}'...")
    audio_path = extract_audio(video_path)
    if not audio_path:
        return None
    
    print(f"\n⏳ Generating word-level timestamps...")
    timestamps_file = caption_generator.generate_word_timestamps(audio_path)
    if not timestamps_file:
        return None
    
    print(f"\n⏳ Adding word-by-word animated captions with '{style_name}' style...")
    return add_animated_word_captions(video_path, timestamps_file, output_path, style_name) 