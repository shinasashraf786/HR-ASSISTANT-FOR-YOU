# Copyright 2025
# INNOVA Data Integration – Streamlit Chat Application

import os
import time
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st

# -------------------------------------------------
# Authentication Layer
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
            st.rerun()
        else:
            st.error("Invalid credentials")


if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.title("Login Required")
    authenticate()
    st.stop()


# -------------------------------------------------
# Environment Setup
# -------------------------------------------------

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ASSISTANT_ID = "asst_TnjbiLVFgUlcy9ZTmO1ruCCI"

st.set_page_config(page_title="INNOVA DATA INTEGRATION AND EMAIL CATEGORISATION", 
                   page_icon="♾️",
                   layout="wide")


# -------------------------------------------------
# Initialise conversation states
# -------------------------------------------------

if "conversations" not in st.session_state:
    st.session_state["conversations"] = {}

if "active_convo" not in st.session_state:
    st.session_state["active_convo"] = None

if "threads" not in st.session_state:
    st.session_state["threads"] = {}    # each conversation gets a unique OpenAI thread


# -------------------------------------------------
# Sidebar (ChatGPT-style)
# -------------------------------------------------

with st.sidebar:
    st.header("Chats")

    # New Chat Button
    if st.button("New Chat"):
        convo_id = str(time.time())

        # New conversation entry
        st.session_state["conversations"][convo_id] = {
            "title": "New Conversation",
            "messages": []
        }

        # Create a new OpenAI thread for this conversation
        new_thread = client.beta.threads.create()
        st.session_state["threads"][convo_id] = new_thread.id

        # Activate it
        st.session_state["active_convo"] = convo_id
        st.rerun()

    # List existing conversations
    for convo_id, convo in st.session_state["conversations"].items():
        if st.button(convo["title"], key=convo_id):
            st.session_state["active_convo"] = convo_id
            st.rerun()


# -------------------------------------------------
# No chat selected yet
# -------------------------------------------------

if st.session_state["active_convo"] is None:
    st.title("INNOVA DATA INTEGRATION AND EMAIL CATEGORISATION ♾️")
    st.caption("Start a new chat using the button on the left.")
    st.stop()


# -------------------------------------------------
# Load active conversation
# -------------------------------------------------

convo_id = st.session_state["active_convo"]
conversation = st.session_state["conversations"][convo_id]
thread_id = st.session_state["threads"][convo_id]


# -------------------------------------------------
# Page Header
# -------------------------------------------------

st.title("INNOVA DATA INTEGRATION AND EMAIL CATEGORISATION ♾️")
st.caption("Handle INNOVA data and email categories in one place, without the clutter")


# -------------------------------------------------
# Display chat history
# -------------------------------------------------

for msg in conversation["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# -------------------------------------------------
# Chat Input + OpenAI Assistant Response
# -------------------------------------------------

if prompt := st.chat_input("Ask anything"):

    # Save user message
    conversation["messages"].append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Update conversation title (first prompt)
    if conversation["title"] == "New Conversation":
        conversation["title"] = prompt[:30]

    # Send user prompt to OpenAI thread
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=prompt
    )

    # Process assistant response
    with st.chat_message("assistant"):
        with st.spinner("Innova AI is thinking…"):
            try:
                # Start a run
                run = client.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=ASSISTANT_ID
                )

                # Poll until done
                while True:
                    status = client.beta.threads.runs.retrieve(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                    if status.status == "completed":
                        break
                    time.sleep(1)

                # Fetch latest reply
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                reply = messages.data[0].content[0].text.value

                st.markdown(reply)

                # Save assistant reply
                conversation["messages"].append({"role": "assistant", "content": reply})

            except Exception as e:
                st.error(f"An error occurred: {e}")
