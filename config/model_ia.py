import streamlit as st
import google.generativeai as genai

from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(api_key=os.getenv('GEMINI_KEY'))
model = genai.GenerativeModel("gemini-2.0-flash")

# def generate_response(prompt):
#    try:
#        response = model.generate_content(prompt)
#        return response.text
#    except Exception as e:
#        return f"Error con la respuesta: {e}"

def generate_response(message):
    try:
        messages = "\n".join([f"{msg['role']} : {msg['content']}" for msg in message])
        response = model.generate_content(messages)
        return response.text
    except Exception as e:
        return f"Error con la respuesta: {e}"

def generate_name(prompt):
    try:
        response = model.generate_content(f"Genera un solo titulo corto de 20 caracteres en base a este texto sin mostrar la cantidad de caracteres: {prompt} ")
        return response.text
    except Exception as e:
        return f"Error con la respuesta: {e}"