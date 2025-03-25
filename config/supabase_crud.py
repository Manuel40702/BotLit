from config.supabase_config import supabase_config
import json
import config.model_ia as model

supabase = supabase_config()

def getUser(user_id):
    response = supabase.table("users").select("user").eq("id",user_id).single().execute()
    return response.data["user"]

def save(chat_id, user_id, name, chat):
    data = {"chat_id":chat_id,"user_id":user_id,"name":name,"chat":chat}
    supabase.table("chats").insert(data).execute()

def edit(chat_id, chat):
    supabase.table("chats").update({
        "chat":chat
    }).eq("chat_id", chat_id).execute()

def getChats(user_id):
    datos = supabase.table("chats").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()

    for item in datos.data:
        if item.get("chat"):
            if isinstance(item["chat"], str):
                try:
                    item["chat"] = json.loads(item["chat"])
                except json.JSONDecodeError:
                    item["chat"] = []
        else:
            item["chat"] = []
    
    return datos.data

def delete(chat_id):
    supabase.table("chats").delete().eq("chat_id", chat_id).execute()

def editName(chat_id, prompt):
    name = model.generate_name(prompt)
    supabase.table("chats").update({
        "name":name
    }).eq("chat_id", chat_id).execute()

def getNameChat(chat_id):
    response = supabase.table("chats").select("name").eq("chat_id",chat_id).single().execute()
    return response.data["name"]