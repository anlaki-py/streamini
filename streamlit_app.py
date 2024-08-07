import os
import streamlit as st
import google.generativeai as genai
import json

# Set the API key from the environmental variable
api_key = os.getenv("GEMINI_API_KEY")

if api_key is None:
    raise ValueError("GEMINI_API_KEY is not set. Please set the environment variable.")

# Configure the Gemini API with the provided API key
genai.configure(api_key=api_key)

st.title("Gemini Chatbot Clone")
with st.expander("ℹ️ Disclaimer"):
    st.caption(
        """We appreciate your engagement! Please note that this demo allows for unlimited interactions.
        Thank you for trying out this application."""
    )

# Initialize session state variables
if "gemini_model" not in st.session_state:
    st.session_state["gemini_model"] = "gemini-1.5-pro"  # Default model

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate assistant response using Gemini API
    with st.chat_message("assistant"):
        try:
            # Create and configure the model based on the selected model
            generation_config = {
                "temperature": 1.0,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 2000,
            }

            # Create the model instance
            model_instance = genai.GenerativeModel(
                model_name=st.session_state["gemini_model"],
                generation_config=generation_config,
                safety_settings={
                    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                    "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                },
            )

            # Start chat and get the response
            response = model_instance.start_chat(history=st.session_state.messages)
            assistant_response = response.text

            # Add AI response to chat history
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})

            # Display the AI's response
            st.markdown(assistant_response)

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.session_state.messages.append(
                {"role": "assistant", "content": f"Sorry, I can't respond right now. Error: {e}"}
            )
            st.rerun()