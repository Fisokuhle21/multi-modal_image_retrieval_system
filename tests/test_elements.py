import streamlit.testing.v1 as st_test

def test_chat_elements():
    app = st_test.AppTest.from_file("app.py")
    app.get("chat_input")
    app.get("audio_input")
    app.get("session_state")
    print("✅ the app elements test passed!")