import streamlit as st
from smartsageHelper import llm_pipeline, ask_llm

# Custom CSS for styling
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Chat bubbles */
    .user-bubble {
        background-color: #ffdddd;
        padding: 10px;
        border-radius: 15px 15px 0 15px;
        margin: 5px 0;
        max-width: 80%;
        margin-left: auto;
    }
    
    .assistant-bubble {
        background-color: #ddffdd;
        padding: 10px;
        border-radius: 15px 15px 15px 0;
        margin: 5px 0;
        max-width: 80%;
        margin-right: auto;
    }
    
    /* Input area */
    .stTextInput>div>div>input {
        background-color: #2d3746;
        color: white;
    }
    
    /* Sidebar */
    .st-emotion-cache-6qob1r {
        background-color: #1a1d24;
    }
</style>
""", unsafe_allow_html=True)

# App title
st.title("🧠 SmartSage - Conversational AI for Your Sources")
st.write("Welcome to **SmartSage**! Upload documents or enter a URL to ask AI-powered questions.")

# Session State Initialization
if "vector_index" not in st.session_state:
    st.session_state.vector_index = None
if "doc_loaded" not in st.session_state:
    st.session_state.doc_loaded = False
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "processing" not in st.session_state:
    st.session_state.processing = False
if "update_clicked" not in st.session_state:
    st.session_state.update_clicked = False

# Sidebar Configuration
with st.sidebar:
    st.title("⚙️ Settings")
    
    # File Uploader
    uploaded_files = st.file_uploader(
        "📂 Upload Documents (PDF/DOCX/TXT)",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True
    )
    
    # URL Input
    st.markdown("---")
    url = st.text_input("🌐 Or enter document URL:")
    
    # API Key
    st.markdown("---")
    api_key = st.text_input("🔐 Gemini API Key", type="password")
    
    # Process Button
    st.markdown("---")
    if st.button("🚀 Process Documents", use_container_width=True):
        if not api_key:
            st.error("API key is required")
        elif not uploaded_files and not url:
            st.warning("Please upload files or enter URL")
        else:
            try:
                with st.spinner("Processing documents..."):
                    vector_index = llm_pipeline(uploaded_files, url, api_key)
                    st.session_state.vector_index = vector_index
                    st.session_state.doc_loaded = True
                    st.success("Documents processed successfully!")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Chat Interface
st.markdown("---")
st.subheader("💬 Chat")

# Display conversation history
chat_container = st.container()
with chat_container:
    for message in st.session_state.conversation:
        if message["role"] == "user":
            st.markdown(
                f'<div class="user-bubble">👤 <strong>You:</strong> {message["text"]}</div>',
                unsafe_allow_html=True
            )
        elif message["role"] == "assistant":
            st.markdown(
                f'<div class="assistant-bubble">🤖 <strong>SmartSage:</strong> {message["text"]}</div>',
                unsafe_allow_html=True
            )
    
    if st.session_state.processing:
        st.markdown(
            '<div class="assistant-bubble">🤖 <strong>SmartSage:</strong> Processing...</div>',
            unsafe_allow_html=True
        )

# Input area at the bottom
col1, col2 = st.columns([6, 1])
with col1:
    user_input = st.text_input(
        "Type your question...", 
        key="user_input",  # Using the session state key
        label_visibility="collapsed",
        value=st.session_state.user_input if 'user_input' in st.session_state else ""  # Bind the input value to session state
    )
with col2:
    send_button = st.button("➤", use_container_width=True)

# Function to handle button click or text input change
def handle_input_change():
    st.session_state.update_clicked = True

# Call the function when user_input or button is pressed
if send_button or (user_input and st.session_state.update_clicked):
    st.session_state.update_clicked = False
    if user_input.strip():
        if not api_key:
            st.warning("Please enter your API key")
        elif (uploaded_files or url) and not st.session_state.doc_loaded:
            st.warning("Please process documents first")
        else:
            # Add user message
            st.session_state.conversation.append({"role": "user", "text": user_input})
            st.session_state.processing = True
            # Reset the input field value (handled automatically by the widget)
            st.session_state.user_input = ""  # Input cleared automatically after pressing send
            st.rerun()  # Rerun to simulate clearing the input and updating chat

# Generate response after rerun
if st.session_state.processing and st.session_state.conversation[-1]["role"] == "user":
    query = st.session_state.conversation[-1]["text"]
    try:
        with st.spinner(""):
            answer = ask_llm(query, st.session_state.vector_index, api_key)
            st.session_state.conversation.append({"role": "assistant", "text": answer})
    except Exception as e:
        st.session_state.conversation.append({"role": "assistant", "text": f"Error: {str(e)}"})
    finally:
        st.session_state.processing = False
        st.rerun()  # Rerun after getting response to update UI
