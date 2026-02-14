import streamlit as st
import os
import subprocess
import soundfile as sf
import shutil
from datetime import timedelta
import time
import sys
import json

# --- CONFIGURATION ---
# Load dynamic path
try:
    with open("config.json", "r") as f:
        BASE_DIR = json.load(f)["base_dir"]
except FileNotFoundError:
    st.error("Please run setup.py first!")
    st.stop()

VIDEO_DIR = BASE_DIR
CAPTIONS_DIR = os.path.join(BASE_DIR, "captions")
SUBTITLES_DIR = os.path.join(BASE_DIR, "subtitles")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")
AUDIO_DIR = os.path.join(BASE_DIR, "audio") # Replaces 'chinese' folder
LOG_FILE = "process_log.txt"

for d in [CAPTIONS_DIR, SUBTITLES_DIR, EXPORT_DIR, AUDIO_DIR]:
    os.makedirs(d, exist_ok=True)

# Path to your Kokoro installation (runs from the current project folder)
KOKORO_WORK_DIR = os.path.dirname(os.path.abspath(__file__))
KOKORO_SCRIPT_PATH = os.path.join(KOKORO_WORK_DIR, "run.py")

st.set_page_config(layout="wide", page_title="Dubbing Studio")

# --- UTILITY FUNCTIONS ---

def format_timestamp(seconds):
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def generate_srt(audio_path, output_path):
    import whisper
    import gc
    import torch
    
    model = whisper.load_model("base") 
    result = model.transcribe(audio_path)
    
    with open(output_path, "w", encoding="utf-8") as srt_file:
        for i, segment in enumerate(result["segments"]):
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])
            text = segment["text"].strip().replace(".", "")
            srt_file.write(f"{i + 1}\n{start} --> {end}\n{text}\n\n")
            
    del model
    del result
    gc.collect() 
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

# --- UI LAYOUT ---

st.title("🎬 AI Dubbing Workflow Manager")

col_sel, col_stat = st.columns([1, 3])
with col_sel:
    video_id = st.number_input("Select Video Number", min_value=1, value=3, step=1)

video_filename = f"{video_id}.mp4"
script_filename = f"{video_id}.txt"
audio_filename = f"{video_id}.wav"
srt_filename = f"{video_id}.srt"

video_path = os.path.join(VIDEO_DIR, video_filename)
script_path = os.path.join(CAPTIONS_DIR, script_filename)

# Ensure audio saves as an absolute path into your project folder
full_audio_path = os.path.join(AUDIO_DIR, audio_filename)
audio_output_path_local = full_audio_path.replace("\\", "/") 
final_srt_path = os.path.join(SUBTITLES_DIR, srt_filename)

col1, col2, col3, col4 = st.columns(4)

# --- BLOCK 1: VIDEO PLAYER ---
with col1:
    st.header("1. Video Player")
    if os.path.exists(video_path):
        st.video(video_path)
        st.caption(f"Playing: {video_filename}")
    else:
        st.error(f"Not Found: {video_path}")

# --- BLOCK 2: NOTE MAKER ---
with col2:
    st.header("2. Script Editor")
    
    initial_text = ""
    if os.path.exists(script_path):
        with open(script_path, "r", encoding="utf-8") as f:
            initial_text = f.read()

    script_content = st.text_area("Script", value=initial_text, height=300)
    target_duration = st.number_input("Target Video Length (s)", min_value=1.0, value=46.0, step=0.5)

    if st.button("Confirm Script & Update Code"):
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        
        new_run_py = f'''import soundfile as sf
import numpy as np
from kokoro import KPipeline
import sys

TARGET_DURATION = {target_duration}
OUTPUT_FILENAME = "{audio_output_path_local}"
TEXT_CONTENT = """{script_content}"""
PAUSE_DURATION = 0.2

try:
    print("Initializing Pipeline...")
    pipeline = KPipeline(lang_code='a')

    def generate_with_metrics(text, speed_factor):
        generator = pipeline(text, voice='af_heart', speed=speed_factor, split_pattern=r'\\n+')
        pieces = []
        segment_count = 0
        for _, _, audio in generator:
            pieces.append(audio)
            pieces.append(np.zeros(int(24000 * PAUSE_DURATION)))
            segment_count += 1
        return np.concatenate(pieces) if pieces else np.array([]), segment_count

    # --- PASS 1: MEASUREMENT ---
    raw_audio, seg_count = generate_with_metrics(TEXT_CONTENT, 1.0)
    total_pause_time = seg_count * PAUSE_DURATION
    speech_len_p1 = (len(raw_audio) / 24000) - total_pause_time

    if speech_len_p1 <= 0: sys.exit(1)

    # --- MATH CALCULATION ---
    target_speech_time = max(TARGET_DURATION - total_pause_time, 1.0)
    
    # 1. Non-linear correction formula
    raw_speed = speech_len_p1 / target_speech_time
    required_speed = raw_speed ** 0.90 
    
    print(f"Pass 2: Adjusting speed to {{required_speed:.2f}}x...")
    final_audio, _ = generate_with_metrics(TEXT_CONTENT, required_speed)

    # 2. Exact Millisecond Array Matching
    target_samples = int(TARGET_DURATION * 24000)
    current_samples = len(final_audio)
    
    if current_samples < target_samples:
        final_audio = np.pad(final_audio, (0, target_samples - current_samples)) # Pad silence
    elif current_samples > target_samples:
        final_audio = final_audio[:target_samples] # Trim excess
        
    sf.write(OUTPUT_FILENAME, final_audio, 24000)
    print(f"Success! Perfect Duration: {{len(final_audio)/24000:.2f}}s")

except Exception as e:
    print(f"CRITICAL ERROR: {{e}}")
    sys.exit(1)
'''
        with open(KOKORO_SCRIPT_PATH, "w", encoding="utf-8") as f:
            f.write(new_run_py)
        st.success("Script Updated with Millisecond Precision!")

