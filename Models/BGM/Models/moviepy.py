import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
sys.dont_write_bytecode = True
from moviepy.editor import *
from Models.config import SAVE_VIDEO_TO
from Models.BGM.utils import ensure_bgm_directory


class BGMGenerator:
    def __init__(self):
        self.default_volume = 0.3  # Default BGM volume (30% of original)
        self.default_video_path = SAVE_VIDEO_TO
        ensure_bgm_directory(self.default_video_path)

    def add_background_music(self, video_path=None, bgm_path=None, output_path=None, 
                           bgm_volume=0.3, voiceover_volume=1.0):
        """Add background music to a video with the main audio (voiceover).
        
        Args:
            video_path (str): Path to the input video with voiceover
            bgm_path (str): Path to the background music file
            output_path (str): Path for the output video with BGM
            bgm_volume (float): Volume level for background music (0.0 to 1.0)
            voiceover_volume (float): Volume level for voiceover (0.0 to 1.0)
            
        Returns:
            str: Path to the output video with BGM added
        """
        if video_path is None:
            video_path = self.default_video_path
            
        if output_path is None:
            name_parts = os.path.splitext(video_path)
            output_path = f"{name_parts[0]}_with_bgm{name_parts[1]}"
        
        print(f"🎵 Adding background music to video: {os.path.basename(video_path)}")
        
        # Load the video
        video = VideoFileClip(video_path)
        
        # If no BGM path is provided, return the original video
        if bgm_path is None or not os.path.exists(bgm_path):
            print("⚠️ No BGM file provided or BGM file not found. Returning original video.")
            return video_path
        
        # Load the background music
        bgm = AudioFileClip(bgm_path)
        
        # Adjust volumes
        bgm = bgm.volumex(bgm_volume)
        voiceover_audio = video.audio.volumex(voiceover_volume)
        
        # Handle BGM duration relative to video duration
        video_duration = video.duration
        bgm_duration = bgm.duration
        
        if bgm_duration < video_duration:
            # If BGM is shorter than video, loop it seamlessly to cover the full video duration
            loops_needed = int(video_duration / bgm_duration) + 1
            bgm_looped = concatenate_audioclips([bgm] * loops_needed)
            # Trim to exact video duration
            bgm_final = bgm_looped.subclip(0, video_duration)
        elif bgm_duration > video_duration:
            # If BGM is longer than video, trim it to video duration
            bgm_final = bgm.subclip(0, video_duration)
        else:
            # If durations match exactly
            bgm_final = bgm
        
        # Mix the voiceover audio with the background music
        # Lower the BGM volume to not overpower the voiceover
        mixed_audio = CompositeAudioClip([voiceover_audio, bgm_final])
        
        # Set the mixed audio to the video
        final_video = video.set_audio(mixed_audio)
        
        # Write the final video with BGM added
        final_video.write_videofile(output_path, 
                                   temp_audiofile="temp-audio.m4a", 
                                   remove_temp=True,
                                   codec="libx264", 
                                   audio_codec="aac")
        
        print(f"✅ Video with background music saved as: {output_path}")
        
        # Close clips to free memory
        video.close()
        bgm.close()
        final_video.close()
        
        return output_path


if __name__ == "__main__":
    generator = BGMGenerator()
    video_path = input("Enter video path: ")
    bgm_path = input("Enter BGM path: ")
    output_path = input("Enter output path (or press Enter for default): ") or None
    generator.add_background_music(video_path, bgm_path, output_path)