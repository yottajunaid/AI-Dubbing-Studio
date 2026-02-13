import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil

print("--- AI Dubbing Studio Setup ---\n")

# 1. Install Python Packages
print("Installing Python dependencies...")
dependencies = ["streamlit", "openai-whisper", "soundfile", "numpy", "kokoro", "torch", "torchaudio"]
subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet"] + dependencies)

# 2. Auto-Install FFmpeg
print("\nChecking for FFmpeg...")
if sys.platform == "win32":
    if not os.path.exists("ffmpeg.exe"):
        print("Downloading FFmpeg for Windows...")
        url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        urllib.request.urlretrieve(url, "ffmpeg.zip")
        print("Extracting FFmpeg...")
        with zipfile.ZipFile("ffmpeg.zip", 'r') as z:
            for file in z.namelist():
                if file.endswith("ffmpeg.exe"):
                    with z.open(file) as zf, open("ffmpeg.exe", 'wb') as f:
                        shutil.copyfileobj(zf, f)
                    break
        os.remove("ffmpeg.zip")
        print("FFmpeg downloaded to project folder.")
    else:
        print("FFmpeg already exists.")
elif sys.platform == "darwin":
    print("Installing FFmpeg for macOS...")
    subprocess.run(["brew", "install", "ffmpeg"], check=False)
else:
    print("Installing FFmpeg for Linux...")
    subprocess.run(["sudo", "apt-get", "install", "-y", "ffmpeg"], check=False)

# 3. Setup Directories
print("\n--- Directory Setup ---")
base_dir = input(r"Enter the folder path containing your videos (e.g., D:\temp\downloads): ").strip()

captions_dir = os.path.join(base_dir, "captions")
subtitles_dir = os.path.join(base_dir, "subtitles")
exports_dir = os.path.join(base_dir, "exports")

for folder in [captions_dir, subtitles_dir, exports_dir]:
    os.makedirs(folder, exist_ok=True)

# 4. Rename Videos
print("\nRenaming videos sequentially...")
existing_mp4s = [f for f in os.listdir(base_dir) if f.lower().endswith(".mp4")]

highest_num = 0
for f in existing_mp4s:
    name = os.path.splitext(f)[0]
    if name.isdigit():
        highest_num = max(highest_num, int(name))

to_rename = [f for f in existing_mp4s if not os.path.splitext(f)[0].isdigit()]

current_index = highest_num + 1
for video in to_rename:
    old_path = os.path.join(base_dir, video)
    new_path = os.path.join(base_dir, f"{current_index}.mp4")
    os.rename(old_path, new_path)
    current_index += 1

# 5. Generate Text Files
print("Generating 100 blank script files...")
for i in range(1, 101):
    open(os.path.join(captions_dir, f"{i}.txt"), 'a').close()

import json
with open("config.json", "w") as f:
    json.dump({"base_dir": base_dir}, f)

print("\n✅ Setup Complete! You can now run: streamlit run app.py")