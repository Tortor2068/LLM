#!/usr/bin/env python3
"""
Audio Transcription Script
Converts audio files to text using faster-whisper and processes phonetic alphabet
"""

import locale
import subprocess
import sys
import os
import copy
import re
from datetime import timedelta

file_name = 'KHAF2-Jun-22-2025-1930Z.mp3'  # Change this to your audio file
whisper_type = "large-v3"  # Options: tiny, base, small, medium, large-v1, large-v2

# Set UTF-8 encoding
locale.getpreferredencoding = lambda: "UTF-8"

def install_dependencies():
    """Install required packages using pip"""
    packages = [
        "faster-whisper",
        "srt", 
        "requests", 
        "tqdm", 
        "googletrans==4.0.0rc1", 
        "httpx", 
        "aiometer"
    ]
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Successfully installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package}: {e}")

def check_cuda():
    """Check CUDA availability"""
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        if result.returncode == 0:
            print("CUDA is available:")
            print(result.stdout)
            return True
        else:
            print("CUDA not available or nvidia-smi not found")
            return False
    except FileNotFoundError:
        print("nvidia-smi not found. CUDA may not be available.")
        return False

def setup_model():
    """Initialize the faster-whisper model"""
    try:
        from faster_whisper import WhisperModel
        
        # Model configuration
        model_size = whisper_type
        device = "cuda" if check_cuda() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        
        print(f"Loading model: {model_size} on {device}")
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        return model
    except ImportError:
        print("faster-whisper not installed. Please run install_dependencies() first.")
        return None

def transcribe_audio(model, filename, **kwargs):
    """Transcribe audio file using the model"""
    if model is None:
        print("Model not initialized")
        return None, None
    
    # Default transcription parameters
    default_params = {
        'beam_size': 5,
        'word_timestamps': True,
        'vad_filter': True,
        'vad_parameters': {
            'threshold': 0.6,
            'min_speech_duration_ms': 250,
            'max_speech_duration_s': float('inf'),
            'min_silence_duration_ms': 100,
            'speech_pad_ms': 400
        }
    }
    
    # Update with provided parameters
    default_params.update(kwargs)
    
    try:
        segments, info = model.transcribe(filename, **default_params)
        print(f"Detected language '{info.language}' with probability {info.language_probability}")
        segments = [i for i in segments]  # force run generator
        return segments, info
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None, None

def sentence_segments_merger(segments, max_text_len=80, max_segment_interval=2.0):
    """Merge word segments into sentence segments"""
    if not segments:
        return []

    merged_segments = []
    current_segment = {"text": "", "start": 0, "end": 0}
    current_segment_template = {"text": "", "start": 0, "end": 0}
    is_current_segment_empty = True

    for i, segment in enumerate(segments):
        # remove empty lines
        segment_text = segment["text"].strip()
        if not segment_text:
            continue

        if is_current_segment_empty:
            current_segment["start"] = segment["start"]
            current_segment["end"] = segment["end"]
            current_segment["text"] = segment["text"].strip()
            is_current_segment_empty = False
            continue

        if segment["start"] - current_segment["end"] < max_segment_interval and \
                len(current_segment["text"] + " " + segment_text) < max_text_len:
            current_segment["text"] += " " + segment_text
            current_segment["text"] = current_segment["text"].strip()
            current_segment["end"] = segment["end"]
        else:
            current_segment["text"] = current_segment["text"].strip()
            merged_segments.append(copy.deepcopy(current_segment))
            current_segment = copy.deepcopy(current_segment_template)
            current_segment["start"] = segment["start"]
            current_segment["end"] = segment["end"]
            current_segment["text"] = segment["text"].strip()
            is_current_segment_empty = False

    # Add the last segment if it's not empty
    if not is_current_segment_empty:
        current_segment["text"] = current_segment["text"].strip()
        merged_segments.append(current_segment)

    return merged_segments

