# INNOVA Chat App with Full Folder Support, PDF Export, and Persistent Storage

import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# -------------------------------------------------
# File Paths
# -------------------------------------------------
STORAGE_FILE = "conversations.json"
EXPORTS_DIR = "exports"
os.makedirs(EXPORTS_DIR, exist_ok=True)

# -------------------------------------------------
# Helper Functions
# -------------------------------------------------
def load_conversations():
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_conversations(data):
    with open(STORAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def export_chat_to_pdf(convo_id, convo):
    filename = os.path.join(EXPORTS_DIR, f"Chat - {convo['title']}.pdf")
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    content = [Paragraph(f"<b>Conversation Title:</b> {convo['title']}", styles['Title']), Spacer(1, 12)]
    for msg in convo["messages"]:
        role = "User" if msg["role"] == "user" else "Assistant"
        content.append(Paragraph(f"<b>{role}:</b> {msg['content']}", styles['BodyText']))
        content.append(Spacer(1, 12))
    doc.build(content)
    return filename

def export_folder_to_pdf(folder_name, conversations):
    filename = os.path.join(EXPORTS_DIR, f"Folder - {folder_name}.pdf")
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    content = [Paragraph(f"<b>Folder:</b> {folder_name}", styles['Title']), Spacer(1, 12)]
    for convo_id, convo in conversations.items():
        if convo.get("folder") == folder_name:
            content.append(Paragraph(f"<b>Conversation:</b> {convo['title']}", styles['Heading2']))
            content.append(Spacer(1, 6))
            for msg in convo["messages"]:
                role = "User" if msg["role"] == "user" else "Assistant"
                content.append(Paragraph(f"<b>{role}:</b> {msg['content']}", styles['BodyText']))
                content.append(Spacer(1, 6))
            content.append(Spacer(1, 12))
    doc.build(content)
    return filename

# -------------------------------------------------
# Authentication
# -------------------------------------------------
def authenticate():
    st.session_state["authenticated"] = False
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == os.getenv("APP_USERNAME") and password == os.getenv("APP_PASSWORD"):
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Invalid credentials")

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.title("Login Required")
    authenticate()
    st.stop()

# -------------------------------------------------
# Init
# -------------------------------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ASSISTANT_ID = "asst_TnjbiLVFgUlcy9ZTmO1ruCCI"

st.set_page_config("INNOVA CHAT", page_icon="\u267e", layout="wide")

if "conversations" not in st.session_state:
    st.session_state["conversations"] = load_conversations()
if "active_convo" not in st.session_state:
    st.session_state["active_convo"] = None
if "threads" not in st.session_state:
    st.session_state["threads"] = {}

# -------------------------------------------------
# Folder + Chat UI
# -------------------------------------------------
def get_folders():
    return sorted(set(c.get("folder", "Uncategorised") for c in st.session_state["conversations"].values()))

with st.sidebar:
    st.header("Folders")
    folders = get_folders()
    folder_search = st.text_input("Search folders")
    folders_to_show = [f for f in folders if folder_search.lower() in f.lower()]
    selected_folder = st.selectbox("Select folder", folders_to_show + ["+ New Folder"])

    if selected_folder == "+ New Folder":
        new_folder = st.text_input("Create new folder")
        if new_folder:
            selected_folder = new_folder

    st.markdown("---")
    st.header("Chats")
    chat_search = st.text_input("Search chats")
    if st.button("New Chat"):
        cid = str(time.time())
        st.session_state["conversations"][cid] = {"title": "New Conversation", "folder": selected_folder, "messages": []}
        thread = client.beta.threads.create()
        st.session_state["threads"][cid] = thread.id
        st.session_state["active_convo"] = cid
        save_conversations(st.session_state["conversations"])
        st.rerun()

    for cid, convo in st.session_state["conversations"].items():
        if convo.get("folder") == selected_folder and chat_search.lower() in convo["title"].lower():
            col1, col2, col3 = st.columns([6, 1, 1])
            if col1.button(convo["title"], key=cid):
                st.session_state["active_convo"] = cid
                st.rerun()
            if col2.button("\u274C", key=f"del_{cid}"):  # ❌
                st.session_state["conversations"].pop(cid)
                st.session_state["threads"].pop(cid, None)
                if st.session_state["active_convo"] == cid:
                    st.session_state["active_convo"] = None
                save_conversations(st.session_state["conversations"])
                st.rerun()
            if col3.download_button("\u2B07\uFE0F", data=open(export_chat_to_pdf(cid, convo), "rb"), file_name=f"{convo['title']}.pdf", mime="application/pdf", key=f"pdf_{cid}"):  # ⬇ = down arrow
                pass

    # Export folder as one PDF
    if selected_folder != "+ New Folder":
        if st.download_button("\U0001F4BE Export Folder PDF", data=open(export_folder_to_pdf(selected_folder, st.session_state["conversations"]), "rb"), file_name=f"{selected_folder}.pdf", mime="application/pdf"):
            pass
        # Delete folder (only if empty)
        if not any(c["folder"] == selected_folder for c in st.session_state["conversations"].values()):
            if st.button("\U0001F5D1 Delete Folder"):
                folders.remove(selected_folder)
                save_conversations(st.session_state["conversations"])
                st.rerun()

# -------------------------------------------------
# Main Chat Area
# -------------------------------------------------
if st.session_state["active_convo"] is None:
    st.title("INNOVA DATA INTEGRATION AND EMAIL CATEGORISATION♾️")
    st.caption("Handle INNOVA data and email categories in one place, without the clutter")
    st.stop()

cid = st.session_state["active_convo"]
convo = st.session_state["conversations"][cid]
if cid not in st.session_state["threads"]:
    st.session_state["threads"][cid] = client.beta.threads.create().id
thread_id = st.session_state["threads"][cid]

st.title(convo["title"])
st.caption(f"Folder: {convo.get('folder', 'Uncategorised')}")

with st.expander("\u2699 Chat Settings"):
    new_title = st.text_input("Rename chat", value=convo["title"])
    new_folder = st.text_input("Move to folder", value=convo.get("folder", "Uncategorised"))
    if st.button("Update"):
        convo["title"] = new_title.strip() or convo["title"]
        convo["folder"] = new_folder.strip() or convo["folder"]
        save_conversations(st.session_state["conversations"])
        st.rerun()

# Chat display
for msg in convo["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask something"):
    convo["messages"].append({"role": "user", "content": prompt})
    save_conversations(st.session_state["conversations"])
    with st.chat_message("user"):
        st.markdown(prompt)
    if convo["title"] == "New Conversation":
        convo["title"] = prompt[:30]
        save_conversations(st.session_state["conversations"])
    client.beta.threads.messages.create(thread_id=thread_id, role="user", content=prompt)
    with st.chat_message("assistant"):
        with st.spinner("Innova AI is thinking..."):
            run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=ASSISTANT_ID)
            while True:
                status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
                if status.status == "completed":
                    break
                time.sleep(1)
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            reply = messages.data[0].content[0].text.value
            st.markdown(reply)
            convo["messages"].append({"role": "assistant", "content": reply})
            save_conversations(st.session_state["conversations"])
