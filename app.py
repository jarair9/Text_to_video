import streamlit as st
import os
import sys
import logging
from pathlib import Path
import traceback
import time
import threading
from io import StringIO

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from Models.Script.script_factory import load_script_model
from Models.Voiceover.voiceover_factory import load_voiceover_model
from Models.Image.image_factory import load_image_model
from Models.Video.video_factory import load_video_model
from Models.Captions.captions_factory import load_caption_model
from Models.Script.utils import save_formatted_script
from Models.Image.utils import format_for_image_prompt
from Models.BGM.bgm_factory import load_bgm_model
from config import (
    SCRIPT_MODEL, IMG_MODEL, AUDIO_MODEL, CAPTION_MODEL, 
    CAPTION_STYLE, BGM_ENABLED, BGM_PATH, BGM_MODEL, ANIMATION
)
from progress_tracker import ProgressTracker, Stage


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_generation_pipeline(topic, script_model, img_model, audio_model, caption_model, animation, audio_voice, caption_style, include_captions=True, include_bgm=True, bgm_enabled=True, bgm_volume=0.3, progress_callback=None):
    """Run the text-to-video generation pipeline with custom configuration."""
    try:
        # Import config module to temporarily update settings
        import importlib
        import importlib.util
        spec = importlib.util.spec_from_file_location("config", "config.py")
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        
        # Also import the config values directly for this function
        from config import BGM_PATH as original_bgm_path
        
        # Temporarily update configuration values
        original_script_model = config.SCRIPT_MODEL
        original_img_model = config.IMG_MODEL
        original_audio_model = config.AUDIO_MODEL
        original_caption_model = config.CAPTION_MODEL
        original_animation = config.ANIMATION
        original_audio_voice = config.AUDIO_MODEL_VOICE
        original_caption_style = config.CAPTION_STYLE
        original_bgm_enabled = config.BGM_ENABLED
        original_bgm_volume = config.BGM_VOLUME
        
        config.SCRIPT_MODEL = script_model
        config.IMG_MODEL = img_model
        config.AUDIO_MODEL = audio_model
        config.CAPTION_MODEL = caption_model
        config.ANIMATION = animation
        config.AUDIO_MODEL_VOICE = audio_voice
        config.CAPTION_STYLE = caption_style
        config.BGM_ENABLED = bgm_enabled
        config.BGM_VOLUME = bgm_volume
        
        # Update sys.modules to make the changes available globally
        sys.modules['config'] = config
        
        # Ensure temp folders exist
        for folder in ["Script", "Voiceover", "Generated_Images", "Video", "Timestamps"]:
            folder_path = Path("Data/Temp") / folder
            folder_path.mkdir(parents=True, exist_ok=True)

        # Initialize progress tracker
        tracker = ProgressTracker(topic)
        
        # Update callback if provided
        if progress_callback:
            progress_callback("Starting script generation...", 10)

        # 1. Generate Script
        tracker.update_stage(Stage.SCRIPT)
        script_generator = load_script_model()
        script = script_generator.generate_script(topic)
        
        if progress_callback:
            progress_callback("Script generated, synthesizing voiceover...", 20)

        # 2. Generate Voiceover
        tracker.update_stage(Stage.VOICEOVER)
        voiceover_generator = load_voiceover_model()
        audio_path = voiceover_generator.generate_voiceover(script)

        # 3. Format script for image generation
        tracker.update_stage(Stage.IMAGE_PREP)
        formatted_script = save_formatted_script(script)
        
        # 4. Format script for image prompts
        image_prompts = format_for_image_prompt(formatted_script)

        # 5. Generate Images
        tracker.update_stage(Stage.IMAGE_GEN)
        image_generator = load_image_model()
        image_paths = []
        
        for i, prompt in enumerate(image_prompts):
            if progress_callback:
                progress_callback(f"Generating image {i+1}/{len(image_prompts)}", 30 + (i * 10))
            image_path = f"image_{i+1}.jpg"
            try:
                image_generator.download_image(prompt, i+1)
                image_paths.append(image_path)
            except Exception as e:
                st.error(f"Error generating image {i+1}: {str(e)}")
            time.sleep(1)

        # 6. Generate Video
        tracker.update_stage(Stage.VIDEO)
        video_generator = load_video_model()
        video_path = video_generator.generate_video(topic)

        # 7. Add Captions to Video
        if video_path and include_captions:
            tracker.update_stage(Stage.CAPTIONS)
            
            # Handle potential variations in caption model name
            actual_caption_model = caption_model
            if 'whisper' in caption_model.lower() and caption_model.lower() != 'whisperx':
                actual_caption_model = 'whisperx'
            elif 'simple' in caption_model.lower() and caption_model.lower() != 'simple_captions':
                actual_caption_model = 'simple_captions'
            
            caption_generator = load_caption_model(actual_caption_model)
            
            try:
                captioned_video_path = caption_generator.process_video(video_path, caption_style)
                if captioned_video_path:
                    video_path = captioned_video_path
                else:
                    st.warning("Captioning failed, but original video is available")
            except Exception as e:
                st.error(f"Error during captioning: {str(e)}")

        # 8. Add Background Music to Video
        if video_path and bgm_enabled and include_bgm:
            tracker.update_stage(Stage.BGM)
            bgm_generator = load_bgm_model()
            
            try:
                bgm_video_path = bgm_generator.add_background_music(
                    video_path=video_path,
                    bgm_path=original_bgm_path,
                    bgm_volume=bgm_volume,
                    voiceover_volume=1.0
                )
                
                if bgm_video_path:
                    video_path = bgm_video_path
                else:
                    st.warning("BGM addition failed, but video is available without BGM")
            except Exception as e:
                st.error(f"Error during BGM addition: {str(e)}")

        # Complete the process
        tracker.complete(video_path if video_path else None)
        
        if progress_callback:
            progress_callback("Video generation complete!", 100)
        
        # Restore original configuration values
        config.SCRIPT_MODEL = original_script_model
        config.IMG_MODEL = original_img_model
        config.AUDIO_MODEL = original_audio_model
        config.CAPTION_MODEL = original_caption_model
        config.ANIMATION = original_animation
        config.AUDIO_MODEL_VOICE = original_audio_voice
        config.CAPTION_STYLE = original_caption_style
        config.BGM_ENABLED = original_bgm_enabled
        config.BGM_VOLUME = original_bgm_volume
        
        sys.modules['config'] = config
        
        return {
            "success": True,
            "script": formatted_script,
            "audio_path": audio_path,
            "image_paths": image_paths,
            "video_path": video_path
        }

    except Exception as e:
        logger.error(f"Error in generation process: {str(e)}")
        logger.error(traceback.format_exc())
        if progress_callback:
            progress_callback(f"Error: {str(e)}", 0)
        return {
            "success": False,
            "error": str(e)
        }


