import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.dont_write_bytecode = True
import importlib
from config import BGM_MODEL


def load_bgm_model():
    module_name = f"Models.BGM.Models.{BGM_MODEL}"
    try:
        module = importlib.import_module(module_name)
        print(f"🎵 Loading BGM Model: {BGM_MODEL}")
        return module.BGMGenerator()
    except ImportError:
        raise ImportError(f"❌ Error: {BGM_MODEL}.py not found in Models/BGM/Models")


if __name__ == "__main__":
    generator = load_bgm_model()
    video_path = input("Enter video path: ")
    bgm_path = input("Enter BGM path: ")
    generator.add_background_music(video_path, bgm_path)