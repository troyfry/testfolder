import streamlit as st


st.set_page_config(
    page_title="Studeaze",
    page_icon="👋",
    layout="wide"
)
hide_default_format = """
       <style>
       #MainMenu {visibility: hidden; }
       footer {visibility: hidden;}
       </style>
       """
st.markdown(hide_default_format, unsafe_allow_html=True)

st.write("# Welcome to Studeaze! 👋")



st.sidebar.success("Select a demo above.")

#openai_api_key = st.sidebar.text_input('OpenAI API Key')

#or Rememrable
st.markdown(
    """
    Welcome to studeaze, a place where learning is made simple and interesting. 
    
    Here You can:

    - easily personalize your learning
    - upload your own material to study 
    - Enter your topic of choice and let AI guide you
    

    """)

