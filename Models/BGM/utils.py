import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


def ensure_bgm_directory(filepath):
    """Ensures the directory for a BGM file exists before saving.
    
    Args:
        filepath (str): The full path where the file will be saved
        
    Returns:
        None
    """
    directory = os.path.dirname(filepath)
    if directory:
        os.makedirs(directory, exist_ok=True)


def get_available_bgm_files(bgm_directory="Data/BGM"):
    """Gets a list of available background music files.
    
    Args:
        bgm_directory (str): Directory to look for BGM files
        
    Returns:
        list: List of available BGM file paths
    """
    bgm_files = []
    if os.path.exists(bgm_directory):
        for file in os.listdir(bgm_directory):
            if file.lower().endswith(('.mp3', '.wav', '.m4a', '.flac')):
                bgm_files.append(os.path.join(bgm_directory, file))
    return bgm_files