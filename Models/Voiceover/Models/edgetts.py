import sys
import os
import asyncio
import edge_tts
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from Models.config import SAVE_VOICEOVER_TO
from config import AUDIO_MODEL_VOICE
from Models.utils import ensure_save_directory
import tempfile
import subprocess
import time

class VoiceOverGenerator:
    def __init__(self):
        ensure_save_directory(SAVE_VOICEOVER_TO)

    def split_text(self, text, max_chars=1000):
        """Split text into chunks of max_chars, breaking at sentence or paragraph boundaries."""
        chunks = []
        current_chunk = ""
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        for para in paragraphs:
            if len(para) <= max_chars:
                if len(current_chunk) + len(para) <= max_chars:
                    current_chunk += para + "\n\n"
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = para + "\n\n"
            else:
                # Split long paragraph into sentences
                sentences = para.split('.')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if sentence:
                        sentence += '.'
                        if len(current_chunk) + len(sentence) <= max_chars:
                            current_chunk += sentence
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = sentence
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

    async def text_to_audio_chunk(self, text, output_path):
        communicate = edge_tts.Communicate(text, AUDIO_MODEL_VOICE)
        await communicate.save(output_path)

    def generate_voiceover(self, text):
        # If text is too long, split it into chunks
        if len(text) > 1000:
            print(f"📝 Text is {len(text)} characters, splitting into chunks...")
            chunks = self.split_text(text, 1000)
            print(f"✂️ Split into {len(chunks)} chunks")
            
            chunk_files = []
            for i, chunk in enumerate(chunks):
                chunk_path = f"{SAVE_VOICEOVER_TO[:-4]}_chunk_{i}.mp3"  # Remove .mp3 and add chunk
                print(f"🔊 Processing chunk {i+1}/{len(chunks)}...")
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.text_to_audio_chunk(chunk, chunk_path))
                loop.close()
                
                chunk_files.append(chunk_path)
                
            # Combine all chunks into the final audio file
            self.combine_audio_chunks(chunk_files, SAVE_VOICEOVER_TO)
            
            # Clean up temporary chunk files
            for chunk_file in chunk_files:
                if os.path.exists(chunk_file):
                    os.remove(chunk_file)
        else:
            # Original behavior for shorter text
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.text_to_audio_chunk(text, SAVE_VOICEOVER_TO))
            loop.close()
        
        print(f"✅ Audio file saved at {SAVE_VOICEOVER_TO}")
    
    def combine_audio_chunks(self, chunk_files, output_path):
        """Combine multiple audio chunks into a single file using ffmpeg."""
        print("🎬 Combining audio chunks...")
        
        # Create a temporary file listing all the chunks
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as list_file:
            for chunk_file in chunk_files:
                list_file.write(f"file '{os.path.abspath(chunk_file)}'\n")
            list_filename = list_file.name
        
        # Use ffmpeg to concatenate the audio files
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_filename,
            '-c', 'copy', output_path, '-y'
        ]
        
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Clean up the temporary list file
        os.remove(list_filename)
        print(f"✅ Combined {len(chunk_files)} chunks into final audio")


if __name__ == "__main__":
    generator = VoiceOverGenerator()
    text = input("Enter text for voiceover: ")
    generator.generate_voiceover(text)
