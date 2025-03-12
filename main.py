import sys
import asyncio

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import streamlit as st
import os
import time
import re
import tempfile

# Local imports
from app.config import TimeRange
from app.audio_processor import (
    create_temp_file,
    trim_audio,
    download_youtube_audio
)
from app.diarizer import run_diarization
from app.transcriber import WhisperTranscriber
from app.llm_services import answer_with_llm

# ------------------ Utility Functions ------------------

def seconds_to_hms(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds - (hours * 3600 + minutes * 60)
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

def hms_to_seconds(hms: str) -> float:
    if '.' in hms:
        time_part, ms_part = hms.split('.')
        ms = float(f"0.{ms_part}")
    else:
        time_part = hms
        ms = 0.0

    parts = time_part.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + int(s) + ms
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + int(s) + ms
    else:
        return int(parts[0]) + ms

def validate_time_format(time_str: str) -> bool:
    pattern = r'^([0-9]{1,2}:)?[0-5]?[0-9]:[0-5][0-9](\.[0-9]{1,3})?$'
    return re.match(pattern, time_str) is not None

def display_header():
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(
            "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f399.png",
            width=80
        )
    with col2:
        st.title("Audio Transcription & Speaker Diarization")
        st.markdown(
            "Process audio files or YouTube videos to get transcriptions with speaker identification."
        )

def get_whisper_models():
    return ["tiny", "base", "small", "medium", "large"]

def display_transcription(transcriptions):
    """Display final transcription results in a styled container."""
    if not transcriptions:
        st.warning("No transcription results available.")
        return

    st.subheader("Transcription Results")
    with st.container():
        st.markdown('<div class="output-container">', unsafe_allow_html=True)

        speakers = list(set(t["speaker"] for t in transcriptions))
        # colors = ["#FF9AA2", "#FFB7B2", "#FFDAC1", "#E2F0CB", "#B5EAD7", "#C7CEEA"]
        colors = ["#FF6B6B", "#4ECDC4", "#FFE66D", "#6A0572", "#2E86AB", "#FFB400"]

        speaker_colors = {speakers[i]: colors[i % len(colors)] for i in range(len(speakers))}

        for seg in transcriptions:
            spk = seg["speaker"]
            txt = seg["text"]
            start = seg["start"]
            end = seg["end"]
            timestamp = f"{start:.2f}s - {end:.2f}s"

            speaker_label = (
                f'<span class="speaker-label" '
                f'style="background-color: {speaker_colors[spk]};">{spk}</span>'
            )
            st.markdown(
                f'{speaker_label} <small>({timestamp})</small> {txt}',
                unsafe_allow_html=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

def combine_transcriptions(transcriptions):
    """Combine all speaker segments into a single text for LLM context."""
    combined = []
    for seg in transcriptions:
        spk = seg["speaker"]
        txt = seg["text"]
        combined.append(f"{spk}: {txt}")
    return "\n".join(combined)

# ------------------ Processing Logic ------------------

def process_audio(file_path: str, start_time: str, end_time: str, whisper_model="base"):
    """
    1. Trim the audio to the given time range.
    2. Diarize.
    3. Transcribe each diarized segment.
    Returns a list of dicts: [{speaker, text, start, end}, ...]
    """
    temp_dir = tempfile.mkdtemp()
    trimmed_path = os.path.join(temp_dir, "trimmed_audio.wav")

    # 1) Trim to user’s requested time range
    trimmed_file = trim_audio(file_path, start_time, end_time, trimmed_path)
    if not trimmed_file:
        return []

    # 2) Diarize
    diarization_segments = run_diarization(trimmed_file)

    # 3) Transcribe
    transcriber = WhisperTranscriber(model_name=whisper_model)
    transcriptions = []
    for i, segment in enumerate(diarization_segments):
        seg_start = seconds_to_hms(segment["start"])
        seg_end = seconds_to_hms(segment["end"])

        segment_path = os.path.join(temp_dir, f"segment_{i}.wav")
        segment_file = trim_audio(trimmed_file, seg_start, seg_end, segment_path)
        if segment_file:
            text = transcriber.transcribe(segment_file)
            transcriptions.append({
                "speaker": segment["speaker"],
                "text": text,
                "start": segment["start"],
                "end": segment["end"]
            })
            os.remove(segment_file)
    os.remove(trimmed_file)

    return transcriptions


def transcribe_audio_source(
    audio_source: str,
    is_youtube: bool,
    start_time: str,
    end_time: str,
    whisper_model: str
) -> None:
    """
    Unified function that handles either:
     - local audio (audio_source is a file path)
     - youtube (audio_source is a youtube url)

    1) Download or copy the audio to a local temp path (if youtube).
    2) process_audio(...) to get transcriptions.
    3) Store results in st.session_state (transcriptions, transcript_text).
    """
    temp_dir = tempfile.mkdtemp()
    if is_youtube:
        # Download from YouTube
        output_file = os.path.join(temp_dir, "youtube_audio.wav")
        audio_file = download_youtube_audio(audio_source, output_file)
        if not audio_file:
            st.error("Failed to download audio from YouTube.")
            return
        final_path = audio_file
    else:
        # local audio
        # audio_source is already a local path
        final_path = audio_source

    # Process
    transcriptions = process_audio(final_path, start_time, end_time, whisper_model)
    if not transcriptions:
        st.error("No transcriptions generated.")
        return

    # Save to session state so we can re-display / re-run LLM on them
    st.session_state["transcriptions"] = transcriptions
    st.session_state["transcript_text"] = combine_transcriptions(transcriptions)
    st.session_state["llm_response"] = ""  # clear old LLM response

    print(f"Transcriptions: {st.session_state['transcript_text']}")

# ------------------ Main UI (Streamlit) ------------------

def main():
    st.set_page_config(page_title="Audio Transcription & Diarization", layout="wide")

    st.markdown(
        """
        <style>
            .main { padding: 2rem; max-width: 1200px; }
            .stTabs [data-baseweb="tab-list"] { gap: 8px; }
            .stTabs [data-baseweb="tab"] {
                height: 50px;
                white-space: pre-wrap;
                background-color: #f0f2f6;
                border-radius: 5px 5px 0 0;
                padding: 8px 16px;
                font-weight: 600;
            }
            .stTabs [aria-selected="true"] {
                background-color: #4CAF50 !important;
                color: white !important;
            }
            .output-container {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 16px;
                background-color: #f9f9f9;
                margin-top: 20px;
            }
            .speaker-label {
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 4px;
                margin-right: 8px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    display_header()

    # Initialize session_state variables (only once).
    if "transcriptions" not in st.session_state:
        st.session_state["transcriptions"] = []
    if "transcript_text" not in st.session_state:
        st.session_state["transcript_text"] = ""
    if "llm_response" not in st.session_state:
        st.session_state["llm_response"] = ""

    # Sidebar config
    st.sidebar.header("Configuration")
    whisper_model = st.sidebar.selectbox(
        "Whisper Model",
        get_whisper_models(),
        index=1,
        key="whisper_model"
    )

    tab1, tab2 = st.tabs(["📁 Upload Audio", "🎥 YouTube URL"])

    # =========== LOCAL AUDIO TAB ===========
    with tab1:
        st.header("Upload Audio File")
        uploaded_file = st.file_uploader("Choose an audio file", type=["wav", "mp3", "m4a"], key="uploader")

        if uploaded_file:
            col1, col2 = st.columns(2)
            with col1:
                st.audio(uploaded_file, format="audio/wav")
            with col2:
                st.subheader("Time Range")
                start_time = st.text_input("Start Time (HH:MM:SS)", "00:00:00", key="audio_start")
                end_time_enabled = st.checkbox("Set End Time", value=True, key="audio_end_enable")
                end_time_default = "00:00:30" if end_time_enabled else ""
                end_time = st.text_input("End Time (HH:MM:SS)", end_time_default, key="audio_end")

            if st.button("Process Audio", key="process_audio"):
                if not validate_time_format(start_time):
                    st.error("Invalid start time format. Use HH:MM:SS or MM:SS.")
                    return
                if end_time_enabled and end_time and not validate_time_format(end_time):
                    st.error("Invalid end time format. Use HH:MM:SS or MM:SS.")
                    return

                # Save uploaded file to a temp path
                with st.spinner("Processing audio..."):
                    temp_path = create_temp_file(uploaded_file)
                    transcribe_audio_source(
                        audio_source=temp_path,
                        is_youtube=False,
                        start_time=start_time,
                        end_time=end_time if end_time_enabled else None,
                        whisper_model=whisper_model
                    )

    # =========== YOUTUBE TAB ===========
    with tab2:
        st.header("YouTube Video")
        youtube_url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
            key="youtube_url"
        )
        if youtube_url:
            st.subheader("Time Range")
            col1, col2 = st.columns(2)
            with col1:
                start_time = st.text_input("Start Time (HH:MM:SS)", "00:00:00", key="yt_start")
            with col2:
                end_time_enabled = st.checkbox("Set End Time", value=True, key="yt_end_enable")
                end_time_default = "00:05:00" if end_time_enabled else ""
                end_time = st.text_input("End Time (HH:MM:SS)", end_time_default, key="yt_end")

            if youtube_url.startswith("https://"):
                st.info("Note: The application will download the audio from this YouTube video.")
            if st.button("Process Video", key="process_video"):
                if not validate_time_format(start_time):
                    st.error("Invalid start time format. Use HH:MM:SS or MM:SS.")
                    return
                if end_time_enabled and end_time and not validate_time_format(end_time):
                    st.error("Invalid end time format. Use HH:MM:SS or MM:SS.")
                    return
                if not youtube_url.startswith("https://"):
                    st.error("Please enter a valid YouTube URL.")
                    return

                with st.spinner("Downloading and processing video..."):
                    transcribe_audio_source(
                        audio_source=youtube_url,
                        is_youtube=True,
                        start_time=start_time,
                        end_time=end_time if end_time_enabled else None,
                        whisper_model=whisper_model
                    )

    # ------------------ SHOW TRANSCRIPTIONS & LLM UI ------------------
    # If we have transcriptions stored, show them
    if st.session_state["transcriptions"]:
        display_transcription(st.session_state["transcriptions"])

        # Download button
        download_text = "\n\n".join([
            f"{t['speaker']} ({t['start']:.2f}s - {t['end']:.2f}s): {t['text']}"
            for t in st.session_state["transcriptions"]
        ])
        st.download_button(
            label="Download Transcription",
            data=download_text,
            file_name=f"transcription_{int(time.time())}.txt",
            mime="text/plain",
            key="download_button"
        )

        # LLM Analysis Section
        st.subheader("Analyze Transcript with LLM")
        predefined_options = [
            "Summarize the discussion",
            "Extract key insights",
            "Any critical next steps?"
        ]
        selected_option = st.selectbox("Pick a predefined question:", predefined_options, key="predefined_q")

        user_question = st.text_input("Or type a custom question:", key="user_q")

        if st.button("Run LLM Query", key="run_llm"):
            if user_question.strip():
                question_to_ask = user_question.strip()
            else:
                question_to_ask = selected_option

            with st.spinner("Thinking..."):
                llm_response = answer_with_llm(
                    context=st.session_state["transcript_text"],
                    question=question_to_ask,
                    model_name="ollama:phi4:14b-fp16",
                    temperature=0.75
                )
            # Store LLM answer so it persists
            st.session_state["llm_response"] = llm_response

        # If we have an LLM response, display it
        if st.session_state["llm_response"]:
            st.write("**AI Agent response:**")
            st.write(st.session_state["llm_response"])

if __name__ == "__main__":
    main()
