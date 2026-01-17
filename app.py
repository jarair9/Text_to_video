import streamlit as st
import os
import subprocess
import sys
from pathlib import Path
import json
from datetime import datetime
import shutil
import glob

# Configure page
st.set_page_config(
    page_title="Text-to-Video Generator",
    page_icon="🎬",
    layout="wide"
)

# Create necessary directories
os.makedirs("Data/History", exist_ok=True)
os.makedirs("Data/Temp/Video", exist_ok=True)

def get_video_history():
    """Get list of generated videos from history"""
    history_dir = "Data/History"
    videos = []
    
    for file in os.listdir(history_dir):
        if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            filepath = os.path.join(history_dir, file)
            stat = os.stat(filepath)
            videos.append({
                'filename': file,
                'filepath': filepath,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'topic': file.replace('.mp4', '').replace('_video.mp4', '') if file.endswith('.mp4') else file
            })
    
    # Sort by modification date (newest first)
    videos.sort(key=lambda x: x['modified'], reverse=True)
    return videos

def save_generation_log(topic, voice_choice, output_path):
    """Save generation log to history"""
    log_entry = {
        'topic': topic,
        'voice_choice': voice_choice,
        'output_path': output_path,
        'timestamp': datetime.now().isoformat(),
        'status': 'completed'
    }
    
    log_file = os.path.join("Data/History", "generation_log.json")
    logs = []
    
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            logs = json.load(f)
    
    logs.append(log_entry)
    
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)

def delete_video(video_path):
    """Delete video file and associated log"""
    if os.path.exists(video_path):
        os.remove(video_path)
        
        # Also try to remove from Temp folder if it exists there
        temp_video = os.path.join("Data/Temp/Video", os.path.basename(video_path))
        if os.path.exists(temp_video):
            os.remove(temp_video)
        
        # Update log file
        log_file = os.path.join("Data/History", "generation_log.json")
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = json.load(f)
            
            # Remove entries related to this video
            logs = [log for log in logs if log.get('output_path', '') != video_path]
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)

def run_main_script(topic, voice_choice):
    """Run the main.py script with the given topic and voice choice"""
    # Update config with voice choice
    config_path = "config.py"
    
    # Read current config
    with open(config_path, 'r') as f:
        config_content = f.read()
    
    # Update voice choice in config
    if "AUDIO_MODEL_VOICE =" in config_content:
        if voice_choice == "Male":
            new_config = config_content.replace(
                'AUDIO_MODEL_VOICE = "en-US-JennyNeural"', 
                'AUDIO_MODEL_VOICE = "en-US-ChristopherNeural"'
            ).replace(
                'AUDIO_MODEL_VOICE = "en-US-AriaNeural"', 
                'AUDIO_MODEL_VOICE = "en-US-ChristopherNeural"'
            ).replace(
                'AUDIO_MODEL_VOICE = "en-US-ZiraNeural"', 
                'AUDIO_MODEL_VOICE = "en-US-ChristopherNeural"'
            )
        else:  # Female
            new_config = config_content.replace(
                'AUDIO_MODEL_VOICE = "en-US-ChristopherNeural"', 
                'AUDIO_MODEL_VOICE = "en-US-JennyNeural"'
            ).replace(
                'AUDIO_MODEL_VOICE = "en-US-AriaNeural"', 
                'AUDIO_MODEL_VOICE = "en-US-JennyNeural"'
            ).replace(
                'AUDIO_MODEL_VOICE = "en-US-ZiraNeural"', 
                'AUDIO_MODEL_VOICE = "en-US-JennyNeural"'
            )
    else:
        # If AUDIO_MODEL_VOICE line doesn't exist, add it
        new_config = config_content
    
    with open(config_path, 'w') as f:
        f.write(new_config)
    
    # Run main.py with topic
    cmd = [sys.executable, "main.py", "--topic", topic, "--output", f"{topic.replace(' ', '_')}_video.mp4"]
    
    # Create a temporary file to capture output
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_file:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            cwd=os.getcwd()
        )
        
        # Stream output to the temporary file and to Streamlit
        output_lines = []
        for line in process.stdout:
            output_lines.append(line)
            tmp_file.write(line)
            tmp_file.flush()
        
        process.wait()
        tmp_file.flush()
        
        # Move the generated video to history folder
        generated_video = "Data/Temp/Video/output_video.mp4"
        final_video = f"Data/History/{topic.replace(' ', '_')}_video.mp4"
        
        if os.path.exists(generated_video):
            shutil.move(generated_video, final_video)
            save_generation_log(topic, voice_choice, final_video)
            return final_video, "".join(output_lines)
        else:
            # Look for any mp4 file in Temp/Video
            video_files = glob.glob("Data/Temp/Video/*.mp4")
            if video_files:
                shutil.move(video_files[0], final_video)
                save_generation_log(topic, voice_choice, final_video)
                return final_video, "".join(output_lines)
    
    return None, "".join(output_lines)

def main():
    st.title("🎬 Text-to-Video Generator")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["Generate Video", "History"])
    
    with tab1:
        st.header("Create New Video")
        
        # Topic input
        topic = st.text_input("Enter topic for your video", placeholder="e.g., The future of AI, Space exploration, Horror stories...")
        
        # Voice character selection
        col1, col2 = st.columns(2)
        with col1:
            voice_choice = st.radio("Select voice character:", ("Female", "Male"))
        
        if st.button("🎬 Generate Video", type="primary", disabled=not topic.strip()):
            if topic.strip():
                with st.spinner(f"Generating video for '{topic}' with {voice_choice.lower()} voice... This may take several minutes."):
                    try:
                        video_path, output = run_main_script(topic, voice_choice)
                        
                        if video_path and os.path.exists(video_path):
                            st.success(f"✅ Video generated successfully!")
                            
                            # Display video
                            with open(video_path, 'rb') as video_file:
                                video_bytes = video_file.read()
                                st.video(video_bytes)
                            
                            st.info(f"Video saved to: {video_path}")
                        else:
                            st.error(f"❌ Video generation failed. See logs below.")
                            st.code(output)
                            
                    except Exception as e:
                        st.error(f"❌ Error during video generation: {str(e)}")
            else:
                st.warning("Please enter a topic for your video.")
    
    with tab2:
        st.header("Video History")
        
        videos = get_video_history()
        
        if videos:
            for video in videos:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.subheader(video['filename'])
                    st.caption(f"Generated: {video['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
                    st.caption(f"Size: {video['size'] / (1024*1024):.2f} MB")
                
                with col2:
                    if os.path.exists(video['filepath']):
                        with open(video['filepath'], 'rb') as video_file:
                            st.download_button(
                                label="📥 Download",
                                data=video_file,
                                file_name=video['filename'],
                                mime='video/mp4'
                            )
                
                with col3:
                    if st.button(f"🗑️ Delete", key=f"delete_{video['filename']}"):
                        delete_video(video['filepath'])
                        st.rerun()
                
                st.markdown("---")
        else:
            st.info("No videos generated yet. Create your first video in the 'Generate Video' tab!")

if __name__ == "__main__":
    main()