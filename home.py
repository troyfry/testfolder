import streamlit as st
import os


st.set_page_config(
    page_title="Memory Palace Tools",
    page_icon="👋",
    layout="wide"
)



st.write("# Memory Palace Tool! 📚")
# Instructions for the user
instruct = """
Require files: palace_items.csv & categories.csv
- **For Mac:** '/Users/yourusername/'
- **For Windows:** 'C:\\Users\\yourusername\\'

**Instructions:**

1. **Enter the name of a palace** (a place you know well) or **Add a new palace**.
2. **Provide the topic and category you wish to learn about.**
3. **Specify the number of main points you want the AI to retrieve.** (If selecting from an existing palace, the number of main points will match the number of palace items.)
4. **List the palace items in your palace.** Each item will be associated with one of the main points retrieved by the AI.

**Note:** Keep in mind the principle of "GIGO" - Garbage In, Garbage Out.
"""


# openai_api_key = st.sidebar.text_input('OpenAI API Key')

# or Rememrable
st.markdown(
    """
    Welcome to Memory Palace Tools, a place where learning is made simple and interesting. Create memorable associations
    between the things you want to learn and familiar places; allowing the information to stick
    *FASTER* and *LONGER*... 

    Here You can:

    - Personalize your learning
    - Organize your topics 
    - Enter your topic of choice and let AI guide you


    """)

with st.expander("Prerequisite:"):
    st.markdown(f'<p style="font-size:14px; color:blue;">{instruct}</p>', unsafe_allow_html=True)

    # Determine the home directory and construct the path
    home_directory = os.path.expanduser("~")
    app_directory = os.path.join(home_directory, "app")