def main():
    # Import config values inside the main function to ensure they're available
    from config import (
        SCRIPT_MODEL, IMG_MODEL, AUDIO_MODEL, CAPTION_MODEL, 
        CAPTION_STYLE, BGM_ENABLED, BGM_PATH, BGM_MODEL, ANIMATION, 
        AUDIO_MODEL_VOICE, BGM_VOLUME
    )
    
    st.set_page_config(
        page_title="Text-to-Video Generator",
        page_icon="🎬",
        layout="wide"
    )

    st.title("🎬 Text-to-Video Generator")
    st.markdown("""
    Transform your ideas into engaging videos with AI! Enter a topic below and let our system create a complete video with script, voiceover, images, and more.
    """)

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        st.subheader("Model Selection")
        
        # Define available models
        script_models = ["openrouter", "ddc", "gemini"]
        img_models = ["pollinations", "pixelmuse", "custom_api", "deepai_wrapper"]
        audio_models = ["edgetts", "openaifm"]
        caption_models = ["whisperx", "simple_captions"]
        animations = ["fadein_fadeout", "zoom_fade_mix", "zoom_in_out"]
        
        # Handle common variations and ensure current config values are in the lists
        if SCRIPT_MODEL not in script_models:
            script_models.insert(0, SCRIPT_MODEL)
        if IMG_MODEL not in img_models:
            img_models.insert(0, IMG_MODEL)
        if AUDIO_MODEL not in audio_models:
            audio_models.insert(0, AUDIO_MODEL)
        
        # Handle caption model variations (case-insensitive check)
        caption_model_found = False
        for model in caption_models:
            if model.lower() == CAPTION_MODEL.lower():
                caption_model_found = True
                break
        if not caption_model_found:
            # Check for partial matches
            if 'whisper' in CAPTION_MODEL.lower():
                # If user has 'whisper' in config, map to 'whisperx'
                if 'whisperx' not in caption_models:
                    caption_models.insert(0, 'whisperx')
            elif 'simple' in CAPTION_MODEL.lower():
                if 'simple_captions' not in caption_models:
                    caption_models.insert(0, 'simple_captions')
            else:
                caption_models.insert(0, CAPTION_MODEL)
        
        if ANIMATION not in animations:
            animations.insert(0, ANIMATION)
        
        script_model_index = script_models.index(SCRIPT_MODEL) if SCRIPT_MODEL in script_models else 0
        img_model_index = img_models.index(IMG_MODEL) if IMG_MODEL in img_models else 0
        audio_model_index = audio_models.index(AUDIO_MODEL) if AUDIO_MODEL in audio_models else 0
        
        # Find the correct index for caption model
        caption_model_index = 0
        for i, model in enumerate(caption_models):
            if model.lower() == CAPTION_MODEL.lower():
                caption_model_index = i
                break
        
        animation_index = animations.index(ANIMATION) if ANIMATION in animations else 0
        
        script_model = st.selectbox("Script Model", script_models, index=script_model_index)
        img_model = st.selectbox("Image Model", img_models, index=img_model_index)
        audio_model = st.selectbox("Audio Model", audio_models, index=audio_model_index)
        caption_model = st.selectbox("Caption Model", caption_models, index=caption_model_index)
        animation = st.selectbox("Animation Style", animations, index=animation_index)
        
        st.subheader("Model Settings")
        
        # Audio voice selection
        audio_voices = ["en-US-JennyNeural", "en-US-GuyNeural", "en-US-AriaNeural", "en-US-DavisNeural", "en-US-EmmaNeural", "en-US-MichelleNeural"]
        # Ensure the current config value is in the list
        if AUDIO_MODEL_VOICE not in audio_voices:
            audio_voices.insert(0, AUDIO_MODEL_VOICE)  # Add current value at the beginning
        audio_voice_index = audio_voices.index(AUDIO_MODEL_VOICE) if AUDIO_MODEL_VOICE in audio_voices else 0
        audio_voice = st.selectbox("Audio Voice", audio_voices, index=audio_voice_index)
        
        # Caption styles
        caption_styles = ["default", "comic", "horror"]
        # Ensure the current config value is in the list
        if CAPTION_STYLE not in caption_styles:
            caption_styles.insert(0, CAPTION_STYLE)  # Add current value at the beginning
        caption_style_index = caption_styles.index(CAPTION_STYLE) if CAPTION_STYLE in caption_styles else 0
        caption_style = st.selectbox("Caption Style", caption_styles, index=caption_style_index)
        
        st.subheader("Options")
        include_captions = st.checkbox("Include Captions", value=True)
        include_bgm = st.checkbox("Include Background Music", value=True)
        
        # BGM settings
        if include_bgm:
            bgm_enabled = st.checkbox("Enable Background Music", value=BGM_ENABLED)
            bgm_volume = st.slider("BGM Volume", min_value=0.0, max_value=1.0, value=BGM_VOLUME, step=0.1)
        else:
            bgm_enabled = False
            bgm_volume = BGM_VOLUME
        
        st.subheader("About")
        st.info("This application generates short-form videos using AI. "
                "The process includes script generation, voiceover synthesis, "
                "image creation, and video assembly.")

    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📝 Enter Your Topic")
        
        topic = st.text_area(
            "Describe the topic for your video:",
            height=100,
            placeholder="e.g., The psychology of decision-making, How to boost productivity, The science behind dreams..."
        )
        
        if st.button("🎬 Generate Video", type="primary"):
            if not topic.strip():
                st.error("Please enter a topic for your video.")
            else:
                # Progress container
                progress_container = st.container()
                
                with progress_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                def update_progress(status, percent):
                    progress_bar.progress(percent / 100)
                    status_text.text(status)
                
                # Run the generation pipeline
                result = run_generation_pipeline(
                    topic=topic,
                    script_model=script_model,
                    img_model=img_model,
                    audio_model=audio_model,
                    caption_model=caption_model,
                    animation=animation,
                    audio_voice=audio_voice,
                    caption_style=caption_style,
                    include_captions=include_captions,
                    include_bgm=include_bgm,
                    bgm_enabled=bgm_enabled,
                    bgm_volume=bgm_volume,
                    progress_callback=update_progress
                )
                
                if result["success"]:
                    st.success("🎉 Video generation completed successfully!")
                    
                    # Display results
                    st.header("📄 Generated Content")
                    st.subheader("Script")
                    st.text_area("Generated Script:", value=result["script"], height=200)
                    
                    st.subheader("Download Results")
                    if result["video_path"]:
                        video_path = result["video_path"]
                        # Ensure the video path is accessible
                        if not os.path.exists(video_path):
                            # Try to find the video file in the output directory
                            import glob
                            video_files = glob.glob(os.path.join("Data", "Temp", "Video", "*.mp4"))
                            if video_files:
                                video_path = video_files[0]
                        
                        if os.path.exists(video_path):
                            with open(video_path, "rb") as f:
                                st.download_button(
                                    label="📥 Download Video",
                                    data=f.read(),
                                    file_name=os.path.basename(video_path),
                                    mime="video/mp4"
                                )
                            
                            st.video(video_path)
                        else:
                            st.warning("Video file was not created successfully or could not be located.")
                    else:
                        st.warning("Video file was not created successfully.")
                        
                else:
                    st.error(f"❌ Video generation failed: {result['error']}")
    
    with col2:
        st.header("ℹ️ How It Works")
        st.markdown("""
        1. **Script Generation** - Creates an engaging script based on your topic
        2. **Voiceover Synthesis** - Converts the script to natural-sounding speech
        3. **Image Creation** - Generates relevant images for the script
        4. **Video Assembly** - Combines images with voiceover into a video
        5. **Captions & Effects** - Adds captions and background music (optional)
        """)
        
        st.header("💡 Tips for Best Results")
        st.markdown("""
        - Be specific with your topic
        - Choose topics that work well in 30-45 seconds
        - Topics with visual elements work best
        - Avoid overly complex subjects
        """)


if __name__ == "__main__":
    main()