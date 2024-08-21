import streamlit as st
import pandas as pd
import io
import os
import platform
from langchain import PromptTemplate, LLMChain, OpenAI

# Hide default Streamlit menu and footer
hide_default_format = """
       <style>
       #MainMenu {visibility: hidden; }
       footer {visibility: hidden;}
       </style>
       """
st.markdown(hide_default_format, unsafe_allow_html=True)

st.markdown("## Study with ease ##\n Mastering Memory Palaces ")
st.markdown(
    """
    ### Let AI Guide You ###
    """)

# Get OpenAI API key
openai_api_key = st.text_input('OpenAI API Key', disabled=True)
llm = OpenAI(temperature=0.6, openai_api_key=openai_api_key)

# Instructions for the user
instruct = """
Please note that to use the AI-powered features in the Memory Palace tool, you might need your own OpenAI API key with a 
balance of about $1 or more. This ensures that the AI can generate the associations effectively for your learning sessions.\n
**Instructions:**

1. **Enter the name of a palace** (a place you know well) or **Add a new palace**.
2. **Provide the topic you wish to learn about.**
3. **Specify the number of main points you want the AI to retrieve.**
4. **List the palace items in your palace.** Each item will be associated with one of the main points retrieved by the AI.

**Note:** Keep in mind the principle of "GIGO" - Garbage In, Garbage Out.
"""

with st.expander("Prerequisite:"):
    st.markdown(instruct)

# Initialize variables
number_choice = 5  # Default number of points
prefill_palace_name = ''
prefill_items = [''] * 10

# Load existing categories from an in-memory list
category_list = []

st.markdown("""<hr style="border:2px solid white">""", unsafe_allow_html=True)

# Inputs for user
entered_pal, user_pal = st.columns(2)
category_col, new_category_col = st.columns([3, 1])

# Category selection or creation
with category_col:
    selected_category = st.selectbox('Select Category', category_list)
    new_category_disabled = bool(selected_category)

with new_category_col:
    new_category = st.text_input('New Category (if applicable)', '', disabled=new_category_disabled)
    new_category_disabled = not bool(new_category)

# Dropdown to select an existing palace
with entered_pal:
    palace_list = []
    selected_palace = st.selectbox('Select an existing palace (optional)', [''] + palace_list)

# Input field for palace name, disabled if a palace is selected
with user_pal:
    palace_name = st.text_input(
        'Add new memory palace (i.e myRoom)',
        max_chars=15,
        value=prefill_palace_name if not selected_palace else '',
        disabled=bool(selected_palace)
    )

topic = st.text_input('Topic to learn about (i.e. World War 1)', max_chars=50)

# Update values if a palace is selected
if selected_palace:
    # Sample data for demo
    prefill_data = {'Palace': selected_palace, **{f'Item_{i + 1}': f'Item {i + 1}' for i in range(10)}}
    existing_items_count = sum([1 for i in range(10) if prefill_data[f'Item_{i + 1}']])
    prefill_items = [str(prefill_data[f'Item_{i + 1}']) for i in range(10)]
    number_choice = existing_items_count

# Input fields for number_choice if a new palace is being created
if not selected_palace:
    number_choice = st.slider('Number of Main points (5-10) to retrieve:', min_value=5, max_value=10, value=5)

# Adjust the number of input fields based on number_choice
items = [st.text_input(f"Enter item {i + 1} for your memory palace:", max_chars=16,
                       value=prefill_items[i] if i < len(prefill_items) else '') for i in range(number_choice)]

# Define the full palace name based on whether the palace is selected or newly created
if selected_palace:
    full_palace_name = f"{topic} - {selected_palace}"
else:
    full_palace_name = f"{topic} - {palace_name}"

disable_associate_button = any(
    item.strip() == '' for item in items) or full_palace_name.strip() == '' or topic.strip() == ''

# Define the prompt templates
topic_prompt = PromptTemplate(
    input_variables=["topic"],
    template=f"Provide {number_choice} important bullet points about {topic}:"
)
topic_chain = LLMChain(llm=llm, prompt=topic_prompt)


def get_topic_info(topic, number_choice):
    response = topic_chain.run({"topic": topic})
    points = response.strip().split('\n')
    return [point.strip('- ') for point in points if point.strip()][:number_choice]


def get_memorable_imagery(item, info):
    prompt = f"""
    Using the memory palace method, create a succinct, vivid and memorable mental imagery to associate the phrase '{info}' with the item '{item}':
    Make the associations interesting, obvious and brief.
    """
    response = llm.predict(prompt)
    return response


def create_csv_buffer(palace_name, items):
    df = pd.DataFrame(columns=['Palace'] + [f'Item_{i + 1}' for i in range(10)])
    new_entry = {'Palace': palace_name}
    for i, item in enumerate(items):
        new_entry[f'Item_{i + 1}'] = item
    df = df.append(new_entry, ignore_index=True)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer


def create_results_buffer(palace_name, topic, items, bullet_points, imagery_list):
    buffer = io.StringIO()
    buffer.write(f"Topic: {topic}\nPalace: {palace_name}\n")
    for i in range(number_choice):
        buffer.write(
            f"{items[i]}: {bullet_points[i] if i < len(bullet_points) else 'N/A'} (Imagery: {imagery_list[i] if i < len(imagery_list) else 'N/A'})\n")
    buffer.seek(0)
    return buffer


def speak_text(text):
    st.markdown(
        f"""
        <script>
        function speak(text) {{
            var msg = new SpeechSynthesisUtterance(text);
            window.speechSynthesis.speak(msg);
        }}
        speak("{text}");
        </script>
        """,
        unsafe_allow_html=True
    )


def main():
    if st.button("Associate", disabled=disable_associate_button):
        st.success("\nAssociating...")
        bullet_points = get_topic_info(topic, number_choice)
        st.success("\nGenerating memorable mental imagery with your palace items...")
        imagery_list = [get_memorable_imagery(items[i], bullet_points[i] if i < len(bullet_points) else '') for i in
                        range(number_choice)]

        st.markdown(f"**Memory Palace: {full_palace_name}**")
        st.markdown("---")

        for i in range(number_choice):
            st.markdown(
                f"**{items[i]}**: {bullet_points[i] if i < len(bullet_points) else 'N/A'} \n(Memorable Imagery: {imagery_list[i] if i < len(imagery_list) else 'N/A'})")

        # Create and offer download for palace_items.csv
        palace_csv_buffer = create_csv_buffer(full_palace_name, items)
        st.download_button(
            label="Download palace_items.csv",
            data=palace_csv_buffer,
            file_name="palace_items.csv",
            mime="text/csv"
        )

        # Create and offer download for results
        results_buffer = create_results_buffer(full_palace_name, topic, items, bullet_points, imagery_list)
        st.download_button(
            label="Download results",
            data=results_buffer,
            file_name=f"{full_palace_name}.txt",
            mime="text/plain"
        )

        # Button to trigger text-to-speech
        if st.button("Read Out Loud"):
            speak_text(" ".join(bullet_points + imagery_list))

        if st.button('Reset'):
            st.experimental_rerun()


if __name__ == "__main__":
    main()
