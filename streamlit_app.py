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
        """We appreciate your engagement! Please note, this demo is designed to
        process a maximum of 10 interactions and may be unavailable if too many
        people use the service concurrently. Thank you for your understanding.
        """
    )

# Initialize session state variables
if "gemini_model" not in st.session_state:
    st.session_state["gemini_model"] = "gemini-1.5-pro"  # Default model

if "messages" not in st.session_state:
    st.session_state.messages = []

if "max_messages" not in st.session_state:
    # Counting both user and assistant messages, so 10 rounds of conversation
    st.session_state.max_messages = 20

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Check if the maximum message limit has been reached
if len(st.session_state.messages) >= st.session_state.max_messages:
    st.info(
        """Notice: The maximum message limit for this demo version has been reached. We value your interest!
        We encourage you to experience further interactions by building your own application with instructions
        from Streamlit's [Build a basic LLM chat app](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)
        tutorial. Thank you for your understanding."""
    )

else:
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
                    {"role": "assistant", "content": "Sorry, I can't respond right now. Please try again later."}
                )
                st.rerun()