# --- BLOCK 3: GENERATE SPEECH (FIXED) ---
with col3:
    st.header("3. Generate Speech")
    st.info(f"Output: {audio_filename}")
    
    if st.button("▶ Start Generation"):
        status_box = st.empty()
        status_box.warning("Initializing AI... (Logs writing to process_log.txt)")
        
        # OPEN A LOG FILE 
        with open(LOG_FILE, "w") as log_f:
            try:
                # We use Popen to run it without blocking the UI thread instantly
                # We pass 'creationflags' to prevent a black window popping up (Optional, but looks nicer)
                process = subprocess.Popen(
                    ["python", "run.py"], 
                    cwd=KOKORO_WORK_DIR, 
                    stdout=log_f, 
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                # Poll for completion
                while process.poll() is None:
                    time.sleep(1)
                    status_box.info("Generating... (AI Model is running, takes 2-3 minutes to generate. Make sure to close all other tabs and apps to save RAM)")
                
                if process.returncode == 0:
                    status_box.success("Generation Complete!")
                    # Add a unique key to reload audio player
                    st.audio(full_audio_path)
                else:
                    status_box.error("Error occurred. Check Logs checkbox below.")
                    
            except Exception as e:
                status_box.error(f"Failed to launch: {e}")

    # View Log Button (Safe way to see errors)
    if st.checkbox("Show Logs"):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                st.code(f.read())

# --- BLOCK 4: SUBTITLES ---
with col4:
    st.header("4. Subtitles")
    if st.button("Generate SRT"):
        if not os.path.exists(full_audio_path):
            st.error("Audio not found!")
        else:
            with st.spinner("Transcribing... (Loading Whisper Model)"):
                try:
                    generate_srt(full_audio_path, final_srt_path)
                    st.success(f"Created {srt_filename}")
                    with open(final_srt_path) as f:
                        st.download_button("Download SRT", f.read(), srt_filename)
                except Exception as e:
                     st.error(f"Subtitle Error: {e}")

# --- BLOCK 5: FINAL RENDER ---
st.markdown("---")
st.header("5. Final Render (Merge Video + Audio + Subs)")

# Define BGM Directory
BGM_DIR = os.path.join(BASE_DIR, "bgm")
os.makedirs(BGM_DIR, exist_ok=True)
bgm_file = os.path.join(BGM_DIR, "pop_chinese_song.mp3")

final_video_path = os.path.join(EXPORT_DIR, f"final_{video_filename}")

# UI for BGM
col_render, col_bgm = st.columns([1, 1])
with col_render:
    render_btn = st.button("🎬 Render Final Video")
with col_bgm:
    use_bgm = st.checkbox("Add Background Music (25% Volume)", value=True)

if render_btn:
    if not os.path.exists(full_audio_path) or not os.path.exists(final_srt_path):
        st.error("Missing Audio or SRT file! Generate them first.")
    else:
        with st.spinner("Rendering final video using FFmpeg..."):
            try:
                import shutil
                temp_srt = "temp_subs.srt"
                shutil.copy(final_srt_path, temp_srt)
                
                # Style Settings
                style = "Fontname=Arial,Bold=1,Fontsize=14,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=1,Shadow=0,Alignment=2,MarginV=120"
                ffmpeg_cmd = r".\ffmpeg.exe" if os.path.exists("ffmpeg.exe") else "ffmpeg"
                
                # Base Command
                cmd = [ffmpeg_cmd, "-y", "-i", video_path, "-i", full_audio_path]
                
                # COMPLEX FILTER LOGIC
                if use_bgm and os.path.exists(bgm_file):
                    cmd.extend(["-i", bgm_file]) # Input 2: BGM
                    
                    # Filter Complex:
                    # [2:a]volume=0.25[bgm]; -> Take input 2 (bgm), lower volume, call it [bgm]
                    # [1:a][bgm]amix=inputs=2:duration=first[mix] -> Mix speech (1:a) and [bgm], stop at length of speech
                    filter_complex = "[2:a]volume=0.25[bgm];[1:a][bgm]amix=inputs=2:duration=first[a_out]"
                    
                    cmd.extend([
                        "-filter_complex", filter_complex,
                        "-map", "0:v:0",   # Map Video from Input 0
                        "-map", "[a_out]", # Map Mixed Audio
                    ])
                else:
                    if use_bgm and not os.path.exists(bgm_file):
                        st.warning(f"BGM file not found at: {bgm_file}. Rendering without music.")
                    
                    # No BGM, just map speech directly
                    cmd.extend([
                        "-map", "0:v:0",
                        "-map", "1:a:0"
                    ])

                # Common ending arguments
                cmd.extend([
                    "-c:v", "libx264", 
                    "-c:a", "aac", 
                    "-b:a", "192k", 
                    "-vf", f"subtitles={temp_srt}:force_style='{style}'", 
                    "-shortest", # Cuts BGM to match video length
                    final_video_path
                ])
                
                process = subprocess.run(cmd, capture_output=True, text=True)
                
                if os.path.exists(temp_srt):
                    os.remove(temp_srt)
                    
                if process.returncode == 0:
                    st.success(f"Final video saved as: final_{video_filename}")
                    preview_col, empty_col = st.columns([1, 3])
                    with preview_col:
                        st.video(final_video_path) 
                else:
                    st.error("FFmpeg rendering failed!")
                    with st.expander("Show FFmpeg Error"):
                        st.code(process.stderr)
                        
            except Exception as e:
                st.error(f"Render Error: {e}")

