import streamlit as st
from audio_recorder_streamlit import audio_recorder
import whisper
import base64

def transcribe(model, audio_path):
    result = model.transcribe(audio_path)
    return result["text"]

def main():
    model = whisper.load_model("base")
    st.title("Find what you need")
    recorded_audio = audio_recorder()
    if recorded_audio:
        audio_file = "audio.mp3"
        with open(audio_file, "wb") as f:
            f.write(recorded_audio)
        
        transcribed_text = transcribe(model, audio_file)
        st.write("Transcribed text:", transcribed_text)

if __name__ == "__main__":
    main()