def translate_phonetic_alphabet(text):
    """Translate NATO phonetic alphabet to letters"""
    # Create a dictionary for NATO phonetic alphabet translation
    phonetic_to_letter = {
        "alpha": "A", "bravo": "B", "charlie": "C", "delta": "D",
        "echo": "E", "foxtrot": "F", "golf": "G", "hotel": "H",
        "india": "I", "juliet": "J", "kilo": "K", "lima": "L",
        "mike": "M", "november": "N", "oscar": "O", "papa": "P",
        "quebec": "Q", "romeo": "R", "sierra": "S", "tango": "T",
        "uniform": "U", "victor": "V", "whiskey": "W", "xray": "X",
        "yankee": "Y", "zulu": "Z"
    }

    # Create a regex pattern to match phonetic words (case-insensitive)
    pattern = r'\b(?:' + '|'.join(re.escape(word) for word in phonetic_to_letter.keys()) + r')\b'

    # Use re.sub with a function to replace matched words
    def replace_match_and_bold(match):
        matched_word = match.group(0).lower()
        letter = phonetic_to_letter[matched_word]

        # Check if the matched word is "november" and the letter is "N"
        if matched_word == "november" and letter == "N":
            # Return the bolded character
            return f"\033[1m{letter}\033[0m"
        else:
            # Return the unbolded character
            return letter

    # Call re.sub here, outside of replace_match_and_bold
    translated_text = re.sub(pattern, replace_match_and_bold, text, flags=re.IGNORECASE)

    # Return the translated text
    return translated_text

def main():
    """Main function to run the transcription pipeline"""
    print("Audio Transcription Script")
    print("=" * 50)
    
    # Install dependencies
    print("Installing dependencies...")
    install_dependencies()
    
    # Setup model
    print("\nSetting up model...")
    model = setup_model()
    if model is None:
        return
    
    # File configuration

    
    directory_path = "."  # Current directory
    filename = os.path.join(directory_path, file_name)
    transcribed_srt_name = 'Transcribed.srt'
    
    # Check if file exists
    if not os.path.exists(filename):
        print(f"Audio file not found: {filename}")
        print("Please update the file_name variable with your audio file path")
        return
    
    # Transcription parameters
    max_text_len = 80
    max_segment_interval = 2.0
    
    print(f"\nTranscribing: {filename}")
    segments, info = transcribe_audio(model, filename)
    
    if segments is None:
        print("Transcription failed")
        return
    
    print(f"Transcription completed. Found {len(segments)} segments.")
    
    # Process segments
    print("\nProcessing segments...")
    segments_lst = []
    for i in segments:
        if hasattr(i, 'words') and i.words is not None:
            for j in i.words:
                if j.word.strip():  # not empty string
                    segments_lst.append({"text": j.word.strip(), "start": j.start, "end": j.end})

    result_merged = sentence_segments_merger(segments_lst,
                                           max_text_len=max_text_len,
                                           max_segment_interval=max_segment_interval)

    # Generate SRT
    print("Generating SRT file...")
    try:
        import srt
        
        result_srt_list = []
        for i, v in enumerate(result_merged):
            result_srt_list.append(srt.Subtitle(index=i,
                                              start=timedelta(seconds=v['start']),
                                              end=timedelta(seconds=v['end']),
                                              content=v['text'].strip()))

        composed_transcription = srt.compose(result_srt_list)

        # Save SRT file
        with open(transcribed_srt_name, 'w', encoding='utf-8') as f:
            f.write(composed_transcription)
        print(f"SRT file saved: {transcribed_srt_name}")

        # Process phonetic alphabet
        print("Processing phonetic alphabet...")
        translated_text = translate_phonetic_alphabet(composed_transcription)

        # Save translated text
        output_filename = "Transcribed.txt"
        output_filepath = os.path.join(directory_path, output_filename)

        try:
            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write(translated_text)
            print(f"Successfully saved the translated text to: {output_filepath}")
        except Exception as e:
            print(f"An error occurred while saving the file: {e}")
            
    except ImportError:
        print("srt module not available. Please install it with: pip install srt")
    except Exception as e:
        print(f"Error processing transcription: {e}")

if __name__ == "__main__":
    main()
