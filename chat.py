import requests
import streamlit as st
import json
from datetime import datetime
from supabase import create_client
import binascii
import uuid

# API Configuration
API_URL = "https://flowiseai-gtn7.onrender.com/api/v1/prediction/fd01db09-c0ff-4211-9b79-5d7d964e01df"

# Page Configuration
st.set_page_config(
    page_title="Mental Health Chat",
    page_icon="🤗",
    layout="wide"
)

# Custom CSS for styling
st.markdown("""
    <style>
    .chat-thread {
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        background-color: #f0f2f6;
        cursor: pointer;
        border: 1px solid #e0e0e0;
    }
    .chat-thread:hover {
        background-color: #e0e2e6;
    }
    .selected-thread {
        background-color: #e0e2e6;
        border: 1px solid #c0c0c0;
    }
    </style>
""", unsafe_allow_html=True)

class ChatHistoryHandler:
    def __init__(self, supabase_url, supabase_key):
        self.supabase = create_client(supabase_url, supabase_key)

    def decode_hex_data(self, hex_str):
        try:
            if hex_str.startswith('\\x'):
                hex_str = hex_str[2:]
            bytes_data = binascii.unhexlify(hex_str)
            return bytes_data.decode('utf-8')
        except Exception as e:
            print(f"Error decoding hex data: {str(e)}")
            return None

    def decode_buffer_data(self, buffer_data):
        try:
            if buffer_data is None:
                return None
            if isinstance(buffer_data, dict):
                return buffer_data
            if isinstance(buffer_data, str) and buffer_data.startswith('\\x'):
                decoded_str = self.decode_hex_data(buffer_data)
                if decoded_str:
                    return json.loads(decoded_str)
            if isinstance(buffer_data, bytes):
                buffer_str = buffer_data.decode('utf-8')
            else:
                buffer_str = str(buffer_data)
            return json.loads(buffer_str)
        except Exception as e:
            print(f"Error in decode_buffer_data: {str(e)}")
            return None

    def extract_messages(self, data):
        messages = []
        try:
            if not data:
                return messages

            # Process messages from channel_values
            if 'channel_values' in data and 'messages' in data['channel_values']:
                # Get the last user message and the last assistant response
                last_user_msg = None
                last_assistant_msg = None
                
                for msg in data['channel_values']['messages']:
                    if isinstance(msg, dict) and 'kwargs' in msg:
                        content = msg['kwargs'].get('content')
                        if content and content.strip():
                            # Skip academic references and processing messages
                            if not content.startswith('reduce') and not any(x in content.lower() for x in 
                                ['journal', 'research', 'disabilities', 'doi', 'isbn']):
                                
                                msg_type = 'user' if 'HumanMessage' in str(msg) else 'assistant'
                                
                                # Update last message based on type
                                if msg_type == 'user':
                                    last_user_msg = {
                                        'role': 'user',
                                        'content': content
                                    }
                                elif msg_type == 'assistant':
                                    # Skip generic acknowledgments
                                    if not content.startswith("Understood") and \
                                       not "processing" in content.lower() and \
                                       len(content.split()) > 3:  # Skip very short responses
                                        last_assistant_msg = {
                                            'role': 'assistant',
                                            'content': content
                                        }

                # Add the last user message and corresponding assistant response
                if last_user_msg:
                    messages.append(last_user_msg)
                if last_assistant_msg:
                    messages.append(last_assistant_msg)

        except Exception as e:
            print(f"Error extracting messages: {str(e)}")
        
        return messages

    def get_chat_history(self):
        try:
            response = self.supabase.table('checkpoints').select('*').execute()
            print(f"Retrieved {len(response.data)} records")

            threads = {}
            for record in response.data:
                try:
                    thread_id = record.get('thread_id')
                    if not thread_id:
                        continue

                    checkpoint_data = self.decode_buffer_data(record.get('checkpoint'))
                    metadata_data = self.decode_buffer_data(record.get('metadata'))

                    messages = []
                    if checkpoint_data:
                        messages.extend(self.extract_messages(checkpoint_data))
                    if metadata_data:
                        messages.extend(self.extract_messages(metadata_data))

                    if messages:
                        if thread_id not in threads:
                            threads[thread_id] = []
                        threads[thread_id].extend(messages)

                except Exception as e:
                    print(f"Error processing record {thread_id}: {str(e)}")
                    continue

            return threads
        except Exception as e:
            print(f"Error retrieving chat history: {str(e)}")
            return {}

