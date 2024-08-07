import os
import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime
import time

# Set the API key from the environmental variable
api_key = os.getenv("GEMINI_API_KEY")

if api_key is None:
    raise ValueError("GEMINI_API_KEY is not set. Please set the environment variable.")

# Available models
models = [
    "gemini-1.5-pro",
    "gemini-1.0-pro",
    "gemini-1.5-pro-exp-0801",
    "gemini-1.5-flash",
]

# Streamlit UI
st.set_page_config(layout="wide", page_title="Aki Gemini AI Chatbot", page_icon=":sparkles:")
st.header("Gemini :sparkles:")

# Model selection in sidebar
selected_model = st.sidebar.selectbox("Select the model:", models)

# API key input in sidebar (for testing purposes, but not recommended for production)
new_api_key = st.sidebar.text_input("Enter new API key (optional):", value="", type="password")
if new_api_key:
    api_key = new_api_key

genai.configure(api_key=api_key)

# System prompt editing and saving
system_prompts_dir = "system_prompts"
if not os.path.exists(system_prompts_dir):
    os.makedirs(system_prompts_dir)

# Default system prompt
default_system_prompt = "You are a helpful assistant."
system_prompt = st.sidebar.text_area("Edit system prompt:", height=100, value=default_system_prompt)

save_system_prompt_name = st.sidebar.text_input("Save system prompt as:")
if st.sidebar.button("Save system prompt"):
    if save_system_prompt_name:
        filename = os.path.join(system_prompts_dir, f"{save_system_prompt_name}.txt")
        with open(filename, "w") as f:
            f.write(system_prompt)
        st.sidebar.success(f"System prompt saved as {filename}")
    else:
        st.sidebar.error("Please enter a name for the system prompt")

# Load saved system prompts
saved_system_prompts = [f"{filename.split('.')[0]}" for filename in os.listdir(system_prompts_dir) if filename.endswith(".txt")]
selected_system_prompt = st.sidebar.selectbox("Select saved system prompt:", ["None"] + saved_system_prompts)

if selected_system_prompt != "None":
    with open(os.path.join(system_prompts_dir, f"{selected_system_prompt}.txt"), "r") as f:
        system_prompt = f.read()

# --- Sliders for Generation Parameters ---
temperature = st.sidebar.slider("Temperature:", min_value=0.0, max_value=2.0, value=1.0, step=0.1)
top_p = st.sidebar.slider("Top P:", min_value=0.0, max_value=2.0, value=0.95, step=0.05)
top_k = st.sidebar.slider("Top K:", min_value=0, max_value=100, value=64, step=1)
max_output_tokens = st.sidebar.slider("Max Output Tokens:", min_value=0, max_value=20000, value=8192, step=1)

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for i, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        st.chat_message("user").markdown(message["content"])
    else:
        container = st.container()
        with container:
            st.chat_message("assistant").markdown(message["content"])
            if st.button("Edit", key=f"edit_{i}"):
                new_content = st.text_area("Edit AI response:", value=message["content"], key=f"edit_area_{i}")
                if st.button("Save changes", key=f"save_{i}"):
                    st.session_state.messages[i]["content"] = new_content
                    st.session_state.edited_message_index = i
                    st.experimental_rerun()

# Save conversation button in sidebar
if st.sidebar.button("Save Conversation"):
    if st.session_state.messages:
        if not os.path.exists("history"):
            os.makedirs("history")
        filename = f"history/output-{len(st.session_state.messages)}-{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(st.session_state.messages, f, indent=4)
        st.sidebar.success(f"Conversation saved as {filename}")
    else:
        st.sidebar.error("No messages to save!")

# Load conversation button in sidebar
conversation_files = [f for f in os.listdir("history") if f.endswith(".json")]
selected_conversation = st.sidebar.selectbox("Load Conversation:", conversation_files)

if st.sidebar.button("Load Conversation"):
    if selected_conversation:
        with open(os.path.join("history", selected_conversation), "r") as f:
            st.session_state.messages = json.load(f)
        st.experimental_rerun()
    else:
        st.sidebar.error("Please select a conversation to load!")

# Clean chat button in sidebar
if st.sidebar.button("Clean chat"):
    st.session_state.messages = []

# Create and configure the model based on the selected model
def create_model(model_name):
    generation_config = {
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "max_output_tokens": max_output_tokens,
        "response_mime_type": "text/plain",
    }

    # Define models that should use the system instruction
    models_with_system_instruction = [
        "gemini-1.5-pro",
        "gemini-1.5-pro-exp-0801",
        "gemini-1.5-flash",
    ]

    system_instruction = None
    if model_name in models_with_system_instruction:
        system_instruction = system_prompt

    return genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config,
        safety_settings={
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
        },
        system_instruction=system_instruction,
    )

# Initialize the chat session if not already in session state or if the model is changed
if "chat_session" not in st.session_state or st.session_state.get("current_model") != selected_model:
    st.session_state.chat_session = create_model(selected_model).start_chat(history=[])
    st.session_state.current_model = selected_model

# Get user input
user_message = st.chat_input("Type your message here...")

# Process user input
if user_message:
    try:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_message})

        # Display the user's message immediately
        st.chat_message("user").markdown(user_message)

        # Check if the previous message was edited
        if "edited_message_index" in st.session_state:
            edited_message_index = st.session_state.edited_message_index
            del st.session_state.edited_message_index
            # Use the edited message as the context for the next response
            response = st.session_state.chat_session.send_message(user_message, history=[st.session_state.messages[edited_message_index]["content"]])
        else:
            response = st.session_state.chat_session.send_message(user_message)

        # Stream AI response
        with st.chat_message("assistant") as msg:
            full_response = ""
            # Assuming response.text is a generator or iterable
            for chunk in response.text.split(' '):  # Adjust this based on how your API returns the response
                full_response += chunk + ' '
                msg.markdown(full_response + "▌")  # Display the response incrementally
                time.sleep(0.05)  # Simulate typing delay

        # Add AI response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"An error occurred: {e}")