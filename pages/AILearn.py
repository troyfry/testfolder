import openai
import streamlit as st
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

# Get OpenAI API key
openai_api_key = st.sidebar.text_input('OpenAI API Key')

llm = OpenAI(temperature=0.6, openai_api_key=openai_api_key)

# Instructions for the user
instruct = """
Complete the input fields. The ordered list of items you 
enter will be associated with the main points of the AI response.
hint: For your palace and items choose a place that you know well
"""
with st.expander("Instructions"):
    st.write(instruct)

st.title("Make Learning Interesting")

if not openai_api_key.startswith('sk-'):
    st.warning('Please enter your OpenAI key!')

# File path for the CSV file
csv_file = 'palace_items.csv'

# Load existing data from CSV
if os.path.exists(csv_file):
    palace_data = pd.read_csv(csv_file)
else:
    palace_data = pd.DataFrame(columns=['Palace'] + [f'Item_{i+1}' for i in range(10)])

with st.expander("expand me"):

    # Dropdown to select an existing palace
    palace_list = palace_data['Palace'].unique().tolist()
    selected_palace = st.selectbox('Select an existing palace (optional)', [''] + palace_list)
    topic = st.text_input(r"$\textsf{\Large Enter the topic you want to learn about (i.e. World War 1):}$", max_chars=50)

    # Initialize variables
    number_choice = 5  # Default number of points
    prefill_palace_name = ''
    prefill_items = [''] * 10

    # Update values if a palace is selected
    if selected_palace:
        prefill_data = palace_data[palace_data['Palace'] == selected_palace].iloc[0]
        
        # Count the non-empty items before converting them to strings
        existing_items_count = sum([1 for i in range(10) if pd.notna(prefill_data[f'Item_{i+1}']) and prefill_data[f'Item_{i+1}'] != ''])
        
        # Now process and store the items
        prefill_items = [str(prefill_data[f'Item_{i+1}']) for i in range(10)]  # Ensure items are strings
        number_choice = existing_items_count  # Set number_choice based on the number of existing items

    # Handle prefill button
   # if selected_palace and st.button("Prefill Room Items"):  # Prefill Button
     #   st.session_state.prefill = True
     #   st.experimental_rerun()

    # Input fields for number_choice if a new palace is being created
    if not selected_palace:
        number_choice = st.number_input(r"$\textsf{\Large Enter number of Main points (5-10) to retrieve:}$", value=5, format="%d", min_value=5, max_value=10)

    # Input field for palace name, disabled if a palace is selected
    palace_name = st.text_input(
        r"$\textsf{\Large Enter a name for your memory palace (i.e mybedroom): }$", 
        max_chars=15, 
        value=prefill_palace_name if not selected_palace else '',
        disabled=bool(selected_palace)
    )
    

    # Adjust the number of input fields based on number_choice
    items = [st.text_input(f"Enter item {i+1} for your memory palace:", max_chars=16, value=prefill_items[i] if i < len(prefill_items) else '') for i in range(number_choice)]

    
    # Define the full palace name based on whether the palace is selected or newly created
    if selected_palace:
        full_palace_name = f"{topic} - {selected_palace}"
    else:
        full_palace_name = f"{topic} - {palace_name}"


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
        new_entry[f'Item_{i+1}'] = item
    
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
    else:
        df = pd.DataFrame(columns=['Palace'] + [f'Item_{i+1}' for i in range(10)])
    
    df = df.append(new_entry, ignore_index=True)
    df.to_csv(csv_file, index=False)

def main():
    if st.button("Associate"):
        filename = f"{topic}.txt"
        st.write("\nAssociating...")
        bullet_points = get_topic_info(topic, number_choice)
        st.write("\nGenerating memorable mental imagery with your palace items...")
        imagery_list = [get_memorable_imagery(items[i], bullet_points[i] if i < len(bullet_points) else '') for i in range(number_choice)]
        
        st.markdown(f"**Memory Palace: {full_palace_name}**")
        st.markdown("---")  # Horizontal line

        for i in range(number_choice):
            st.markdown(f"**{items[i]}**: {bullet_points[i] if i < len(bullet_points) else 'N/A'} (Memorable Imagery: {imagery_list[i] if i < len(imagery_list) else 'N/A'})")

        # Save only if a new palace is created
        if not selected_palace:
            save_to_csv(palace_name, items, csv_file)
            st.success(f"Palace info saved to {csv_file}")

    # Save the information to a text file
        with open(filename, "w") as file:
            file.write(f"Topic: {topic}: Palace: {full_palace_name}\n")
            for i in range(number_choice):
                file.write(f"\n{items[i]}: {bullet_points[i] if i < len(bullet_points) else 'N/A'} (Imagery: {imagery_list[i] if i < len(imagery_list) else 'N/A'})\n")

        with open(f"{filename}", "r") as file:
            response_contents = file.read()
            st.download_button("Download results", response_contents, file_name=f"{filename}")
            os.remove(filename)
    
    #if st.button("Clear Text Fields"):
     #   st.rerun()

if __name__ == "__main__":
    main()
