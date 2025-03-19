import os
import openai
import streamlit as st
import autogen
from autogen import AssistantAgent, UserProxyAgent

# Set your OpenAI API key
openai.api_key = "YourOpenAIAPIKey"

# Disable Docker globally
os.environ["AUTOGEN_USE_DOCKER"] = "False"

# Define the LLM configuration
llm_config = {"model": "gpt-3.5-turbo", "api_key": openai.api_key}

# Disable Docker in the agents by setting use_docker to False
code_execution_config = {"use_docker": False}

# Create the AssistantAgents for documentation and unit test generation
documentation_assistant = AssistantAgent(
    name="documentation_agent", 
    llm_config={"config_list": [llm_config]}, 
    code_execution_config=code_execution_config
)
testcode_assistant = AssistantAgent(
    name="testcode_agent", 
    llm_config={"config_list": [llm_config]}, 
    code_execution_config=code_execution_config
)

# Create a UserProxyAgent for handling user inputs
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
)

# Streamlit App Title
st.title("AI Code Documentation and Unit Test Generator")

# Step 1: File Upload
st.subheader("Upload your code file(s)")
uploaded_files = st.file_uploader("Choose code files", type=['py', 'java', 'cs'], accept_multiple_files=True)

# Function to load the content of uploaded files
def load_file_content(uploaded_files):
    file_contents = {}
    for uploaded_file in uploaded_files:
        content = uploaded_file.read().decode("utf-8").strip()
        if content:
            file_contents[uploaded_file.name] = content
        else:
            st.write(f"Uploaded file {uploaded_file.name} is empty or unreadable.")
    return file_contents

# Function to generate documentation for all files at once using AutoGen
def ai_agent_1_generate_code_documentation(file_contents):
    documentation = {}
    for file_name, code_content in file_contents.items():
        st.write(f"Generating documentation for file: {file_name}")
        st.code(code_content)  # Display code content to verify

        # Original prompt for documentation generation
        user_proxy.initiate_chat(
            documentation_assistant, 
            message=(
                f"I want to understand specifically what the uploaded code does. "
                f"Please avoid explaining the purpose and benefits. Simply describe the functionality and actions of each part of the code.\n\n{code_content}"
            )
        )
        generated_doc = documentation_assistant.last_message().get('content', 'No documentation generated')
        documentation[file_name] = generated_doc
    return documentation

# Function to generate unit tests for all files at once using AutoGen
def ai_agent_2_generate_unit_tests(documentation):
    unit_tests = {}
    for file_name, doc_content in documentation.items():
        st.write(f"Generating unit tests for file: {file_name}")
        st.code(doc_content)  # Display documentation content to verify
 # Determine the file extension to specify the language
        file_extension = file_name.split('.')[-1]
        language = "Python"  # Default to Python
        if file_extension == 'java':
            language = "Java"
        elif file_extension == 'cs':
            language = "C#"
        # Original prompt for unit test generation
        user_proxy.initiate_chat(
            testcode_assistant, 
            message=(
                f"Please generate a complete set of unit test cases in {language} for the provided code. "
                f"Each test should cover individual methods and key functionality, including edge cases "
                f"and typical use cases. For each function, include tests that verify correct outputs, "
                f"handle invalid inputs, and confirm expected behavior. Structure the tests clearly, "
                f"using assertions to validate outputs, and ensure the tests are runnable. Avoid summarizing the code; focus on creating tests that cover all possible scenarios to ensure robust functionality."
            )
        )
        generated_tests = testcode_assistant.last_message().get('content', 'No unit tests generated')
        unit_tests[file_name] = generated_tests
    return unit_tests

# Step 2: Display buttons and results after files are uploaded
if uploaded_files:
    file_contents = load_file_content(uploaded_files)

    # Button for generating documentation for all uploaded files
    if st.button("Generate Code Documentation"):
        documentation = ai_agent_1_generate_code_documentation(file_contents)

        # Display generated documentation for each file
        st.subheader("Generated Documentation")
        for file, doc in documentation.items():
            st.markdown(f"**{file}**")
            st.code(doc)

    # Button for generating unit tests for all uploaded files
    if st.button("Generate Unit Tests"):
        # Ensure documentation is available before generating tests
        documentation = ai_agent_1_generate_code_documentation(file_contents)  # Generating documentation before tests
        unit_tests = ai_agent_2_generate_unit_tests(documentation)

        # Display generated unit test cases for each file
        st.subheader("Generated Unit Test Cases")
        for file, tests in unit_tests.items():
            st.markdown(f"**{file}**")
            st.code(tests)
