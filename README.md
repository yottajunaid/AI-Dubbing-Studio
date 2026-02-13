# 🎬 AI Dubbing Studio

A complete, automated workflow manager for dubbing Asian dramas and video clips. This app allows you to write scripts, generate AI speech matched exactly to your video length, create SRT subtitles, and render the final video—all from a single web interface.

Powered by **Streamlit**, **Kokoro-TTS**, **OpenAI Whisper**, and **FFmpeg**.

---

## ⚠️ CRITICAL: Memory Management
This application runs heavy AI models locally (Kokoro TTS and Whisper). **To prevent crashes and "Out of Memory" errors:**
* Close all unnecessary browser tabs.
* Close heavy background applications (games, video editors, etc.).
* The app is designed to clear memory between tasks, but starting with free RAM is highly recommended.
* Screen may go blank if device runs out of memory, it will generate just let the AI do his work.

---

## ✨ Features
* **Built-in Video Player:** Watch and pause your video while writing the script.
* **Smart Speech Generation:** Calculates the exact speed required for your TTS audio to perfectly match your target video length.
* **Auto-Subtitles:** Uses Whisper to generate highly accurate `.srt` files with timestamps.
* **Zero-RAM Rendering:** Uses FFmpeg to securely burn subtitles and merge audio without crashing your system.

---

## ⚙️ Installation

### Prerequisites (All Operating Systems)
1. Install [Python 3.9 - 3.11](https://www.python.org/downloads/) (Make sure to check "Add Python to PATH" during installation).
2. Clone or download this repository.

### 🪟 Windows (Highly Recommended / Optimized)
Windows is the most optimized platform for this tool. The setup script will automatically download the correct FFmpeg build for you.
1. Open Command Prompt or PowerShell in the project folder.
2. Run the setup script:
    `python setup.py`
3. Follow the prompt to configure your video directory.
4. Run: `streamlit run app.py`

### 🍎 macOS
1. Ensure you have [Homebrew](https://brew.sh/) installed.
2. Open Terminal in the project folder.
3. Run the setup script (it will automatically use Homebrew to install FFmpeg):
    `python3 setup.py`
4. Follow the prompt to configure your video directory.
5. Run: `streamlit run app.py`

### 🐧 Linux
1. Open Terminal in the project folder.
2. Run the setup script (it will automatically use `apt` to install FFmpeg):
    `python3 setup.py`
3. Follow the prompt to configure your video directory.
4. Run: `streamlit run app.py`

---

## 🚀 How to Use

1. Start the web application:
    `streamlit run app.py`
2. **Select Video:** Enter the number of the video you want to dub (e.g., `1` for `1.mp4`).
3. **Write Script:** Type your translated script in the Note Maker. Enter your exact target video length.
4. **Confirm Script:** Click the button to calculate math and update the TTS engine.
5. **Generate Speech:** Runs Kokoro-TTS to generate the audio file.
6. **Generate SRT:** Runs Whisper to transcribe the newly generated audio into subtitles.
7. **Render:** Merges the original video, the new audio, and the styled subtitles into a final export.

---

## 📁 Directory Structure
Once configured, the app expects and utilizes this folder structure:

    /your-chosen-folder/
    │── 1.mp4
    │── 2.mp4
    ├── /captions/    (Stores your .txt scripts)
    ├── /audio/       (Stores the generated Kokoro .wav files)
    ├── /subtitles/   (Stores the generated Whisper .srt files)
    └── /exports/     (Stores the final rendered mp4 videos)
