import soundfile as sf
import numpy as np
from kokoro import KPipeline
import sys

TARGET_DURATION = 31.0
OUTPUT_FILENAME = "D:/streamlit-test/videos/audio/1.wav"
TEXT_CONTENT = """This boy wants to impress his girl
He fears but his friends forced him
His friends pushed him forward
He refuses to do so
The boys were so naughty that they pushed him over again
He strikes to the girl
Oh no
He gives the flower to her
Will she accept the flowers?
Yes
She gives a kiss to him.
His friends started celebrating
The girls is happy and started walking away
Oh no, the boy went paralyzed by the kiss
His friends handle him
Kissing him was the biggest mistake
Now he cannot walk anymore"""
PAUSE_DURATION = 0.2

try:
    print("Initializing Pipeline...")
    pipeline = KPipeline(lang_code='a')

    def generate_with_metrics(text, speed_factor):
        generator = pipeline(text, voice='af_heart', speed=speed_factor, split_pattern=r'\n+')
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
    
    print(f"Pass 2: Adjusting speed to {required_speed:.2f}x...")
    final_audio, _ = generate_with_metrics(TEXT_CONTENT, required_speed)

    # 2. Exact Millisecond Array Matching
    target_samples = int(TARGET_DURATION * 24000)
    current_samples = len(final_audio)
    
    if current_samples < target_samples:
        final_audio = np.pad(final_audio, (0, target_samples - current_samples)) # Pad silence
    elif current_samples > target_samples:
        final_audio = final_audio[:target_samples] # Trim excess
        
    sf.write(OUTPUT_FILENAME, final_audio, 24000)
    print(f"Success! Perfect Duration: {len(final_audio)/24000:.2f}s")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    sys.exit(1)
