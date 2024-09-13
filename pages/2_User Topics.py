import streamlit as st
from langchain_community.llms import OpenAI
import os

st.title("Study with the ease of the Memory Palace")
# Set OpenAI API key from sidebar input
openai_api_key = st.text_input('OpenAI API Key', disabled=True)

llm = OpenAI(temperature=0.6, openai_api_key=openai_api_key)



def get_topic_info(subtopics_list, palace_items):
    associations = []
    for i, subtopic in enumerate(subtopics_list):
        if i < len(palace_items):
            association_text = f"{subtopic} associated with Palace Item {i + 1}"
        else:
            association_text = f"{subtopic} (No associated Palace Item)"
        associations.append(association_text)
    return associations

def get_memorable_imagery(palaceItems, subtopics):
    prompt = f"""Using the memory palace method, use the meaning of the text "{subtopics}" to create a one-sentence, vivid, and memorable mental imagery 
    to associate the phrase '{subtopics}' with the palace items '{palaceItems}':
    Make the associations obvious, interesting, and brief.
    """
    response = llm.invoke(prompt)
    return response

def open_palace_file():
    try:
        with open("../storedApps/my_palaces.txt", "r") as file:
            contents = file.read()
            lines = contents.strip().split("\n")
            for item in lines:
                st.write(item)
    except FileNotFoundError:
        st.error("The file 'my_palaces.txt' does not exist.")
    except Exception as e:
        st.error(f"An error occurred: {e}")



def add_to_palace_file(pal_line):
    
    try:

           # file.write(f"{pal_line}\n")  # Append the new line to the file
           # st.write("File my_palaces.txt updated")
        
        with open("../storedApps/my_palaces.txt", "a") as file:  # Use 'a' mode to append content
           
            file.write(f"{pal_line}\n")  # Append the new line to the file
            st.write("File my_palaces.txt updated")
    except FileNotFoundError:
        st.error("The file 'my_palaces.txt' does not exist.")
    except Exception as e:
        st.error(f"An error occurred: {e}")

def save_to_palace_file(new_line):
    try:
        with open("../storedApps/my_palaces.txt", "a") as file:  # Use 'a' mode to append content
            file.write(f"{new_line} |\n")  # Append the new line to the file
    except FileNotFoundError:
        st.error("The file 'my_palaces.txt' does not exist.")
    except Exception as e:
        st.error(f"An error occurred: {e}")

palace_data = {}
palace_items = []

def main():

    instruct = """
    Enter your subject of choice. List the things you want to learn separated by a 'line return'. 
    Enter palace items per 'thing to learn'. AI will respond with association between each 'thing to learn' and palace item

    hint: For your palace and items choose a place that you know well
    """
    with st.expander("Instructions"):
        st.write(instruct)
        


    
    st.write(openai_api_key[:6])
    col1, col2 = st.columns([3, 4])

    with col1:
        with st.expander("Topic you want to learn"):
            topic_input = st.text_input("Enter topic - i.e. World War 1")
            subtopics_input = st.text_area("Subtopic list? (line return after each entry):", max_chars=500)
            subtopics_list = [sub.strip() for sub in subtopics_input.splitlines()]
            
            palace_name = st.text_input("Enter a name for your memory palace (i.e mybedroom):", max_chars=15)
            
            palace_items = []
            for i, subtopic in enumerate(subtopics_list):
                palace_item = st.text_input(f"Palace item for '{subtopic}':", key=f"item_{i}")
                palace_items.append(palace_item)

            palace_data[palace_name] = palace_items
            full_palace_name = f"{palace_name}-{topic_input}"

        if st.button("Associate"):
            
            st.warning("\nAssociating...")
            bullet_points = get_topic_info(subtopics_list, palace_items)

            st.write("\nGenerating memorable mental imagery with your palace items...")
            imagery_list = [get_memorable_imagery(palace_items[i], bullet_points[i]) for i in range(len(subtopics_list))]

            st.markdown(f"**Memory Palace: {full_palace_name}**")
            st.markdown("---")

            for i in range(len(subtopics_list)):
                st.markdown(f"**{palace_items[i]}**: <span style='color:blue;'>{bullet_points[i] if i < len(bullet_points) else 'N/A'} (Memorable Imagery: {imagery_list[i] if i < len(imagery_list) else 'N/A'})</span>", unsafe_allow_html=True)

            filename = f"{topic_input}.txt"
            with open(filename, "w") as file:
                file.write(f"Palace: {full_palace_name}\nTopic: {topic_input}\nPalace items: {palace_items} \nSubtopics: {subtopics_list}:\n\n")
                for i in range(len(subtopics_list)):
                    file.write(f"\n{palace_items[i]}: {bullet_points[i] if i < len(bullet_points) else 'N/A'} (Imagery: {imagery_list[i] if i < len(imagery_list) else 'N/A'})\n")
          #  st.write(f"\nInformation saved to {filename}")

            with open(f"{filename}", "r") as file:
                response_contents = file.read()
                st.download_button("Download results", response_contents, file_name=f"{filename}")
                os.remove(filename)

    palace_file =  f"{palace_name}.txt" 
        
    pal_line = f"{palace_name} - {', '.join(palace_items)}"
    

    with open(palace_file, "w") as file:
        file.write(pal_line)

    with open(palace_file, "r") as file:
        text_contents = file.read()

    st.download_button("Download palace", text_contents, file_name=palace_file)
    os.remove(palace_file)

if __name__ == "__main__":
    main()
