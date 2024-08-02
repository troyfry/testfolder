import openai
import streamlit as st
from langchain import PromptTemplate, LLMChain, OpenAI

# Replace with your OpenAI API key
#from secretkeys import openapi_key
import os
from pages import usertopic


hide_default_format = """
       <style>
       #MainMenu {visibility: hidden; }
       footer {visibility: hidden;}
       </style>
       """

#openai_api_key = st.secrets["OPENAI_API_KEY"]
openai_api_key = st.sidebar.text_input('OpenAI API Key')

llm = OpenAI(temperature=0.6, openai_api_key = openai_api_key)
 # Initialize empty lists for items before and after the dash

st.markdown(hide_default_format, unsafe_allow_html=True)

st.title("Interesting Learning")

number_choice = st.number_input(r"$\textsf{\Large Enter number of Main points to retreive:}$", value=5, format="%d", min_value=5, max_value=10)
number_choice = int(number_choice) 
topic = st.text_input(r"$\textsf{\Large Enter the topic you want to learn about:}$", max_chars=50)
    

# Define the prompt templates
topic_prompt = PromptTemplate(
    input_variables=["topic"],
    template=f"Provide {number_choice} important bullet points about {topic}:"
)


# Define the chains
topic_chain = LLMChain(llm=llm, prompt=topic_prompt)




def get_topic_info(topic):
    response = topic_chain.run({"topic": topic})
    points = response.strip().split('\n')
    return [point.strip('- ') for point in points if point.strip()]



def get_memorable_imagery(item, info):
    prompt = f"""
    Using the memory palace method, create a succint, vivid and memorable mental imagery to associate the phrase '{info}' with the item '{item}':
    Make the associations interesting, obvious and brief. 
    """
    response = llm.predict(prompt)
    return response

def main():

    with st.expander("SEE PALACES"):
        on = st.toggle("show palaces")

        with open("my_palaces.txt", "r") as file:
            palace_contents = file.read()

            st.download_button("Download my_palaces.txt", palace_contents, file_name="my_palaces.txt")
        if on:
        #  if st.button("Load Palaces"):
            usertopic.open_palace_file()  

        


    palace_name = st.text_input(r"$\textsf{\Large Enter a name for your memory palace:}$", max_chars=15)

    full_palace_name = f"{topic} - {palace_name}"

    items = [st.text_input(f"Enter item {i+1} for your memory palace:",  max_chars=16) for i in range(number_choice)]




    if st.button("Associate"):
        if not openai_api_key.startswith('sk-'):
            st.warning('Please enter your OpenAI key!')
       

        filename = f"{topic}.txt"
        

        st.write("\nAssociating...")
        bullet_points = get_topic_info(topic)

        st.write("\nGenerating memorable mental imagery with your palace items...")
        imagery_list = [get_memorable_imagery(items[i], bullet_points[i]) for i in range(number_choice)]
        
        st.write(f"\nInformation saved to {filename}")


        st.write(f"\nHere are the important points associated with {topic}:")

        st.markdown(f"**Memory Palace: {full_palace_name}**")
        st.markdown("---")  # Horizontal line

        for i in range(number_choice):
            st.markdown(f"**{items[i]}**: {bullet_points[i] if i < len(bullet_points) else 'N/A'} (Memorable Imagery: {imagery_list[i] if i < len(imagery_list) else 'N/A'})")

        # Save the information to a text file
        
        with open(filename, "w") as file:
            file.write(f"Topic: {topic}: Palace: {full_palace_name}\n")
            for i in range(number_choice):
                file.write(f"\n{items[i]}: {bullet_points[i] if i < len(bullet_points) else 'N/A'} (Imagery: {imagery_list[i] if i < len(imagery_list) else 'N/A'})\n")
       # st.write(f"\nInformation saved to {filename}")

     
        with open(filename, "r") as file:
            text_contents = file.read()

        st.download_button("Download text", text_contents, file_name=filename)
        
        pal_line = f"{palace_name} - {', '.join(items)}"
        print(palace_name)
        usertopic.add_to_palace_file(pal_line)
        
        

            

if __name__ == "__main__":
    main()
