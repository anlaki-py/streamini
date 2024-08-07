import time
import os
import joblib
import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import random
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()
GOOGLE_API_KEY = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

new_chat_id = f'{time.time()}'
MODEL_ROLE = 'ai'
AI_AVATAR_ICON = '✨'

# Create a data/ folder if it doesn't already exist
os.makedirs('data/', exist_ok=True)

# Load past chats (if available)
past_chats = {}
if os.path.exists('data/past_chats_list'):
    past_chats = joblib.load('data/past_chats_list')

# --- YouTube Bot Configuration ---
video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Example: Rick Astley - Never Gonna Give You Up
views = 1000  # Number of views you want
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
]
proxy_list = [
    "192.168.1.1:8080",  # Replace with actual proxies
]

# --- Streamlit UI ---
st.set_page_config(layout="wide", page_title="Aki Gemini AI Chatbot", page_icon=":sparkles:")
st.header("Gemini :sparkles:")

# Initialize session state
if 'chat' not in st.session_state:
    st.session_state.chat = []
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'chat_id' not in st.session_state:
    st.session_state.chat_id = None
if 'system_prompt' not in st.session_state:
    st.session_state.system_prompt = "You are a helpful assistant."
if 'temperature' not in st.session_state:
    st.session_state.temperature = 1.0
if 'top_p' not in st.session_state:
    st.session_state.top_p = 0.95
if 'top_k' not in st.session_state:
    st.session_state.top_k = 64
if 'max_output_tokens' not in st.session_state:
    st.session_state.max_output_tokens = 8192

# Sidebar for past chats
with st.sidebar:
    st.write('# Past Chats')
    if st.session_state.chat_id is None:
        st.session_state.chat_id = st.selectbox(
            label='Pick a past chat',
            options=[new_chat_id] + list(past_chats.keys()),
            format_func=lambda x: past_chats.get(x, 'New Chat'),
            placeholder='_',
        )
    else:
        st.session_state.chat_id = st.selectbox(
            label='Pick a past chat',
            options=[new_chat_id, st.session_state.chat_id] + list(past_chats.keys()),
            index=1,
            format_func=lambda x: past_chats.get(x, 'New Chat' if x != st.session_state.chat_id else st.session_state.chat_title),
            placeholder='_',
        )
    st.session_state.chat_title = f'ChatSession-{st.session_state.chat_id}'

    models = [
        "gemini-1.5-pro",
        "gemini-1.0-pro",
        "gemini-1.5-pro-exp-0801",
        "gemini-1.5-flash",
    ]
    selected_model = st.selectbox("Select the model:", models)

    new_api_key = st.text_input("Enter new API key (optional):", value="", type="password")
    if new_api_key:
        GOOGLE_API_KEY = new_api_key
        genai.configure(api_key=GOOGLE_API_KEY)

    system_prompts_dir = "system_prompts"
    os.makedirs(system_prompts_dir, exist_ok=True)

    default_system_prompt = "You are a helpful assistant."
    system_prompt = st.text_area("Edit system prompt:", height=100, value=st.session_state.system_prompt)

    save_system_prompt_name = st.text_input("Save system prompt as:")
    if st.button("Save system prompt"):
        if save_system_prompt_name:
            filename = os.path.join(system_prompts_dir, f"{save_system_prompt_name}.txt")
            with open(filename, "w") as f:
                f.write(system_prompt)
            st.success(f"System prompt saved as {filename}")
        else:
            st.error("Please enter a name for the system prompt")

    saved_system_prompts = [f"{filename.split('.')[0]}" for filename in os.listdir(system_prompts_dir) if filename.endswith(".txt")]
    selected_system_prompt = st.selectbox("Select saved system prompt:", ["None"] + saved_system_prompts)

    if selected_system_prompt != "None":
        with open(os.path.join(system_prompts_dir, f"{selected_system_prompt}.txt"), "r") as f:
            st.session_state.system_prompt = f.read()
    else:
        st.session_state.system_prompt = system_prompt

    temperature = st.slider("Temperature:", min_value=0.0, max_value=2.0, value=st.session_state.temperature, step=0.1)
    top_p = st.slider("Top P:", min_value=0.0, max_value=2.0, value=st.session_state.top_p, step=0.05)
    top_k = st.slider("Top K:", min_value=0, max_value=100, value=st.session_state.top_k, step=1)
    max_output_tokens = st.slider("Max Output Tokens:", min_value=0, max_value=20000, value=st.session_state.max_output_tokens, step=1)

    if st.button("Apply Changes"):
        # Apply changes to the system prompt and other settings
        st.session_state.temperature = temperature
        st.session_state.top_p = top_p
        st.session_state.top_k = top_k
        st.session_state.max_output_tokens = max_output_tokens
        st.success("Changes applied!")

    if st.button("Save Conversation"):
        if st.session_state.messages:
            if not os.path.exists("history"):
                os.makedirs("history")
            filename = f"history/output-{len(st.session_state.messages)}-{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(st.session_state.messages, f, indent=4)
            st.success(f"Conversation saved as {filename}")
        else:
            st.error("No messages to save!")

    conversation_files = [f for f in os.listdir("history") if f.endswith(".json")]
    selected_conversation = st.selectbox("Load Conversation:", conversation_files)

    if st.button("Load Conversation"):
        if selected_conversation:
            with open(os.path.join("history", selected_conversation), "r") as f:
                st.session_state.messages = json.load(f)
            st.experimental_rerun()
        else:
            st.error("Please select a conversation to load!")

    if st.button("Clean chat"):
        st.session_state.messages = []

