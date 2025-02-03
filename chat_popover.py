import streamlit as st
import requests
import json

# API Configuration
#API_URL = "http://localhost:3000/api/v1/prediction/40374a74-e1c8-47a4-981a-e8fc3695d9fe"
API_URL = "https://flowiseai-gtn7.onrender.com/api/v1/prediction/fd01db09-c0ff-4211-9b79-5d7d964e01df"

# Page Configuration
st.set_page_config(
    page_title="Chat Popover",
    page_icon="💭",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS with styled link
st.markdown("""
    <style>
    /* Link styling */
    .chatbot-link {
        display: inline-block;
        color: #29537D;
        text-decoration: none;
        font-family: 'Open Sans', sans-serif;
        font-weight: 600;
        padding: 8px 15px;
        margin: 10px 0;
        border-radius: 5px;
        transition: all 0.3s ease;
        text-align: center;
        background-color: #f0f7ff;
    }
    
    .chatbot-link:hover {
        background-color: #dbedf5;
        transform: translateY(-1px);
    }
    
    /* Center the link container */
    .link-container {
        display: flex;
        justify-content: center;
        margin-bottom: 15px;
        border-bottom: 1px solid #dbedf5;
        padding-bottom: 15px;
    }
    
    /* Style the go-to-full-chat text */
    .go-to-full-chat {
        color: #666;
        font-size: 0.9em;
        text-align: center;
        margin-top: 5px;
        font-family: 'Open Sans', sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

def response_generator(question):
    try:
        payload = {"question": question}
        response = requests.post(
            API_URL, 
            json=payload, 
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"text": f"I apologize, but I'm having trouble connecting. Error: {str(e)}"}

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
        welcome_message = {
            "role": "assistant",
            "content": "👋 Hello! How can I help you today?"
        }
        st.session_state.messages.append(welcome_message)

def chat_interface():
    # Styled link to full chat
    st.markdown("""
        <div class="link-container">
            <div>
                <a href="http://localhost:8501/" class="chatbot-link" target="_blank">
                    Mental Health ChatBot
                </a>
                <div class="go-to-full-chat">Go to full chat window ↗️</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = response_generator(prompt)
                    if 'text' in response:
                        st.markdown(response['text'])
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": response['text']
                        })
                    else:
                        st.error("Unexpected response. Please try again.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

def main():
    initialize_session_state()
    chat_interface()

if __name__ == "__main__":
    main()