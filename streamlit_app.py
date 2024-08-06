import os
import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime

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
st.set_page_config(layout="wide", page_title="Gemini AI Chatbot")

# Model selection in sidebar
selected_model = st.sidebar.selectbox("Select the model:", models)

# API key input in sidebar
new_api_key = st.sidebar.text_input("Enter new API key (optional):", value="", type="password")

if new_api_key:
    api_key = new_api_key

genai.configure(api_key=api_key)

# System prompt editing and saving
system_prompts_dir = "system_prompts"
if not os.path.exists(system_prompts_dir):
    os.makedirs(system_prompts_dir)

# Default system prompt
system_prompt = "You are a helpful assistant."

# Load saved system prompts
saved_system_prompts = [f"{filename.split('.')[0]}" for filename in os.listdir(system_prompts_dir) if filename.endswith(".txt")]
selected_system_prompt = st.sidebar.selectbox("Select saved system prompt:", saved_system_prompts)

if selected_system_prompt:
    with open(os.path.join(system_prompts_dir, f"{selected_system_prompt}.txt"), "r") as f:
        system_prompt = f.read()

# Add sliders for generation configuration
st.sidebar.header("Adjust Model Parameters")
temperature = st.sidebar.slider("Temperature", 0.0, 2.0, 1.0, 0.1)
top_p = st.sidebar.slider("Top-p (Nucleus Sampling)", 0.0, 1.0, 0.95, 0.01)
top_k = st.sidebar.slider("Top-k", 0, 100, 64, 1)
max_output_tokens = st.sidebar.slider("Max Output Tokens", 1, 8192, 8192, 1)

# Apply button for system prompt, model, and sliders
if st.sidebar.button("Apply Configuration"):
    st.session_state.applied_model = selected_model
    st.session_state.applied_system_prompt = system_prompt
    st.session_state.applied_temperature = temperature
    st.session_state.applied_top_p = top_p
    st.session_state.applied_top_k = top_k
    st.session_state.applied_max_output_tokens = max_output_tokens

    # Reinitialize the chat session with the new configuration
    st.session_state.chat_session = create_model(
        st.session_state.applied_model,
        st.session_state.applied_system_prompt,
        st.session_state.applied_temperature,
        st.session_state.applied_top_p,
        st.session_state.applied_top_k,
        st.session_state.applied_max_output_tokens
    ).start_chat(history=[])

    st.session_state.messages = []  # Clear the chat history on new configuration
    st.experimental_rerun()  # Rerun to update the UI with the new session

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

# Clean chat button in sidebar
if st.sidebar.button("Clean chat"):
    st.session_state.messages = []

# Create and configure the model based on the selected model
def create_model(model_name, system_prompt, temperature, top_p, top_k, max_output_tokens):
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

# Initialize the chat session with the applied configuration
if "chat_session" not in st.session_state:
    st.session_state.chat_session = create_model()
        selected_model,
        system_prompt,
        temperature,
        top_p,
        top_k,
        max_output_tokens
    ).start_chat(history=[])
    st.session_state.applied_model = selected_model
    st.session_state.applied_system_prompt = system_prompt
    st.session_state.applied_temperature = temperature
    st.session_state.applied_top_p = top_p
    st.session_state.applied_top_k = top_k
    st.session_state.applied_max_output_tokens = max_output_tokens

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

        # Add AI response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response.text})

        # Display the AI's response
        st.chat_message("assistant").markdown(response.text)
    except Exception as e:
        st.error(f"An error occurred: {e}")