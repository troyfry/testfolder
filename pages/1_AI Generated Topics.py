Perfectly
working
# Working code testfolder/AI Topic 8/13

import openai
import streamlit as st
from streamlit_gsheets import GSheetsConnection
from langchain import PromptTemplate, LLMChain, OpenAI
import pandas as pd
import os

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
**Save "palace_items.csv" to the appropriate location on your local drive:**

- **For Mac:** '/Users/yourusername/'
- **For Windows:** 'C:\\Users\\yourusername\\'

**Instructions:**

1. **Enter the name of a palace** (a place you know well) or **Add a new palace**.
2. **Provide the topic you wish to learn about.**
3. **Specify the number of main points you want the AI to retrieve.** (If selecting from an existing palace, the number of main points will match the number of palace items.)
4. **List the palace items in your palace.** Each item will be associated with one of the main points retrieved by the AI.

**Note:** Keep in mind the principle of "GIGO" - Garbage In, Garbage Out.
"""
og_file = "palace_items.csv"
with st.expander("Prerequisite:"):
    st.markdown(instruct)
    with open(og_file, "r") as file:
        response_contents = file.read()
        st.download_button("Download palace_items.csv", response_contents, file_name=f"{og_file}")

# if not openai_api_key.startswith('sk-'):
#   st.warning('Please enter your OpenAI key!')

# File path for the CSV file
home_directory = os.path.expanduser("~")
csv_file = file_path = os.path.join(home_directory, 'palace_items.csv')

# Load existing data from CSV
if os.path.exists(csv_file):
    palace_data = pd.read_csv(csv_file)
else:
    palace_data = pd.DataFrame(columns=['Palace'] + [f'Item_{i + 1}' for i in range(10)])
# Initialize variables
number_choice = 5  # Default number of points
prefill_palace_name = ''
prefill_items = [''] * 10

with st.expander("Start Here"):
    entered_pal, user_pal = st.columns(2)
    palace_list = palace_data['Palace'].unique().tolist()
    # Add content to the first column
    with entered_pal:
        # Dropdown to select an existing palace

        selected_palace = st.selectbox('Select an existing palace (optional)', [''] + palace_list)

    # Add content to the second column
    with user_pal:
        # Input field for palace name, disabled if a palace is selected
        palace_name = st.text_input(
            'Add new memory palace (i.e myRoom)',
            max_chars=15,
            value=prefill_palace_name if not selected_palace else '',
            disabled=bool(selected_palace)
        )

    topic = st.text_input('Topic to learn about (i.e. World War 1)', max_chars=50)

    # Update values if a palace is selected
    if selected_palace:
        prefill_data = palace_data[palace_data['Palace'] == selected_palace].iloc[0]

        # Count the non-empty items before converting them to strings
        existing_items_count = sum(
            [1 for i in range(10) if pd.notna(prefill_data[f'Item_{i + 1}']) and prefill_data[f'Item_{i + 1}'] != ''])

        # Now process and store the items
        prefill_items = [str(prefill_data[f'Item_{i + 1}']) for i in range(10)]  # Ensure items are strings
        number_choice = existing_items_count  # Set number_choice based on the number of existing items

    # Handle prefill button
    # if selected_palace and st.button("Prefill Room Items"):  # Prefill Button
    #   st.session_state.prefill = True
    #   st.experimental_rerun()

    # Input fields for number_choice if a new palace is being created
    if not selected_palace:
        number_choice = st.slider('Number of Main points (5-10) to retrieve:', min_value=5,
                                  max_value=10, value=5)
    st.markdown(
        """<hr style="border:2px solid white">""",
        unsafe_allow_html=True
    )

    # Adjust the number of input fields based on number_choice
    items = [st.text_input(f"Enter item {i + 1} for your memory palace:", max_chars=16,
                           value=prefill_items[i] if i < len(prefill_items) else '') for i in range(number_choice)]

    # Define the full palace name based on whether the palace is selected or newly created
    if selected_palace:
        full_palace_name = f"{topic} - {selected_palace}"
    else:
        full_palace_name = f"{topic} - {palace_name}"
        # Check if any input item is empty

    disable_associate_button = any(
        item.strip() == '' for item in items) or full_palace_name.strip() == '' or topic.strip() == ''

    # Define the prompt templates
    topic_prompt = PromptTemplate(
        input_variables=["topic"],
        template=f"Provide {number_choice} important bullet points about {topic}:"
    )

    # Define the chains
    topic_chain = LLMChain(llm=llm, prompt=topic_prompt)


def get_topic_info(topic, number_choice):
    response = topic_chain.run({"topic": topic})
    points = response.strip().split('\n')
    # Ensure we only use the number of points specified by number_choice
    return [point.strip('- ') for point in points if point.strip()][:number_choice]


def get_memorable_imagery(item, info):
    prompt = f"""
    Using the memory palace method, create a succinct, vivid and memorable mental imagery to associate the phrase '{info}' with the item '{item}':
    Make the associations interesting, obvious and brief.
    """
    response = llm.predict(prompt)
    return response


def save_to_csv(palace_name, items, csv_file):
    new_entry = {'Palace': palace_name}
    for i, item in enumerate(items):
        new_entry[f'Item_{i + 1}'] = item

    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
    else:
        df = pd.DataFrame(columns=['Palace'] + [f'Item_{i + 1}' for i in range(10)])

    df = df.append(new_entry, ignore_index=True)
    df.to_csv(csv_file, index=False)


def main():
    # Associate button is disabled if any input items are empty
    if st.button("Associate", disabled=disable_associate_button):
        filename = f"{topic}.txt"
        st.success("\nAssociating...")
        bullet_points = get_topic_info(topic, number_choice)
        st.success("\nGenerating memorable mental imagery with your palace items...")
        imagery_list = [get_memorable_imagery(items[i], bullet_points[i] if i < len(bullet_points) else '') for i in
                        range(number_choice)]

        st.markdown(f"**Memory Palace: {full_palace_name}**")
        st.markdown("---")  # Horizontal line

        for i in range(number_choice):
            st.markdown(
                f"**{items[i]}**: {bullet_points[i] if i < len(bullet_points) else 'N/A'} \n(Memorable Imagery: {imagery_list[i] if i < len(imagery_list) else 'N/A'})")

        # Save only if a new palace is created
        if not selected_palace:
            save_to_csv(palace_name, items, csv_file)
            st.success(f"Palace info saved to {csv_file}")

        # Save the information to a text file
        with open(filename, "w") as file:
            file.write(f"Topic: {topic}: Palace: {full_palace_name}\n")
            for i in range(number_choice):
                file.write(
                    f"\n{items[i]}: {bullet_points[i] if i < len(bullet_points) else 'N/A'} (Imagery: {imagery_list[i] if i < len(imagery_list) else 'N/A'})\n")

        with open(f"{filename}", "r") as file:
            response_contents = file.read()
            st.download_button("Download results", response_contents, file_name=f"{filename}")

        if st.button('Reset'):
            st.experimental_rerun()

            # os.remove(filename)


if __name__ == "__main__":
    main()


