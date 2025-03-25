import streamlit as st
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

def supabase_config():
    #SUPABASE_URL = st.secrets["supabase"]["SUPABASE_URL"]
    #SUPABASE_KEY = st.secrets["supabase"]["SUPABASE_KEY"]
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    return create_client(SUPABASE_URL, SUPABASE_KEY)