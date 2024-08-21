import streamlit as st


# Function to include JavaScript for text-to-speech
def speak_text(text):
    st.markdown(
        f"""
        <script>
        function speak(text) {{
            var msg = new SpeechSynthesisUtterance(text);
            window.speechSynthesis.speak(msg);
        }}
        speak("{text.replace('"', '\\"').replace("'", "\\'")}");
        </script>
        """,
        unsafe_allow_html=True
    )


st.title("Read Aloud App")

# File uploader for .txt files
uploaded_file = st.file_uploader("Choose a text file", type="txt")

if uploaded_file is not None:
    # Read the content of the file
    content = uploaded_file.read().decode("utf-8")

    # Display the content of the file
    st.text_area("File Content", content, height=300)

    # Button to read the content aloud
    st.link_button("Read Aloud", url="https://ttsmaker.com/", disabled=True)


