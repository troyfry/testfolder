import streamlit as st
from streamlit_tags import st_tags
from langchain.chains import LLMChain
from langchain_community.llms import OpenAI
from langchain.prompts import PromptTemplate
from database_operations import DatabaseOperations
import json
import os

# Initialize database
db = DatabaseOperations()

def display_instructions():
    st.markdown("""
    # Memory Palace App: User Guide

    Welcome to the Memory Palace App! This guide will help you understand how to use the app effectively and manage your data.

    ## Important: Data Management

    **Your data is temporarily stored during each session. To keep your work, make sure to save it before closing the app or refreshing the page.**

    - Data is refreshed (reset to a blank state) when you:
      - Close and reopen the app
      - Refresh the browser page
      - After a period of inactivity on Streamlit Cloud

    - To retain your data across sessions:
      1. Go to the "Save/Load Data" tab
      2. Click "Download Data" to save your current data as a JSON file
      3. When you return, use the "Load Data" option to upload your saved file

    ## How to Use the App

    1. Create Memory Palaces in the "Create Memory Palace" tab
    2. View your results in the "View Results" tab
    3. Manage your palaces in the "Manage Palaces" tab
    4. Save and load your data in the "Save/Load Data" tab

    Remember to save your data regularly, especially after making significant changes!
    """)

def save_data():
    data = db.export_data()
    st.download_button(
        label="Download Data",
        data=json.dumps(data, indent=2),
        file_name="memory_palace_data.json",
        mime="application/json"
    )

def load_data():
    uploaded_file = st.file_uploader("Choose a file to upload", type="json")
    if uploaded_file is not None:
        data = json.load(uploaded_file)
        db.import_data(data)
        st.success("Data loaded successfully!")


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

# Main app
def main():
    st.title("Association Creator")

    # Add a collapsible section for instructions at the top
    with st.expander("📘 Click here for User Instructions"):
        display_instructions()

    # Set up the OpenAI API key input
    openai_api_key = st.text_input('OpenAI API Key', type='password', disabled=True)

    try:
        llm = OpenAI(temperature=0.6, openai_api_key=openai_api_key)
    except Exception as e:
        st.error(f"Error initializing OpenAI: {str(e)}")
        return

    # Tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs(["Create Memory Palace", "View Results", "Manage Palaces", "Save/Load Data"])


    with tab1:
        # Palace selection or creation
        palaces = db.get_palaces()
        palace_options = [""] + [palace[1] for palace in palaces]
        selected_palace = st.selectbox('Select an existing palace', palace_options, key='select_palace')
        new_palace = st.text_input('Or, add a new palace name', max_chars=25, key='new_palace', disabled=bool(selected_palace))

        items = []
        palace_id = None
        palace_name = selected_palace if selected_palace else new_palace

        # Load items if an existing palace is selected
        if palace_name:
            if selected_palace:
                palace_id = next(palace[0] for palace in palaces if palace[1] == selected_palace)
                items = db.get_palace_items(palace_id)

            items = st_tags(
                label='Memory palace items',
                text='Press enter to add more items',
                value=items,
                maxtags=10,
                key='exist_items' if selected_palace else 'new_items'
            )

        # Category selection or creation
        categories = db.get_categories()
        category_options = [""] + [category[1] for category in categories]
        selected_category = st.selectbox('Select Category', category_options, key='select_category')
        new_category = st.text_input('Or, add a new category', key='new_category', disabled=bool(selected_category))
        category = selected_category if selected_category else new_category

        topic = st.text_area('Enter the topic to learn about', max_chars=100, key='topic')

        # Generate Associations button disabled if conditions are not met
        generate_button_disabled = not palace_name or len(items) < 5 or not category or not topic

        if st.button("Generate Associations", key='generate', disabled=generate_button_disabled):
            st.success("Making Associations......")
            bullet_points = get_topic_info(topic, llm)
            imagery_list = [get_memorable_imagery(item, point, llm) for item, point in zip(items, bullet_points)]

            # Display the associations
            st.markdown(f"**Memory Palace: {palace_name}**")
            st.markdown(f"**Topic: {topic}**")
            st.markdown("---")
            content = ""
            for item, point, imagery in zip(items, bullet_points, imagery_list):
                st.markdown(f"**{item}**:\n {point} \n\n(Memorable Imagery: {imagery})")
                content += f"{item}: {point} (Imagery: {imagery})\n"

            # Save to database
            if not selected_palace:  # Only save if it's a new palace
                palace_id = db.add_palace(palace_name)
                db.add_items(palace_id, items)

            if not selected_category:
                category_id = db.add_category(category)
            else:
                category_id = next(cat[0] for cat in categories if cat[1] == selected_category)

            association_id = db.save_association(topic, category_id, palace_id, content)

            if association_id:
                st.success(f"Associations saved successfully.")

    with tab2:
        st.header("View Associations")

        categories = db.get_categories()
        if not categories:
            st.write("No categories found.")
        else:
            selected_category = st.selectbox("Select a Category", [cat[1] for cat in categories])

            if selected_category:
                category_id = next(cat[0] for cat in categories if cat[1] == selected_category)
                associations = db.get_associations(category_id)

                if not associations:
                    st.write("No association files found in this category.")
                else:
                    selected_association = st.selectbox("Select an Association", [assoc[1] for assoc in associations])

                    if selected_association:
                        association = next(assoc for assoc in associations if assoc[1] == selected_association)
                        topic, palace_id, content = association[1], association[2], association[3]

                        palace_name = next(palace[1] for palace in db.get_palaces() if palace[0] == palace_id)

                        st.markdown(f"### Topic: {topic}")
                        st.markdown(f"**Memory Palace: {palace_name}**")
                        st.write("")

                        for line in content.strip().split('\n'):
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

    with tab3:
        st.header("Manage Palaces")

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

        # Save items to database when button is clicked
        if st.button("Save Palace Items"):
            if palace_name and palace_items:
                palace_id = db.add_palace(palace_name)
                if palace_id:
                    db.add_items(palace_id, palace_items)
                    st.success(f"Palace '{palace_name}' and items saved successfully!")
                else:
                    st.error(f"Palace '{palace_name}' already exists. Please choose a different name.")
            else:
                st.error("Please enter both a palace name and items.")

        # Display the current palace data
        st.subheader("Current Palace Data")
        palaces = db.get_palaces()
        for palace in palaces:
            st.write(f"Palace: {palace[1]}")
            items = db.get_palace_items(palace[0])
            st.write(f"Items: {', '.join(items)}")
            st.write("---")

    with tab4:
        st.header("Save or Load Your Data")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Save Data")
            st.write("Click below to download your current data:")
            save_data()

        with col2:
            st.subheader("Load Data")
            st.write("Upload a previously saved JSON file:")
            load_data()
if __name__ == "__main__":
    main()