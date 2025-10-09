#!/usr/bin/env python3
"""
Download TinyLlama model for DocuMind RAG pipeline
Run: python download_model.py
"""

import os
import requests
from pathlib import Path
import sys

def download_tinyllama():
    """Download TinyLlama model for local LLM generation"""

    # Create models directory
    models_dir = Path(__file__).parent / "models"
    models_dir.mkdir(exist_ok=True)

    model_path = models_dir / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

    if model_path.exists():
        print(f"Model already exists at: {model_path}")
        return str(model_path)

    # TinyLlama model URL (Q4_K_M quantization for good balance of size/speed)
    url = "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

    print("Downloading TinyLlama model (this may take a few minutes)...")
    print(f"URL: {url}")
    print(f"Saving to: {model_path}")

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(model_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(".1f", end='', flush=True)

        print("\nDownload completed!")
        print(f"Model saved to: {model_path}")
        print(f"Size: {model_path.stat().st_size / (1024*1024):.1f} MB")

        return str(model_path)

    except Exception as e:
        print(f"Download failed: {e}")
        print("You can manually download the model from:")
        print(url)
        print(f"And place it in: {models_dir}")
        return None

if __name__ == "__main__":
    model_path = download_tinyllama()
    if model_path:
        print(f"\n✅ Model ready for use: {model_path}")
        print("You can now run your RAG pipeline with LLM generation!")
    else:
        print("\n❌ Model download failed. Please download manually.")
        sys.exit(1)