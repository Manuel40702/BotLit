import streamlit as st
import re
from config.supabase_config import supabase_config

st.set_page_config("BotLit", layout="wide")

def validar_email(email):
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.match(patron, email)

st.markdown("<center><h1>BotLit: Supabase and Gemini AI</h1></center>", unsafe_allow_html=True)

_, col, _ = st.columns([3,3,3])

with col:
    with st.form("register", clear_on_submit=True):
        supabase = supabase_config()

        st.subheader("Create Account")
        user = st.text_input("User", placeholder="User", autocomplete="off")
        email = st.text_input("Email", placeholder="Email", autocomplete="off")
        password = st.text_input("Password", placeholder="Password", autocomplete="off", type="password")
        submit = st.form_submit_button("Register")

        if submit:
            if validar_email(email):
                try:
                    response = supabase.auth.sign_up({"email": email, "password": password})
                    if(response.user.id):
                        data = {"user": user, "email": response.user.email}
                        supabase.table("users").insert(data).execute()
                        st.switch_page("main.py")
                    else:
                        st.write(response)
                except Exception as e:
                    st.error(f"Error:  {str(e)}")
            else:
                st.warning("Write a valid email")