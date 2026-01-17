import os
import sys
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
sys.dont_write_bytecode = True
from moviepy.editor import *
from moviepy.video.fx.all import crop
from Models.Animations.animations_factory import load_animation_model
from Models.Video.utils import ensure_directories, verify_assets, transcribe_audio_with_script, crop_to_portrait, load_timestamps, load_script_lines
from Models.config import SAVE_VIDEO_TO, VIDEO_FPS, SAVE_TIMESTAMPS_TO, SAVE_SCRIPT_TO, SAVE_VOICEOVER_TO, SAVE_IMAGES_TO
from config import VIDEO_MODEL_CONFIG

class VideoGenerator:
    def __init__(self):
        self.audio_file = SAVE_VOICEOVER_TO
        ensure_directories()
        self.animation = load_animation_model()
        self.config = VIDEO_MODEL_CONFIG
        
    def generate_video(self, topic=None):
        """Generates the video based on the audio and images."""
        print(f"🎬 Starting video generation with config: {self.config}...")
        
        # Check if timestamps already exist (from caption system or previous run)
        if os.path.exists(SAVE_TIMESTAMPS_TO):
            print("✅ Using existing timestamps...")
            timestamps = load_timestamps(SAVE_TIMESTAMPS_TO)
        else:
            # Fallback to Whisper-based timestamp generation
            # But since Whisper is causing numpy issues, we'll try to continue without timestamps
            print("⚠️ No timestamps found, attempting to continue without them...")
            # Load script lines directly and estimate timing
            script_lines = load_script_lines(SAVE_SCRIPT_TO)
            # Create a basic timeline assuming ~2.5 seconds per sentence
            timestamps = []
            current_time = 0.0
            for i, line in enumerate(script_lines):
                if line.strip():
                    duration = max(2.0, 0.5 * len(line.split()))  # At least 2 seconds per segment
                    timestamps.append({
                        "start": current_time,
                        "end": current_time + duration,
                        "text": line.strip()
                    })
                    current_time += duration
            
            # Save the generated timestamps for future use
            os.makedirs(os.path.dirname(SAVE_TIMESTAMPS_TO), exist_ok=True)
            with open(SAVE_TIMESTAMPS_TO, "w", encoding="utf-8") as f:
                json.dump(timestamps, f, indent=4)
            print(f"✅ Estimated timestamps saved to {SAVE_TIMESTAMPS_TO}")
        
        if not verify_assets(timestamps, self.audio_file):
            print("⚠️ Some assets are missing but continuing with available ones...")
        
        image_clips = []
        
        for i, segment in enumerate(timestamps, start=1):
            image_path = f"{SAVE_IMAGES_TO.rstrip('/')}/image_{i}.jpg"
            if not os.path.exists(image_path):
                print(f"⚠️ Warning: Image {image_path} not found, skipping...")
                continue

            duration = segment["end"] - segment["start"]
            image_clip = ImageClip(image_path).set_duration(duration)
            image_clip = image_clip.resize(1.1)
            image_clip = crop_to_portrait(image_clip)
            image_clip = self.animation.apply(image_clip, zoom_in=(i % 2 == 1))
            image_clips.append(image_clip)

        if not image_clips:
            print("❌ Error: No images found to create video")
            return None

        video = concatenate_videoclips(image_clips, method="compose")
        audio = AudioFileClip(self.audio_file)
        video = video.set_audio(audio)

        output_filename = SAVE_VIDEO_TO
        print(f"⏳ Rendering video to {output_filename}...")
        
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        
        preset = "ultrafast" if self.config == "standard" else "medium"
        threads = 4 if self.config == "standard" else 8
        
        video.write_videofile(output_filename, fps=VIDEO_FPS, preset=preset, threads=threads)
        print(f"✅ Video successfully saved as '{output_filename}'")
        return output_filename

if __name__ == "__main__":
    topic = input("Enter the topic: ")
    generator = VideoGenerator()
    generator.generate_video(topic)
