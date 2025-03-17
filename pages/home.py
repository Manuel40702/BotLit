import streamlit as st
from config.supabase_config import supabase_config
from streamlit_cookies_manager import CookieManager
import config.supabase_crud as sc

cookies = CookieManager()
if not cookies.ready():
    st.stop()

session = cookies.get("session")
if not session: 
    st.switch_page("main.py")

supabase = supabase_config()

st.subheader("BotLit")

with st.sidebar:
    
    if st.button("Logout", icon=":material/exit_to_app:", type="tertiary"):
        supabase.auth.sign_out()
        cookies.clear()
        cookies.save()
        st.switch_page("main.py")
    
    user = sc.getUser(session)
    st.subheader(f":blue-background[Welcome: {user}]")