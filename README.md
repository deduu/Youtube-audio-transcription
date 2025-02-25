<div align="center">
  <img src="https://raw.githubusercontent.com/deduu/audio-transcription-processor/main/assets/logo.png" alt="Project Logo" width="150">
  <h1>YouTube Audio Extractor and Transcriber</h1>
  <p>Enable AI to control your browser 🤖</p>

  ![Stars](https://img.shields.io/github/stars/deduu/audio-transcription-processor?style=for-the-badge)
  ![Discord](https://img.shields.io/discord/1234567890?style=for-the-badge&label=Discord&color=5865F2)
  ![Documentation](https://img.shields.io/badge/Documentation-Complete-blue?style=for-the-badge)
  ![Cloud](https://img.shields.io/badge/Cloud-Ready-blue?style=for-the-badge)
</div>

---

# YouTube Audio Extractor and Transcriber using Whisper & PyAnnote

This project includes a Streamlit web app (and/or Python scripts) that enable you to:

- Specify YouTube URLs and time ranges for audio extraction
- Automatically download only the specified audio segments
- Perform speaker diarization using pyannote.audio
- Transcribe the segmented audio using OpenAI Whisper
- Export transcriptions to a text file

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Example](#example)
- [Output](#output)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)
- [How to Contribute](#how-to-contribute)
- [Citation](#citation)
- [License](#license)

## Prerequisites
- Python 3.10 or higher (as specified in your pyproject.toml)
- Poetry for package management
- FFmpeg installed and in your system PATH
- Hugging Face token if you plan to use PyAnnote's speaker-diarization pipeline

## Installation

Clone the repository:
```bash
git clone https://github.com/deduu/audio-transcription-processor
cd audio-transcription-processor
```

Install dependencies using Poetry:
```bash
poetry install
```
This reads your pyproject.toml (and poetry.lock if present) and installs all required packages in an isolated virtual environment.

Install FFmpeg (if not already):
- Windows: Download from the official FFmpeg site and add to your system PATH.
- macOS:
  ```bash
  brew install ffmpeg
  ```
- Linux:
  ```bash
  sudo apt-get update
  sudo apt-get install ffmpeg
  ```

Optional: Set your Hugging Face token if you want to run speaker diarization (pyannote.audio):
```bash
export HUGGINGFACE_TOKEN="hf_xxxYourTokenxxx"
```
If you do not set this, you may see errors when running diarization steps.

## Usage

### A. Running the Streamlit App

If you're using the modular Streamlit approach (e.g., streamlit_app.py plus audio_processor.py, diarizer.py, etc.):

1. Navigate to the repository folder.
2. Activate the Poetry virtual environment (optional, but recommended):
   ```bash
   poetry shell
   ```
3. Run the app via Streamlit:
   ```bash
   streamlit run streamlit_app.py
   ```
4. Open the URL in your browser (Streamlit will display the local URL, typically http://localhost:8501).

From the Streamlit UI:
- Upload a local audio file under "Upload Audio" or paste a YouTube link under "YouTube URL".
- Specify start time / end time to trim the audio.
- Press "Process" to download, trim, diarize, and transcribe.
- View speaker-labeled transcripts and optionally download them as text.

### B. Running a Python Script (CLI approach)

If your code includes a direct Python script (like main.py) that:
- Loops over multiple YouTube URLs or local files,
- Extracts time ranges,
- Diarizes and transcribes,
- And writes a list.txt for each processed segment,

You can run it like this:
```bash
poetry run python main.py
```

In the script, edit any configuration variables (e.g., URL list, time ranges, or the output paths) according to your needs.

## Example

### Sample Input

```
YouTube URL: https://www.youtube.com/watch?v=7ARBJQn6QkM
Time Range: 0 - 30 seconds
```

<div align="center">
  <a href="https://www.youtube.com/watch?v=7ARBJQn6QkM" target="_blank">
    <img src="https://img.youtube.com/vi/7ARBJQn6QkM/0.jpg" alt="Sample YouTube Video" width="480" height="360" border="10" />
  </a>
</div>

### Sample Output Transcription

```
SPEAKER_00 (0.03s - 3.61s): At some point you have to believe something, we've reinvented computing as we know it.

SPEAKER_02 (3.61s - 5.75s): What is the vision for what you see coming next?

SPEAKER_00 (5.85s - 8.97s): If we ask ourselves if it can do this, how far can it go?

SPEAKER_02 (8.97s - 13.46s): How do we get from the robots that we have now to the future world that you see?

SPEAKER_00 (13.46s - 20.89s): Clear everything that moves will be robotics someday and it will be soon. We invested tens of billions of dollars before it really happened.

SPEAKER_00 (21.02s - 25.36s): No, that's very good. You did some research. But the big breakthrough I would say.

SPEAKER_00 (26.37s - 27.40s): This one week.

SPEAKER_01 (28.23s - 29.48s): That's Jensen Wong.

SPEAKER_01 (31.33s - 34.96s): and whether you know it or not, his decisions are shaping your future.
```

## Output

### Extracted Audio Files
- Saved in a folder, typically named extracted_audio/ (you can customize it in your config or code).
- Filenames often include the specified ID (e.g., 1.wav, 2.wav, etc.).

### Transcriptions
- If you're using the Streamlit app, transcriptions appear in the UI and can be downloaded as .txt.
- If using a direct script approach, they may be compiled into something like transcriptions/list.txt, where each line has:
  ```
  extracted_audio/1.wav|This is the transcribed text from audio file 1
  extracted_audio/2.wav|This is the transcribed text from audio file 2
  ```

## Customization

### Choose Whisper Model Size
Whisper supports different model sizes:
- 'tiny'
- 'base'
- 'small'
- 'medium'
- 'large'

Open transcriber.py (or whichever script loads Whisper) and set:
```python
self.model = whisper.load_model("base")
```
Change "base" to the size you want. Larger models offer better accuracy but require more system memory/GPU resources.

### Adjust Output Directories
By default, modules like audio_processor.py might use:
```python
audio_output_dir = "extracted_audio"
transcription_output_dir = "transcriptions"
```

Change these as desired. Ensure the script creates them if they don't exist:
```python
os.makedirs(audio_output_dir, exist_ok=True)
os.makedirs(transcription_output_dir, exist_ok=True)
```

## Troubleshooting

### FFmpeg Not Found
- Confirm `ffmpeg -version` works in your terminal.
- Make sure your PATH environment variable includes the FFmpeg binary location.

### yt-dlp Errors
- Update to the latest version:
  ```bash
  poetry update yt-dlp
  ```
- Check your network connectivity, ensure you can access YouTube.

### PyAnnote / Whisper Errors
- Make sure your Hugging Face token is set for pyannote/speaker-diarization.
- Whisper can require substantial GPU/CPU memory depending on the model chosen.

### Permission Issues
- Run the script with sufficient privileges if writing to restricted folders.
- Check file system read/write permissions.

## How to Contribute

We welcome contributions to improve the YouTube Audio Extractor and Transcriber! Here's how you can contribute:

1. **Fork the Repository**
   - Create your own fork of the project

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Your Changes**
   - Implement your feature or bug fix
   - Add or update tests as necessary
   - Update documentation to reflect your changes

4. **Commit Your Changes**
   ```bash
   git commit -m "Add feature: your feature description"
   ```

5. **Push to Your Branch**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Submit a Pull Request**
   - Open a pull request from your feature branch to our main branch
   - Provide a clear description of the changes and reference any related issues

7. **Code Review**
   - Wait for the maintainers to review your pull request
   - Make any requested changes

### Contribution Guidelines

- Follow the existing code style and conventions
- Write clear, documented, and testable code
- Keep pull requests focused on a single feature or bug fix
- Test your changes thoroughly before submitting
- Update the README.md if necessary

## Citation

If you use this tool in your research or project, please cite it as:

```bibtex
@software{Youtube_audio_transcription_processor2025,
  author = {Dedu, Author},
  title = {YouTube Audio Extractor and Transcriber},
  url = {https://github.com/deduu/audio-transcription-processor},
  year = {2025},
  month = {February}
}
```

## License
This project is licensed under the Apache License 2.0. See the LICENSE file for details.

**Disclaimer**: This script/app is for educational and personal use. Please respect YouTube's Terms of Service and copyright laws when downloading and using content.