import streamlit as st
from config.supabase_config import supabase_config
from streamlit_cookies_manager import CookieManager
import config.supabase_crud as sc
import config.model_ia as model
import uuid

cookies = CookieManager()
if not cookies.ready():
    st.stop()

session = cookies.get("session")
if not session: 
    st.switch_page("main.py")

supabase = supabase_config()

st.subheader("BotLit")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_id" not in st.session_state:
    st.session_state.chat_id = ""

if "new_chat" not in st.session_state:
    st.session_state.new_chat = False

def cleanChat():
    st.session_state.new_chat = False

def cleanMessages():
    st.session_state.messages = []

def loadChat(chat, chat_id):
    st.session_state.new_chat = True
    st.session_state.messages = chat
    st.session_state.chat_id = chat_id


with st.sidebar:
    
    if st.button("Logout", icon=":material/exit_to_app:", type="tertiary"):
        supabase.auth.sign_out()
        cookies.clear()
        cookies.save()
        cleanChat()
        cleanMessages()
        st.switch_page("main.py")
    
    user = sc.getUser(session)
    st.subheader(f":blue-background[Welcome: {user}]")
    st.title("My Chats")
    if st.button("New Chat", icon=":material/add:", use_container_width=True):
        st.session_state.chat_id = str(uuid.uuid4())
        sc.save(st.session_state.chat_id, session, "new chat","")
        st.session_state.new_chat = True
        cleanMessages()
    
    datos = sc.getChats(session)
    if datos:
        for item in datos:
            c1,c2 = st.columns([10,2])
            c1.button(item["name"], 
                    type="tertiary", 
                    key=f"id_{item['chat_id']}", 
                    on_click=loadChat, 
                    args=(item["chat"],item["chat_id"]))
            c2.button(" ",
                    icon=":material/delete:",
                    type="tertiary",
                    key=f"delete_{item['chat_id']}",
                    on_click= sc.delete,
                    args=(item["chat_id"],)
                    )
    else:
        st.caption("Empty Chats")

# Chat
if st.session_state.new_chat:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Write your message: "):
        st.session_state.messages.append({"role":"user", "content":prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Wait answer..."):
            response = model.generate_response(st.session_state.messages)
        
        st.session_state.messages.append({"role":"ai", "content":response})

        with st.chat_message("ai"):
            st.markdown(response)
        
        sc.edit(st.session_state.chat_id, st.session_state.messages)
        if sc.getNameChat(st.session_state.chat_id) == "new chat":
            sc.editName(st.session_state.chat_id, prompt)
        
else:
    st.success("Select or create a chat")
