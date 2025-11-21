# Copyright 2025
# HR Shortlister Streamlit Chat Application

import os
import time
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st

# -------------------------------------------------
# Simple Authentication Layer
# -------------------------------------------------

def authenticate():
    st.session_state["authenticated"] = False

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    correct_username = os.getenv("APP_USERNAME")
    correct_password = os.getenv("APP_PASSWORD")

    if st.button("Login"):
        if username == correct_username and password == correct_password:
            st.session_state["authenticated"] = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")


if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.title("Login Required")
    authenticate()
    st.stop()


# -------------------------------------------------
# Environment Setup
# -------------------------------------------------

# Load environment variables from .env
load_dotenv()

# Configure OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Your Assistant ID
ASSISTANT_ID = "asst_TnjbiLVFgUlcy9ZTmO1ruCCI"

# Streamlit Page Config
st.set_page_config(page_title="INNOVA DATA INTEGRATION AND EMAIL CATEGORISATION", page_icon="♾️")

# -------------------------------------------------
# App Header
# -------------------------------------------------

st.title("INNOVA DATA INTEGRATION AND EMAIL CATEGORISATION♾️")
st.caption("Handle INNOVA data and email categories in one place, without the clutter")


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

if prompt := st.chat_input("Ask anything"):
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
        with st.spinner("Innova AI is thinking…"):
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

