import streamlit as st
import re
from config.supabase_config import supabase_config
from streamlit_cookies_manager import CookieManager

st.set_page_config("BotLit", layout="wide")

cookies = CookieManager()
if not cookies.ready():
    st.stop()

session = cookies.get("session")
if session: 
    st.switch_page("pages/home.py")

def validar_email(email):
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.match(patron, email)

st.markdown("<center><h1>BotLit: Supabase and Gemini AI</h1></center>", unsafe_allow_html=True)

_, col, _ = st.columns([3,3,3])

with col:
    with st.container(border=True):
        supabase = supabase_config()

        st.subheader("Sign In")
        email = st.text_input("Email", placeholder="Email", autocomplete="off")
        password = st.text_input("Password", placeholder="Password", autocomplete="off", type="password")
        bt1, bt2 = st.columns([4,1])
        submit = bt1.button("Login", icon =":material/send:")

        if submit:
            if validar_email(email):
                try:
                    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if(response.user.id):
                        cookies["session"] = response.user.id
                        cookies.save()
                        st.switch_page("pages/home.py")
                    else:
                        st.write(response)
                except Exception as e:
                    st.error(f"Error:  {str(e)}")
            else:
                st.warning("Write a valid email")
        
        if bt2.button("Create Account", type="tertiary"):
            st.switch_page("pages/register.py")