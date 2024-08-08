# Streamini :sparkles:

Streamini is a conversational AI application built with Streamlit and the Google Gemini API. This app allows users to interact with different Gemini AI models, customize prompts, and manage conversation history effectively.

## Features

- **Model Selection:** Choose from different available models like `gemini-1.5-pro`, `gemini-1.0-pro`, `gemini-1.5-pro-exp-0801`, and `gemini-1.5-flash`.
- **System Prompt Customization:** Modify and save system prompts to guide the AI's behavior.
- **Conversation Management:** Save and load conversations for later use.
- **Response Customization:** Adjust AI response parameters such as temperature, top-p, top-k, and max output tokens.
- **Chat Editing:** ~~Edit the AI's responses directly in the chat interface.~~

## Installation

### Prerequisites

- Python 3.7+
- Streamlit
- Google Gemini API Key

### Clone the Repository

```bash
git clone https://github.com/anlaki-py/streamini.git
cd streamini
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Set Up Environment Variables

You need to set the `GEMINI_API_KEY` environment variable. This key can be obtained from Google Gemini API.

For Unix/Linux/MacOS:

```bash
export GEMINI_API_KEY=your_gemini_api_key
```

For Windows:

```bash
set GEMINI_API_KEY=your_gemini_api_key
```

Alternatively, you can directly input the API key in the Streamlit sidebar for testing purposes.

## Usage

Run the Streamlit app with the following command:

```bash
streamlit run streamlit_app.py
```

This will start the app locally and open it in your default web browser. You can interact with the chatbot, modify prompts, save/load conversations, and adjust AI response parameters from the sidebar.

## File Structure

```plaintext
streamini/
├── .devcontainer/       # Directory containing development container configuration
├── .streamlit/          # Streamlit configuration directory
├── history/             # Directory to save conversation history
├── system_prompts/      # Directory to save custom system prompts
├── README.md            # Readme file
├── local_app.py         # Local application script for testing
├── requirements.txt     # Python dependencies
└── streamlit_app.py     # Main application script
```

## Customization

### System Prompts

You can create and save custom system prompts via the Streamlit sidebar. Saved prompts are stored in the `system_prompts/` directory.

### Conversation History

Save the current conversation from the sidebar, and it will be stored in the `history/` directory. Load previously saved conversations as needed.
