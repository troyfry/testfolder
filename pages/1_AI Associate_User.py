import os
import pandas as pd
import streamlit as st
from streamlit_tags import st_tags
from langchain.chains import LLMChain
from langchain_community.llms import OpenAI
from langchain.prompts import PromptTemplate


# Function to create an empty CSV file if it doesn't exist
def create_empty_csv1(csv_file, columns):
    if not os.path.exists(csv_file):
        df = pd.DataFrame(columns=columns)
        df.to_csv(csv_file, index=False)


# Function to load palace items from the CSV file
def load_palace_items1(csv_file):
    if os.path.exists(csv_file):
        return pd.read_csv(csv_file)
    else:
        return pd.DataFrame(columns=['Palace'] + [f'item{i + 1}' for i in range(10)])


# Function to save palace items to the CSV file
def save_to_csv1(palace_name, items, csv_file):
    # Load the current data
    df = load_palace_items1(csv_file)

    # Check if the palace already exists and update it
    if palace_name in df['Palace'].values:
        df.loc[df['Palace'] == palace_name, [f'item{i + 1}' for i in range(len(items))]] = items
    else:
        # If the palace doesn't exist, append a new row
        new_row = [palace_name] + items + [''] * (10 - len(items))  # Fill remaining items with empty strings
        df.loc[len(df)] = new_row

    # Save the updated DataFrame to CSV
    df.to_csv(csv_file, index=False)

# Function to load items for a selected palace
def load_palace_items(palace_name, csv_file):
    try:
        if os.path.exists(csv_file):
            palace_data = pd.read_csv(csv_file)
            palace_row = palace_data[palace_data['Palace'] == palace_name]
            if not palace_row.empty:
                palace_row = palace_row.iloc[0]
                items = [palace_row[f'item{i + 1}'] for i in range(10) if
                         f'item{i + 1}' in palace_row and pd.notna(palace_row[f'item{i + 1}'])]
                return items
    except Exception as e:
        st.error(f"Error loading palace items: {str(e)}")
    return []

# Function to save palace items to CSV
def save_to_csv(palace_name, items, csv_file):
    try:
        new_entry = {'Palace': palace_name}
        for i, item in enumerate(items):
            new_entry[f'item{i + 1}'] = item

        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
        else:
            df = pd.DataFrame(columns=['Palace'] + [f'item{i + 1}' for i in range(10)])

        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        df.to_csv(csv_file, index=False)
    except Exception as e:
        st.error(f"Error saving to CSV: {str(e)}")

# Function to save data to category folder
def save_to_category_folder(topic, category, palace_name, items, bullet_points, imagery_list, app_directory):
    try:
        # Convert category to lowercase for case-insensitive comparison
        category_lower = category.lower()

        # Check if a folder with the same name (case-insensitive) already exists
        existing_folders = [f.lower() for f in os.listdir(app_directory) if
                            os.path.isdir(os.path.join(app_directory, f))]

        if category_lower in existing_folders:
            # If it exists, use the existing folder name (preserving original case)
            category_folder = os.path.join(app_directory,
                                           [f for f in os.listdir(app_directory) if f.lower() == category_lower][0])
        else:
            # If it doesn't exist, create a new folder
            category_folder = os.path.join(app_directory, category)
            os.makedirs(category_folder, exist_ok=True)

        filename = os.path.join(category_folder, f"{topic}-{palace_name}.txt")
        with open(filename, "w") as file:
            file.write(f"Topic: {topic}\nPalace: {palace_name}\n")
            for item, bullet, imagery in zip(items, bullet_points, imagery_list):
                file.write(f"{item}: {bullet} (Imagery: {imagery})\n")
        return filename
    except Exception as e:
        st.error(f"Error saving to category folder: {str(e)}")
        return None

# Function to get topic information from the LLM
def get_topic_info(topic, llm):
    try:
        topic_prompt = PromptTemplate(
            input_variables=["topic"],
            template=f"Provide important bullet points about {{topic}}:"
        )
        topic_chain = LLMChain(llm=llm, prompt=topic_prompt)
        response = topic_chain.run({"topic": topic})
        points = response.strip().split('\n')
        return [point.strip('- ') for point in points if point.strip()]
    except Exception as e:
        st.error(f"Error getting topic information: {str(e)}")
        return []