# --- Main Chat Area ---
st.write('# Chat with Gemini')

try:
    st.session_state.messages = joblib.load(
        f'data/{st.session_state.chat_id}-st_messages'
    )
    st.session_state.gemini_history = joblib.load(
        f'data/{st.session_state.chat_id}-gemini_messages'
    )
    print('old cache')
except:
    st.session_state.messages = []
    st.session_state.gemini_history = []
    print('new_cache made')

# Create and configure the model based on the selected model
def create_model(model_name):
    generation_config = {
        "temperature": st.session_state.temperature,
        "top_p": st.session_state.top_p,
        "top_k": st.session_state.top_k,
        "max_output_tokens": st.session_state.max_output_tokens,
    }

    return genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config,
        safety_settings={
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
        }
    )

# Initialize the chat session if not already in session state or if the model is changed
if "chat_session" not in st.session_state or st.session_state.get("current_model") != selected_model:
    model_instance = create_model(selected_model)
    st.session_state.chat_session = model_instance.start_chat(history=[])
    st.session_state.current_model = selected_model

    # Set the system prompt after starting the chat session
    st.session_state.chat_session.system_prompt = st.session_state.system_prompt

# Display chat messages from history on app rerun
for i, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(message["content"])
    else:
        container = st.container()
        with container:
            with st.chat_message("assistant"):
                st.markdown(message["content"])
            if st.button("Edit", key=f"edit_{i}"):
                new_content = st.text_area("Edit AI response:", value=message["content"], key=f"edit_area_{i}")
                if st.button("Save changes", key=f"save_{i}"):
                    st.session_state.messages[i]["content"] = new_content
                    st.session_state.edited_message_index = i
                    st.experimental_rerun()

# React to user input
if prompt := st.chat_input('Your message here...'):
    if st.session_state.chat_id not in past_chats.keys():
        past_chats[st.session_state.chat_id] = st.session_state.chat_title
        joblib.dump(past_chats, 'data/past_chats_list')
    with st.chat_message('user'):
        st.markdown(prompt)
    st.session_state.messages.append(
        dict(
            role='user',
            content=prompt,
        )
    )
    try:
        if "edited_message_index" in st.session_state:
            edited_message_index = st.session_state.edited_message_index
            del st.session_state.edited_message_index
            response = st.session_state.chat_session.send_message(prompt, history=[st.session_state.messages[edited_message_index]["content"]])
        else:
            response = st.session_state.chat_session.send_message(prompt)

        with st.chat_message(
            name=MODEL_ROLE,
            avatar=AI_AVATAR_ICON,
        ):
            message_placeholder = st.empty()
            full_response = ''
            assistant_response = response
            for chunk in response.text.split(' '):
                full_response += chunk + ' '
                time.sleep(0.05)
                message_placeholder.write(full_response + '▌')
            message_placeholder.write(full_response)

        st.session_state.messages.append(
            dict(
                role=MODEL_ROLE,
                content=response.text,
                avatar=AI_AVATAR_ICON,
            )
        )
        st.session_state.gemini_history = st.session_state.chat_session.history
        joblib.dump(
            st.session_state.messages,
            f'data/{st.session_state.chat_id}-st_messages',
        )
        joblib.dump(
            st.session_state.gemini_history,
            f'data/{st.session_state.chat_id}-gemini_messages',
        )
    except Exception as e:
        st.error(f"An error occurred: {e}")

# --- YouTube Bot Function ---
def run_youtube_bot():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # Run Chrome in headless mode (no GUI)
    options.add_argument(f"user-agent={random.choice(user_agents)}")
    # If using proxies, uncomment the following lines and configure them
    # options.add_argument("--proxy-server=%s" % random.choice(proxy_list))

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    for i in range(views):
        try:
            driver.get(video_url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "movie_player")))
            watch_time = random.randint(30, 60)
            time.sleep(watch_time)
            print(f"View {i+1} completed (watched for {watch_time} seconds).")
        except TimeoutException:
            print(f"Timeout for view {i+1}. Skipping...")

    driver.quit()
    print("View botting complete!")

# --- YouTube Bot Button ---
if st.button("Run YouTube Bot"):
    run_youtube_bot()