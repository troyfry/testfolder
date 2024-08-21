
import os
import platform
import pandas as pd
import streamlit as st
from langchain import LLMChain, OpenAI
from langchain.prompts import PromptTemplate

# Determine the home directory and construct the path
home_directory = os.path.expanduser("~")
app_directory = os.path.join(home_directory, "app")

# Print debug information
st.write("Home Directory:", home_directory)
st.write("App Directory:", app_directory)
st.write("Current Working Directory:", os.getcwd())

# List files in the directory
if os.path.exists(app_directory):
    st.write("Files in App Directory:", os.listdir(app_directory))
else:
    st.write("App Directory does not exist.")

# Get OpenAI API key
openai_api_key = st.text_input('OpenAI API Key', disabled=True)
llm = OpenAI(temperature=0.6, openai_api_key=openai_api_key)

# Hide default Streamlit menu and footer
hide_default_format = """
       <style>
       #MainMenu {visibility: hidden; }
       footer {visibility: hidden;}
       </style>
       """
st.markdown(hide_default_format, unsafe_allow_html=True)

st.markdown("## Study with ease ##\n Mastering Memory Palaces")
st.markdown("### Let AI Guide You ###")

# Define filenames
og_file = "palace_items.csv"
category_file = "categories.csv"

# Determine the home directory and construct the path
home_directory = os.path.expanduser("~")
if platform.system() == "Windows":
    app_directory = os.path.join(home_directory, "app")
else:
    app_directory = os.path.join(home_directory, "app")

# Create the directory if it does not exist
os.makedirs(app_directory, exist_ok=True)

# Construct the full paths for palace_items.csv and categories.csv
csv_file = os.path.join(app_directory, 'palace_items.csv')
category_csv_file = os.path.join(app_directory, 'categories.csv')

# Function to create an empty CSV file with the given columns
def create_empty_csv(file_path, columns):
    pd.DataFrame(columns=columns).to_csv(file_path, index=False)

# Check if files exist and provide an option to create them if they don't
if not os.path.exists(csv_file) or not os.path.exists(category_csv_file):
    st.warning("Required files not found! Please create them to continue.")
    if st.button("Create palace_items.csv and categories.csv"):
        # Create the necessary files with appropriate columns
        create_empty_csv(csv_file, ['Palace'] + [f'Item_{i + 1}' for i in range(10)])
        create_empty_csv(category_csv_file, ['Category'])
        st.success("Files created successfully! Please reload the page.")
        st.experimental_rerun()
else:
    st.success("Required files found! You can proceed.")

# Load existing palace data from CSV
if os.path.exists(csv_file):
    palace_data = pd.read_csv(csv_file)
else:
    palace_data = pd.DataFrame(columns=['Palace'] + [f'Item_{i + 1}' for i in range(10)])

# Load existing categories from CSV
if os.path.exists(category_csv_file):
    category_data = pd.read_csv(category_csv_file)
    category_list = sorted(set(category_data['Category'].dropna().tolist() + ['']))
else:
    category_data = pd.DataFrame(columns=['Category'])
    category_list = ['']

# Initialize variables
number_choice = 5  # Default number of points
prefill_palace_name = ''
prefill_items = [''] * 10
with st.expander("Start Here"):
    entered_pal, user_pal = st.columns(2)
    palace_list = palace_data['Palace'].unique().tolist()
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
        prefill_data = palace_data[palace_data['Palace'] == selected_palace].iloc[0]
        existing_items_count = sum(
            [1 for i in range(10) if pd.notna(prefill_data[f'Item_{i + 1}']) and prefill_data[f'Item_{i + 1}'] != ''])
        prefill_items = [str(prefill_data[f'Item_{i + 1}']) for i in range(10)]
        number_choice = existing_items_count

    # Input fields for number_choice if a new palace is being created
    if not selected_palace:
        number_choice = st.slider('Number of Main points (5-10) to retrieve:', min_value=5, max_value=10, value=5)

    st.markdown("""<hr style="border:2px solid white">""", unsafe_allow_html=True)

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


    def save_to_category_folder(category, palace_name, items, bullet_points, imagery_list):
        # Create category folder if it does not exist
        category_folder = os.path.join(app_directory, category)
        os.makedirs(category_folder, exist_ok=True)

        # Define filename and save to category folder
        filename = os.path.join(category_folder, f"{palace_name}.txt")
        with open(filename, "w") as file:
            file.write(f"Topic: {topic}\nPalace: {palace_name}\n")
            for i in range(number_choice):
                file.write(
                    f"{items[i]}: {bullet_points[i] if i < len(bullet_points) else 'N/A'} (Imagery: {imagery_list[i] if i < len(imagery_list) else 'N/A'})\n")
        return filename

    def add_category_to_csv(new_category, category_csv_file):
        # Check if the category file exists and load existing data
        if os.path.exists(category_csv_file):
            category_data = pd.read_csv(category_csv_file)
        else:
            category_data = pd.DataFrame(columns=['Category'])

        # Add new category if it does not exist
        if new_category and new_category not in category_data['Category'].tolist():
            category_data = category_data.append({'Category': new_category}, ignore_index=True)
            category_data.to_csv(category_csv_file, index=False)


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

            if not selected_palace:
                try:
                    save_to_csv(palace_name, items, csv_file)

                except AttributeError as e:
                    # Handle the AttributeError and display a user-friendly message
                    st.error(f"An error occurred: {e}")
                    st.write(
                        "Create the required files.")

            st.success(f"Palace info saved to {csv_file}")
            selected_or_new_category = selected_category if selected_category else new_category
            if selected_or_new_category:
                filename = save_to_category_folder(selected_or_new_category, full_palace_name, items, bullet_points,
                                                   imagery_list)
              #  with open(filename, "r") as file:
              #      response_contents = file.read()
              #      st.download_button("Download results", response_contents, file_name=os.path.basename(filename))

            if new_category and new_category != selected_category:
                add_category_to_csv(new_category, category_csv_file)

            if st.button('Reset'):
                st.experimental_rerun()




    if __name__ == "__main__":
        main()
