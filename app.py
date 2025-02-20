import streamlit as st
from streamlit_option_menu import option_menu
import shared.functions as fns

def save_text_feedback(index) -> None:
    st.session_state.messages_text[index]["feedback"] = st.session_state[f"feedback_{index}"]

def save_voice_feedback(index) -> None:
    st.session_state.messages_voice[index]["feedback"] = st.session_state[f"feedback_{index}"]

def clear_text_chat_history() -> None:
    st.session_state.messages_text = []

def clear_voice_chat_history() -> None:
    st.session_state.messages_voice = []

def rerun() -> None:
    st.rerun()

def main() -> None:
    st.set_page_config(page_title="Multimodal Image Retrieval System")
    selected = option_menu(
        menu_title = None,
        options = ["Text Mode", "Voice Mode"],
        icons=['card-text', 'record-btn'],
        default_index=0,
        orientation="horizontal",
        styles={
            "nav-link": {
                "font-size": "15px"
            },
            "nav-link-selected": {"background-color": "purple", "padding-top": "-100px"}
        }
    )

    if selected == "Text Mode":
        st.title('Text Mode')

        msg = st.chat_message("assistant", avatar='icons/assistant.png')
        msg.write("Welcome to the Text Mode Chat, how may I assist you today?")

        # Store generated responses
        if "messages_text" not in st.session_state.keys():
            st.session_state.messages_text = []

        # Display or clear chat messages
        for i, message in enumerate(st.session_state.messages_text):
            with st.chat_message(message["role"], avatar='icons/text_user.png' if message["role"] == "user" else "icons/assistant.png"):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    feedback = message.get("feedback", None)
                    st.session_state[f"feedback_{i}"] = feedback
                    st.feedback(
                        "thumbs",
                        key=f"feedback_{i}",
                        disabled=feedback is not None,
                        on_change=save_text_feedback,
                        args=[i],
                    )
                    columns = st.columns(3, vertical_alignment="top")
                    for col, image, caption in zip(columns, message["content"], message["caption"]):
                        with col:
                            st.image(image)
                            st.write(caption)

        # User-provided prompt
        if prompt := st.chat_input("Let's find your perfect image"):
            st.session_state.messages_text.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar='icons/text_user.png'):
                st.write(prompt)

        # Generate a new response if last message is not from assistant
        if st.session_state.messages_text != [] and st.session_state.messages_text[-1]["role"] != "assistant":
            with st.chat_message("assistant", avatar='icons/assistant.png'):
                with st.spinner("Getting your image(s)..."):
                    response = fns.run_text_to_image(prompt)  
                    images = [img['image'] for img in response["metadatas"][0]]
                    captions = fns.generate_captions(response)

            cols = st.columns(3, vertical_alignment="top")

            imgs = []
            caps = []
            for col, image, caption in zip(cols, images, captions):
                with col:
                    st.image(image)
                    st.write(caption)
                    imgs.append(image)
                    caps.append(caption)
            message = {"role": "assistant", "content": imgs, "caption": caps}
            st.feedback(
                "thumbs",
                key=f"feedback_{len(st.session_state.messages_text)}",
                on_change=save_text_feedback,
                args=[len(st.session_state.messages_text)],
            )
            st.session_state.messages_text.append(message)
        
        if st.session_state.messages_text != []:
            st.button('Clear Chat History', on_click=clear_text_chat_history, icon=":material/delete:")


    if selected == "Voice Mode":
        audio_value = None
        prompt = None
        st.title('Voice Mode')

        msg = st.chat_message("assistant", avatar='icons/assistant.png')
        msg.write("Welcome to the Voice Mode Chat, how may I assist you today?")

        # Store generated responses
        if "messages_voice" not in st.session_state.keys():
            st.session_state.messages_voice = []

        # Display or clear chat messages
        for i, message in enumerate(st.session_state.messages_voice):
            with st.chat_message(message["role"], avatar='icons/voice_user.png' if message["role"] == "user" else "icons/assistant.png"):
                if message["role"] == "user":
                    st.audio(message["audio"])
                    st.write(message["content"])
                else:
                    feedback = message.get("feedback", None)
                    st.session_state[f"feedback_{i}"] = feedback
                    st.feedback(
                        "thumbs",
                        key=f"feedback_{i}",
                        disabled=feedback is not None,
                        on_change=save_voice_feedback,
                        args=[i],
                    )
                    columns = st.columns(3, vertical_alignment="top")
                    for col, image, cap, audio in zip(columns, message["content"], message["caption"], message["audio"]):
                        with col:
                            st.image(image)
                            st.write(cap)
                            st.audio(data=audio["data"], sample_rate=audio["sample_rate"])

        # User-provided prompt
        if (audio_value == None and prompt == None) or (len(st.session_state.messages_voice) >= 1 and prompt != st.session_state.messages_voice[-1]["content"]):
            with st.chat_message("user", avatar='icons/voice_user.png'):
                audio_value = st.audio_input("Record a voice message")

                if audio_value:
                    st.audio(audio_value)
                    prompt = fns.convert_audio_to_text(audio_value)
                    st.write(prompt)
                    st.session_state.messages_voice.append({"role": "user", "content": prompt, "caption": "a user's input", "audio": audio_value})

        # Generate a new response if last message is not from assistant
        if st.session_state.messages_voice != [] and st.session_state.messages_voice[-1]["role"] != "assistant":
            with st.chat_message("assistant", avatar='icons/assistant.png'):
                with st.spinner("Getting your image(s)..."):
                    response = fns.run_text_to_image(prompt)
                    images = [img['image'] for img in response["metadatas"][0]]
                    captions = fns.generate_captions(response)

            cols = st.columns(3, vertical_alignment="top")

            imgs = []
            caps = []
            audios = []
            for col, image, caption in zip(cols, images, captions):
                with col:
                    st.image(image)
                    st.write(caption)
                    with st.spinner("Generating audio..."):
                        audio_data, sample_rate = fns.generate_audio_from_text(caption)
                    st.audio(data=audio_data, sample_rate=sample_rate)
                    imgs.append(image)
                    caps.append(caption)
                    audios.append({
                        "data": audio_data,
                        "sample_rate": sample_rate
                    })
            message = {"role": "assistant", "content": imgs, "caption": captions, "audio": audios}
            st.feedback(
                "thumbs",
                key=f"feedback_{len(st.session_state.messages_voice)}",
                on_change=save_voice_feedback,
                args=[len(st.session_state.messages_voice)],
            )
            st.session_state.messages_voice.append(message)
            audio_value = None
        
        if st.session_state.messages_voice != []:
            st.button('New request', on_click=rerun, type="primary", icon=":material/add_circle:")
        if st.session_state.messages_voice != []:
            st.button('Clear Chat History', on_click=clear_voice_chat_history, icon=":material/delete:")

    hide_the_style = """
                    <style>
                    div[data-testid="stToolbar"] {visibility: hidden; height: 0%; position: fixed;}
                    div[data-testid="stDecoration"] {visibility: hidden; height: 0%; position: fixed;}
                    div[data-testid="stStatusWidget"] {visibility: hidden; height: 0%; position: fixed;}
                    #MainManu {visibility: hidden; height: 0%;}
                    footer {visibility: hidden; height: 0%;}
                    header {visibility: hidden; height: 0%;}
                    </style>
                    """
    st.markdown(hide_the_style,unsafe_allow_html=True)


if __name__ == "__main__":
    main()