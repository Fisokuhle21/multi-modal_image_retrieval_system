import streamlit as st
from streamlit_option_menu import option_menu
import shared.functions as fns

st.set_page_config(page_title="Multimodal Image Retrieval System")

selected = option_menu(
    menu_title = None,
    options = ["Text Mode", "Voice Mode"],
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
    for message in st.session_state.messages_text:
        with st.chat_message(message["role"], avatar='icons/text_user.png' if message["role"] == "user" else "icons/assistant.png"):
            if message["role"] == "user":
                st.write(message["content"])
            else:
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
        st.session_state.messages_text.append(message)

    def clear_chat_history():
        st.session_state.messages_text = []
    
    if st.session_state.messages_text != []:
        st.button('Clear Chat History', on_click=clear_chat_history)


if selected == "Voice Mode":
    st.title('Voice Mode')

    msg = st.chat_message("assistant", avatar='icons/assistant.png')
    msg.write("Welcome to the Voice Mode Chat, how may I assist you today?")

    # Store generated responses
    if "messages_voice" not in st.session_state.keys():
        st.session_state.messages_voice = []

    # Display or clear chat messages
    for message in st.session_state.messages_voice:
        with st.chat_message(message["role"], avatar='icons/voice_user.png' if message["role"] == "user" else "icons/assistant.png"):
            if message["role"] == "user":
                st.audio(message["audio"])
                st.write(message["content"])
            else:
                columns = st.columns(3, vertical_alignment="top")
                for col, image, cap, audio in zip(columns, message["content"], message["caption"], message["audio"]):
                    with col:
                        st.image(image)
                        st.write(cap)
                        st.audio(data=audio["data"], sample_rate=audio["sample_rate"])

    # User-provided prompt
    if st.session_state.messages_voice == [] or st.session_state.messages_voice[-1]["role"] == "assistant":
        with st.chat_message("user", avatar='icons/voice_user.png'):
            audio_value = None
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
        st.session_state.messages_voice.append(message)

    def clear_chat_history():
        st.session_state.messages_voice = []
    
    if st.session_state.messages_voice != []:
        st.button('Clear Chat History', on_click=clear_chat_history)

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