# Function to get memorable imagery for an item
def get_memorable_imagery(item, info, llm):
    try:
        prompt = f"""
        Using the memory palace method, create a simple mental imagery to associate the phrase '{info}' with the item '{item}':
        Make the associations interesting, obvious and in one sentence.
        """
        response = llm.predict(prompt)
        return response
    except Exception as e:
        st.error(f"Error getting memorable imagery: {str(e)}")
        return ""

def create_empty_csv(file_path, columns):
    try:
        pd.DataFrame(columns=columns).to_csv(file_path, index=False)
    except Exception as e:
        st.error(f"Error creating empty CSV: {str(e)}")

# Main app
def main():
    st.title("Association Creator")

    # Define filenames and directories
    home_directory = os.path.expanduser("~")
    app_directory = os.path.join(home_directory, "app")
    os.makedirs(app_directory, exist_ok=True)
    csv_file = os.path.join(app_directory, "palace_items.csv")
    category_csv_file = os.path.join(app_directory, "categories.csv")

    # Check if files exist and provide an option to create them if they don't
    if not os.path.exists(csv_file) or not os.path.exists(category_csv_file):
        st.error(f'Required files not found at "{app_directory}". Please click below.')
        st.write("")
        if st.button("Create palace_items.csv and categories.csv"):
            create_empty_csv(csv_file, ['Palace'] + [f'item{i + 1}' for i in range(10)])
            create_empty_csv(category_csv_file, ['Category'])
            st.success("Files created successfully! Please reload the page.")
            st.rerun()
    else:
        st.success("Required files found! You can proceed.")

    # Tabs for different functionalities
    tab1, tab2, tab3 = st.tabs(["Create Memory Palace", "View Results", "Manage Palaces"])

    with tab1:


        # Set up the OpenAI API key input
        openai_api_key = st.text_input('OpenAI API Key', type='password', disabled=True)

        try:
            llm = OpenAI(temperature=0.6, openai_api_key=openai_api_key)
        except Exception as e:
            st.error(f"Error initializing OpenAI: {str(e)}")
            return

        # Load existing palace data
        try:
            if os.path.exists(csv_file):
                palace_data = pd.read_csv(csv_file)
                palace_list = palace_data['Palace'].unique().tolist()
            else:
                palace_list = []
        except Exception as e:
            st.error(f"Error loading existing palace data: {str(e)}")
            palace_list = []

        # Palace selection or creation
        selected_palace = st.selectbox('Select an existing palace', [''] + palace_list, key='select_palace')
        new_palace = st.text_input('Or, add a new palace name', max_chars=25, key='new_palace',
                                   disabled=bool(selected_palace))

        items = []
        palace_name = selected_palace if selected_palace else new_palace

        # Load items if an existing palace is selected
        if palace_name:
            if selected_palace:
                items = load_palace_items(palace_name, csv_file)

                items = st_tags(
                    label='Memory palace items',
                    text='Press enter to add more items',
                    value=items,
                    maxtags=10,
                    key='exist_items'
                )
            else:
                items = st_tags(
                    label='Enter Memory palace items',
                    text='Press enter to add more items',
                    value=[],  # Initial items (empty)
                    suggestions=['desk', 'chair', 'door'],
                    maxtags=10,  # Maximum number of items
                    key='new_items'
                )

        # Category and topic
        try:
            if os.path.exists(category_csv_file):
                category_data = pd.read_csv(category_csv_file)
                category_list = sorted(set(category_data['Category'].dropna().tolist() + ['']))
            else:
                category_list = ['']
        except Exception as e:
            st.error(f"Error loading categories: {str(e)}")


        # Category selection or creation
        selected_category = st.selectbox('Select Category', category_list, key='select_category')
        new_category = st.text_input('Or, add a new category', key='new_category', disabled=bool(selected_category))
        category = selected_category if selected_category else new_category

        topic = st.text_input('Enter the topic to learn about', max_chars=100, key='topic')

        # New input for user-defined points
        user_points = st_tags(
            label='Enter key points about the topic',
            text='Press enter to add more points',
            value=[],
            key='user_points'
        )
        # Generate Associations button disabled if conditions are not met
        generate_button_disabled = not palace_name or len(items) < 5 or not category or not topic

        if st.button("Generate Associations", key='generate', disabled=generate_button_disabled):
            st.success("Making Associations......")

            # Use user-defined points instead of AI-generated ones
            bullet_points = user_points[:len(items)]  # Limit to the number of items
            imagery_list = [get_memorable_imagery(item, point, llm) for item, point in zip(items, bullet_points)]

            # Display the associations
            st.markdown(f"**Memory Palace: {palace_name}**")
            st.markdown(f"**Topic: {topic}**")
            st.markdown("---")
            for item, point, imagery in zip(items, bullet_points, imagery_list):
                st.markdown(f"**{item}**:\n {point} \n\n(Memorable Imagery: {imagery})")

            # Save to CSV and category folder
            if not selected_palace:  # Only save if it's a new palace
                save_to_csv(palace_name, items, csv_file)
            file_path = save_to_category_folder(topic, category, palace_name, items, bullet_points,
                                                imagery_list, app_directory)

            if file_path:
                st.success(f"Associations saved to {file_path}.")


    with tab2:
        st.header("View Associations")

        # Get the app directory
        home_directory = os.path.expanduser("~")
        app_directory = os.path.join(home_directory, "app")

        # Get the list of categories (folders inside app_directory)
        categories = [d for d in os.listdir(app_directory) if os.path.isdir(os.path.join(app_directory, d))]
        if not categories:
            st.write("No categories found.")
        else:
            selected_category = st.selectbox("Select a Category", categories)

            if selected_category:
                category_folder = os.path.join(app_directory, selected_category)
                # Get list of txt files in the category folder
                txt_files = [f for f in os.listdir(category_folder) if f.endswith('.txt')]

                if not txt_files:
                    st.write("No association files found in this category.")
                else:
                    selected_file = st.selectbox("Select an Association File", txt_files)

                    if selected_file:
                        # Read the content of the txt file
                        file_path = os.path.join(category_folder, selected_file)
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                            # Parse and display the content
                            lines = content.strip().split('\n')
                            if len(lines) >= 2:
                                topic_line = lines[0]
                                palace_line = lines[1]
                                st.markdown(f"**{topic_line}**")
                                st.markdown(f"**{palace_line}**")
                                st.write("")
                                for line in lines[2:]:
                                    # Each line is '{item}: {bullet} (Imagery: {imagery})'
                                    if line:
                                        try:
                                            item_part, rest = line.split(':', 1)
                                            bullet_part, imagery_part = rest.rsplit('(Imagery:', 1)
                                            bullet = bullet_part.strip()
                                            imagery = imagery_part.strip(') ').strip()
                                            item = item_part.strip()
                                            st.markdown(f"**{item}**")
                                            st.write(f"{bullet}")
                                            st.write(f"*Imagery:* {imagery}")
                                            st.write("---")
                                        except Exception as e:
                                            st.write(line)
                            else:
                                st.write(content)
                        except Exception as e:
                            st.error(f"Error reading or parsing file: {str(e)}")

    with tab3:

        # Define the CSV file path
        home_directory = os.path.expanduser("~")
        app_directory = os.path.join(home_directory, "app")
        os.makedirs(app_directory, exist_ok=True)
        csv_file = os.path.join(app_directory, "palace_items.csv")

        # Create CSV if it doesn't exist
        create_empty_csv1(csv_file, ['Palace'] + [f'item{i + 1}' for i in range(10)])

        # Palace name input
        palace_name = st.text_input('Enter your memory palace name:', max_chars=25)

        # Use streamlit-tags to input multiple palace items
        palace_items = st_tags(
            label="Enter items for your memory palace:",
            text="Press enter to add more",
            value=[],  # Initial items (empty)
            suggestions=["Book", "Lamp", "Desk", "Mirror"],  # Optional suggestions
            maxtags=10,  # Maximum number of items
            key='palace_items'
        )

        # Save items to CSV when button is clicked
        if st.button("Save Palace Items"):
            if palace_name and palace_items:
                save_to_csv1(palace_name, palace_items, csv_file)
                st.success(f"Palace '{palace_name}' and items saved successfully!")
            else:
                st.error("Please enter both a palace name and items.")

        # Display the current palace data
        st.subheader("Current Palace Data")
        df = load_palace_items1(csv_file)
        st.dataframe(df)

if __name__ == "__main__":
    main()