def initialize_session_state():
    if 'chat_handler' not in st.session_state:
        st.session_state.chat_handler = ChatHistoryHandler(
            supabase_url="https://njjwqayxblfovroxlwar.supabase.co",
            supabase_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5qandxYXl4Ymxmb3Zyb3hsd2FyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc4NTE1OTQsImV4cCI6MjA1MzQyNzU5NH0.1Ai2qd78ka70YhWSCeFnaXsK_7wpwPGs8beDfJsBT1E"
        )
    
    if 'current_thread_id' not in st.session_state:
        st.session_state.current_thread_id = None
    
    if 'chat_threads' not in st.session_state:
        st.session_state.chat_threads = {}
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []

def get_first_user_message(messages):
    """Get the first user message from a thread"""
    for msg in messages:
        if msg['role'] == 'user':
            return msg['content']
    return "New Chat"

def clean_messages(messages):
    """Remove duplicates while maintaining order"""
    seen = set()
    cleaned = []
    for msg in messages:
        msg_key = (msg['role'], msg['content'])
        if msg_key not in seen:
            seen.add(msg_key)
            cleaned.append(msg)
    return cleaned

def display_sidebar():
    st.sidebar.title("Chat History")
    
    # New Chat button
    if st.sidebar.button("+ New Chat", use_container_width=True):
        st.session_state.current_thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    # Display chat threads
    for thread_id, messages in st.session_state.chat_threads.items():
        first_msg = get_first_user_message(messages)
        preview = first_msg[:50] + "..." if len(first_msg) > 50 else first_msg
        
        button_key = f"thread_{thread_id}"
        is_selected = st.session_state.current_thread_id == thread_id
        button_style = "selected-thread" if is_selected else "chat-thread"
        
        if st.sidebar.button(preview, key=button_key, use_container_width=True):
            st.session_state.current_thread_id = thread_id
            st.session_state.messages = clean_messages(messages)
            st.rerun()

def main():
    initialize_session_state()
    
    # Ensure current_thread_id is set
    if not st.session_state.current_thread_id:
        st.session_state.current_thread_id = str(uuid.uuid4())
    
    # Load chat history if not already loaded
    if not st.session_state.chat_threads:
        st.session_state.chat_threads = st.session_state.chat_handler.get_chat_history()
    
    # Display sidebar with chat history
    display_sidebar()
    
    # Main chat area
    st.title("Mental Health Chat")
    
    # Display current chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("Type your message here..."):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Add message to current thread
        new_user_message = {"role": "user", "content": prompt}
        st.session_state.messages.append(new_user_message)

        # Get and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = requests.post(
                        API_URL,
                        json={"question": prompt},
                        headers={'Content-Type': 'application/json'},
                        timeout=30
                    )
                    response.raise_for_status()
                    response_data = response.json()
                    
                    if 'text' in response_data:
                        st.markdown(response_data['text'])
                        new_assistant_message = {
                            "role": "assistant",
                            "content": response_data['text']
                        }
                        st.session_state.messages.append(new_assistant_message)
                        
                        # Update the chat threads with the new messages
                        current_thread = st.session_state.current_thread_id
                        if current_thread not in st.session_state.chat_threads:
                            st.session_state.chat_threads[current_thread] = []
                        st.session_state.chat_threads[current_thread] = st.session_state.messages.copy()
                        
                    else:
                        st.error("I apologize, but I received an unexpected response. Please try again.")
                except Exception as e:
                    st.error(f"I apologize, but an error occurred. Please try again or contact support. Error: {str(e)}")

if __name__ == "__main__":
    main()