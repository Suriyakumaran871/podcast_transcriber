import streamlit as st
import os
import requests
import time
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

# API URLs
UPLOAD_URL = "https://api.assemblyai.com/v2/upload"
TRANSCRIPT_URL = "https://api.assemblyai.com/v2/transcript"

headers = {
    "authorization": ASSEMBLYAI_API_KEY,
    "content-type": "application/json"
}

st.set_page_config(page_title="AssemblyAI Podcast Transcriber", layout="centered")
st.title("🎙️ Podcast Transcriber (AssemblyAI)")

if not ASSEMBLYAI_API_KEY:
    st.error("❌ AssemblyAI API key not found in `.env`")
    st.stop()

uploaded_file = st.file_uploader("Upload podcast file (.mp3/.wav/.flac)", type=["mp3", "wav", "flac"])

def upload_to_assemblyai(file_path):
    with open(file_path, 'rb') as f:
        response = requests.post(UPLOAD_URL, headers={"authorization": ASSEMBLYAI_API_KEY}, files={"file": f})
    response.raise_for_status()
    return response.json()["upload_url"]

def request_transcription(audio_url):
    json_data = {
        "audio_url": audio_url,
        "language_code": "en_us",
        "auto_chapters": False
    }
    response = requests.post(TRANSCRIPT_URL, json=json_data, headers=headers)
    response.raise_for_status()
    return response.json()["id"]

def poll_transcription(transcript_id):
    polling_endpoint = f"{TRANSCRIPT_URL}/{transcript_id}"
    while True:
        response = requests.get(polling_endpoint, headers=headers)
        data = response.json()
        if data["status"] == "completed":
            return data["text"]
        elif data["status"] == "error":
            raise RuntimeError(data["error"])
        time.sleep(3)

if uploaded_file:
    st.audio(uploaded_file)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(uploaded_file.read())
        file_path = tmp.name

    st.info("🔁 Uploading to AssemblyAI")
    try:
        audio_url = upload_to_assemblyai(file_path)
        st.success("✅ File uploaded.")

        st.info("🧠 Transcribing...")
        transcript_id = request_transcription(audio_url)
        transcript_text = poll_transcription(transcript_id)

        st.subheader("📝 Transcript")
        st.text_area("Transcription", transcript_text, height=300)
        st.download_button("📥 Download Transcript", transcript_text, file_name="transcript.txt")

    except Exception as e:
        st.error(f"❌ Transcription failed: {e}")
