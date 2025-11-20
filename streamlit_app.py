# Copyright 2025
# HR Shortlister Streamlit Chat Application

import os
import time
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st

# -------------------------------------------------
# Environment Setup
# -------------------------------------------------

# Load environment variables from .env
load_dotenv()

# Configure OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Your Assistant ID
ASSISTANT_ID = "asst_bBLvW1TIJ2lBYTjCYlfftrhu"

# Streamlit Page Config
st.set_page_config(page_title="HR Shortlister", page_icon="🤖")

# -------------------------------------------------
# App Header
# -------------------------------------------------

st.title("HR Shortlister 🤖")
st.caption("Chat with your AI assistant to evaluate and shortlist candidates efficiently.")

st.markdown("""
This assistant connects to **OpenAI’s HR Shortlister** to help you:
- Review and compare candidate profiles.
- Generate shortlist recommendations.
- Draft evaluation feedback and hiring insights.
""")

# -------------------------------------------------
# Chat Interface Setup
# -------------------------------------------------

if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display prior messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------------------------------------------------
# User Input
# -------------------------------------------------

if prompt := st.chat_input("Ask HR Shortlister anything..."):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to thread
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt
    )

    # Run the assistant
    with st.chat_message("assistant"):
        with st.spinner("HR Shortlister is thinking..."):
            try:
                run = client.beta.threads.runs.create(
                    thread_id=st.session_state.thread_id,
                    assistant_id=ASSISTANT_ID
                )

                # Poll until run completes
                while True:
                    status = client.beta.threads.runs.retrieve(
                        thread_id=st.session_state.thread_id,
                        run_id=run.id
                    )
                    if status.status == "completed":
                        break
                    time.sleep(1)

                # Get assistant reply
                messages = client.beta.threads.messages.list(
                    thread_id=st.session_state.thread_id
                )
                reply = messages.data[0].content[0].text.value

                st.markdown(reply)

                # Store assistant response
                st.session_state.messages.append({"role": "assistant", "content": reply})

            except Exception as e:
                st.error(f"An error occurred: {e}")

# -------------------------------------------------
# Sidebar
# -------------------------------------------------

st.sidebar.header("About HR Shortlister")
st.sidebar.write("""
**HR Shortlister** uses OpenAI’s API to support HR teams by:
- Analysing resumes and candidate experience.
- Providing shortlist recommendations.
- Suggesting structured evaluation feedback.
""")

st.sidebar.divider()

st.sidebar.header("Tips for Better Results")
st.sidebar.write("""
- Be clear about the role and context.
- Provide short candidate summaries if possible.
- Ask measurable, outcome-based questions.
""")

st.sidebar.divider()
st.sidebar.caption("Built with ❤️ using Streamlit and OpenAI.")
